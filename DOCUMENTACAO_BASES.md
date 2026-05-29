# Documentação das Bases de Dados — BCT/UFRN
## Pipeline de Preparação para Aprendizado de Máquina

---

## Sumário

1. [Visão geral do pipeline](#1-visão-geral-do-pipeline)
2. [Arquivos de entrada](#2-arquivos-de-entrada)
3. [Tratamentos aplicados](#3-tratamentos-aplicados)
4. [Arquivos gerados](#4-arquivos-gerados)
   - [base_discentes_semestre_ml.csv](#41-base_discentes_semestre_mlcsv)
   - [base_sequencial_por_semestre.csv](#42-base_sequencial_por_semestrecsv)
   - [base_flat_por_aluno.csv](#43-base_flat_por_alunocsv)
5. [Encodings aplicados](#5-encodings-aplicados)
6. [Lógica de equivalência de disciplinas](#6-lógica-de-equivalência-de-disciplinas)
7. [Guia de uso por tarefa de ML](#7-guia-de-uso-por-tarefa-de-ml)
8. [Decisões de design e limitações conhecidas](#8-decisões-de-design-e-limitações-conhecidas)

---

## 1. Visão geral do pipeline

O pipeline parte de um histórico bruto de matrículas do curso de Bacharelado em Ciência e Tecnologia (BCT/UFRN) e produz três bases progressivamente mais elaboradas, cada uma adequada a um conjunto diferente de tarefas de ML.

```
matriculas_...bct_cleaned.csv          mapeamento_niveis_equivalencias.csv
         │                                          │
         └──────────────────┬───────────────────────┘
                            ▼
              [gerar_base_ml.py]
              Filtragem, encoding, pivot por disciplina,
              cálculo de semestre cronológico, acumulação
                            │
                            ▼
            base_discentes_semestre_ml.csv        ← base intermediária
                            │
              [gerar_bases_b.py]
              Separação em duas visões para ML
                 ┌──────────┴──────────┐
                 ▼                     ▼
  base_sequencial_por_semestre.csv   base_flat_por_aluno.csv
  (1 linha = aluno × semestre)       (1 linha = 1 aluno)
```

---

## 2. Arquivos de entrada

### `matriculas_...bct_cleaned.csv`

Histórico de matrículas de 4.777 discentes do BCT. Cada linha representa uma matrícula em uma turma específica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_discente` | string (hash) | Identificador anonimizado do aluno |
| `id_turma` | int | Identificador da turma |
| `id_componente_curricular` | int | ID interno do componente |
| `codigo` | string | Código da disciplina (ex.: `ECT1113`) |
| `nome` | string | Nome da disciplina |
| `media_final` | float | Nota final obtida (0–10) |
| `numero_total_faltas` | int | Total de faltas naquela turma |
| `descricao` | string | Resultado da matrícula (ver encoding abaixo) |
| `ano_turma` / `periodo_turma` | int | Ano e período em que a turma foi ofertada |
| `ano_ingresso` / `periodo_ingresso` | int | Ano e período de ingresso do aluno no curso |
| `status` | string | Situação atual do aluno no curso |
| `renda` | float | Renda familiar declarada |
| `escola_ens_medio` | string | Tipo de escola no ensino médio |
| `sexo` | string | `M` ou `F` |
| `ano_nascimento` | float | Ano de nascimento |
| `raca` | string | Autodeclaração racial |
| `cotista` | bool | Se ingressou por cotas (`t`/`f`) |
| `possui_bolsa_pesquisa` | bool | Auxílio pesquisa |
| `possui_auxilio_alimentacao` | bool | Auxílio alimentação |
| `possui_auxilio_transporte` | bool | Auxílio transporte |
| `possui_auxilio_residencia_moradia` | bool | Auxílio moradia |

**Volume:** 182.132 linhas × 27 colunas.

---

### `mapeamento_niveis_equivalencias.csv`

Grade das 23 disciplinas obrigatórias do BCT, organizada em 4 níveis, com os códigos históricos equivalentes ao código canônico atual.

| Coluna | Descrição |
|--------|-----------|
| `Nível` | Nível curricular (1º a 4º) |
| `Código` | Código canônico atual (ex.: `ECT2103`) |
| `nome` | Nome da disciplina |
| `equivalencia` | Códigos históricos aceitos como equivalentes |

**Obrigatórias por nível:**

| Nível | Disciplinas |
|-------|-------------|
| 1º | ECT2101 Pré-Cálculo, ECT2102 Vetores e Geometria Analítica, ECT2103 Cálculo I, ECT2104 Química Geral, ECT2105 Práticas de Leitura e Escrita I, ECT2106 Ciência, Tecnologia e Sociedade |
| 2º | ECT2201 Cálculo II, ECT2202 Álgebra Linear, ECT2203 Lógica de Programação, ECT2204 Introdução à Física Clássica I, ECT2205 Práticas de Leitura e Escrita II, ECT2206 Gestão e Economia da CTI, ECT2207 Probabilidade e Estatística |
| 3º | ECT2301 Cálculo III, ECT2302 Metodologia Científica, ECT2303 Linguagem de Programação, ECT2304 Introdução à Física Clássica II, ECT2305 Prática de Leitura em Inglês, ECT2306 Meio Ambiente e Desenvolvimento Urbano, ECT2307 Física Experimental I |
| 4º | ECT2401 Computação Numérica, ECT2402 Introdução à Física Clássica III, ECT2403 Física Experimental II |

---

## 3. Tratamentos aplicados

### 3.1 Cálculo do semestre cronológico

O semestre cronológico representa quantos semestres o aluno cursou desde seu ingresso, independentemente de quando as disciplinas foram ofertadas:

```
semestre_cronologico = (ano_turma - ano_ingresso) × 2
                     + (periodo_turma - periodo_ingresso)
                     + 1
```

Registros com semestre cronológico < 1 ou > 20 foram removidos como ruído.

### 3.2 Resolução de equivalências

O histórico do BCT contém múltiplas versões de grade curricular. Uma disciplina cursada como `ECT1113` (código antigo) é equivalente a `ECT2103` (Cálculo I, código atual). O mapeamento cobre 75 códigos históricos distintos que se reduzem a 23 canônicos.

A lógica de equivalência segue as regras:

- `OU` separa grupos alternativos — basta um grupo ser satisfeito
- `E` une códigos dentro de um grupo — todos devem ter sido aprovados

Exemplo: `ECT2403` é cumprida por `(ECT1314 E ECT1315)` **ou** `(ECT1304 E ECT1305)` **ou** outras combinações.

### 3.3 Acumulação cumulativa de status

Para cada aluno, o estado de uma disciplina em qualquer semestre reflete o **melhor resultado obtido até aquele momento** (não apenas naquele semestre). Isso é feito via `cummax` por aluno. O efeito prático:

- Se um aluno reprovou em Cálculo I no semestre 2 e foi aprovado no semestre 4, a partir do semestre 4 o campo `ECT2103_status` passa a ser `1` e `ECT2103_nota` reflete a nota de aprovação.
- Isso torna a base adequada para predição prospectiva: o modelo lê o estado atual do aluno, não o histórico de tentativas.

### 3.4 Métricas por semestre

Para cada par (aluno, semestre), foram calculadas métricas sobre **todas as disciplinas cursadas** naquele semestre (não apenas as obrigatórias):

| Coluna | Cálculo |
|--------|---------|
| `media_periodo` | Média das notas finais do semestre |
| `faltas_no_periodo` | Soma de faltas no semestre |
| `reprovacoes_no_periodo` | Contagem de matrículas com status < 0 no semestre |
| `total_faltas_acumulado` | Soma acumulada de faltas até aquele semestre |
| `total_reprovacoes_acumulado` | Soma acumulada de reprovações até aquele semestre |

---

## 4. Arquivos gerados

### 4.1 `base_discentes_semestre_ml.csv`

**Base intermediária.** Gerada por `gerar_base_ml.py`. Serve de entrada para as duas bases finais e pode ser usada diretamente.

- **Linhas:** 26.299 (1 por aluno × semestre)
- **Colunas:** 89
- **Granularidade:** aluno + semestre cronológico

#### Estrutura de colunas

**Identificação (4 colunas)**

| Coluna | Descrição |
|--------|-----------|
| `id_discente` | Hash anonimizado do aluno |
| `ano_ingresso` | Ano de ingresso no curso |
| `periodo_ingresso` | Período de ingresso (1 ou 2) |
| `semestre_cronologico` | Semestre de referência (1–20) |

**Dados socioeconômicos (10 colunas)**

| Coluna | Tipo | Valores |
|--------|------|---------|
| `renda` | float | Renda familiar declarada; −1 = não informado |
| `sexo_encoded` | int | 1 = M, 0 = F |
| `ano_nascimento` | float | Ano de nascimento |
| `raca_encoded` | int | Label encoding de 0–N; −1 = não informado |
| `escola_ens_medio_encoded` | int | 2 = todo público, 1 = misto, 0 = todo particular, −1 = não informado |
| `cotista_encoded` | int | 1 = cotista, 0 = não cotista |
| `possui_bolsa_pesquisa` | int | 1 = sim, 0 = não |
| `possui_auxilio_alimentacao` | int | 1 = sim, 0 = não |
| `possui_auxilio_transporte` | int | 1 = sim, 0 = não |
| `possui_auxilio_residencia_moradia` | int | 1 = sim, 0 = não |

**Target (1 coluna)**

| Coluna | Tipo | Valores |
|--------|------|---------|
| `status_curso_encoded` | int | 1 = concluído/formado, 0 = ativo, −1 = cancelado |

**Métricas de desempenho (5 colunas)**

| Coluna | Descrição |
|--------|-----------|
| `media_periodo` | Média das notas no semestre atual |
| `faltas_no_periodo` | Total de faltas no semestre atual |
| `reprovacoes_no_periodo` | Reprovações no semestre atual |
| `total_faltas_acumulado` | Faltas acumuladas até este semestre |
| `total_reprovacoes_acumulado` | Reprovações acumuladas até este semestre |

**Disciplinas obrigatórias (69 colunas)**

Para cada uma das 23 disciplinas canônicas, três colunas:

| Padrão | Descrição | Valores |
|--------|-----------|---------|
| `ECTxxxx_nota` | Melhor nota acumulada | 0.0–10.0; 0.0 = não cursou |
| `ECTxxxx_status` | Melhor status acumulado | 1 = aprovado, −1 = reprovado, 0 = não cursou |
| `ECTxxxx_faltas` | Faltas naquele semestre nessa disciplina | int ≥ 0 |

---

### 4.2 `base_sequencial_por_semestre.csv`

**Base para modelos que leem sequências.** Gerada por `gerar_bases_b.py`. Versão refinada da base intermediária, com colunas duplicadas removidas e ordenação didática.

- **Linhas:** 26.299 (1 por aluno × semestre)
- **Colunas:** 66
- **Diferença em relação à base intermediária:** remove colunas `ECTxxxx_faltas` (reduz ruído para modelos de sequência), e a estrutura de colunas foi reordenada para facilitar leitura.

#### Quando usar

Tarefas onde a trajetória ao longo do tempo é relevante:

- Predição de evasão semestre a semestre (`status_curso_encoded` como target em cada timestep)
- Modelos sequenciais como LSTM, GRU, ou Transformer
- XGBoost com `group_id = id_discente` (cada aluno é uma sequência de exemplos ordenados)
- Análise de sobrevivência (survival analysis)

#### Como iterar corretamente

```python
import pandas as pd

df = pd.read_csv("base_sequencial_por_semestre.csv")

# Cada aluno é uma sequência — sempre ordenar antes de usar
df = df.sort_values(["id_discente", "semestre_cronologico"])

# Para LSTM: agrupar por aluno e empilhar semestres como timesteps
for aluno_id, grupo in df.groupby("id_discente"):
    sequencia = grupo.drop(columns=["id_discente"]).values
    # sequencia.shape = (n_semestres, n_features)
```

#### Distribuição do target

| `status_curso_encoded` | Significado | Linhas |
|------------------------|-------------|--------|
| 1 | Concluído / Formado | 13.560 (51,6%) |
| −1 | Cancelado | 11.940 (45,4%) |
| 0 | Ativo | 799 (3,0%) |

---

### 4.3 `base_flat_por_aluno.csv`

**Base para modelos clássicos.** Gerada por `gerar_bases_b.py`. Uma linha por aluno. O progresso semestral foi "deitado" como colunas `s1_`, `s2_`, `s3_`, `s4_`, representando os primeiros 4 semestres.

- **Linhas:** 4.777 (1 por aluno)
- **Colunas:** 219
- **Features temporais:** semestres 1 a 4 pivotados (204 colunas de features + 15 fixas)

#### Por que 4 semestres?

A mediana de semestres para concluir é 6. Ao usar apenas os 4 primeiros semestres como features, o modelo aprendido sobre alunos concluídos pode ser aplicado diretamente sobre alunos ativos que ainda cursam esses semestres — que é o cenário real de predição.

#### Targets

| Coluna | Tipo | Uso |
|--------|------|-----|
| `concluiu` | float (0.0 / 1.0 / NaN) | Classificação binária: 1 = concluiu, 0 = cancelou, NaN = ainda ativo (inferência) |
| `semestres_para_concluir` | float | Regressão: número total de semestres até encerrar o vínculo |

#### Estatísticas do target de regressão (concluídos)

| Estatística | Valor |
|-------------|-------|
| Média | 6,9 semestres |
| Mediana | 6 semestres |
| Desvio padrão | 3,0 semestres |
| Mínimo | 1 semestre |
| Máximo | 20 semestres |

#### Distribuição de alunos

| Grupo | N | Uso recomendado |
|-------|---|-----------------|
| Concluídos (`concluiu = 1`) | 2.261 | Treino e teste (regressão e classificação) |
| Cancelados (`concluiu = 0`) | 2.386 | Treino e teste (classificação) |
| Ativos (`concluiu = NaN`) | 130 | Somente inferência — sem label disponível |

#### Estrutura das features pivotadas

Para cada semestre `s` ∈ {1, 2, 3, 4} e cada feature `f`, existe uma coluna `s{s}_{f}`. As features incluídas no pivot são:

- `media_periodo` — média das notas no semestre
- `faltas_no_periodo` — total de faltas no semestre
- `reprovacoes_no_periodo` — reprovações no semestre
- `total_faltas_acumulado` — faltas acumuladas até o semestre
- `total_reprovacoes_acumulado` — reprovações acumuladas até o semestre
- `ECTxxxx_nota` e `ECTxxxx_status` para cada uma das 23 obrigatórias (estado acumulado)

Alunos que não atingiram o semestre `s` têm `0` nessas colunas (interpretado como "não cursou ainda").

#### Como usar para regressão (tempo de conclusão)

```python
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

df = pd.read_csv("base_flat_por_aluno.csv")

# Seleciona apenas alunos com label disponível
labeled = df[df["concluiu"].notna()].copy()

# Define features e target
FEATURE_COLS = [c for c in labeled.columns
                if c not in ["id_discente", "concluiu", "semestres_para_concluir"]]

X = labeled[FEATURE_COLS].fillna(0)
y = labeled["semestres_para_concluir"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

print("MAE:", mean_absolute_error(y_test, model.predict(X_test)))

# Inferência em alunos ativos
ativos = df[df["concluiu"].isna()].copy()
ativos["semestres_previstos"] = model.predict(ativos[FEATURE_COLS].fillna(0))
```

#### Como usar para classificação (risco de evasão)

```python
from sklearn.ensemble import GradientBoostingClassifier

labeled = df[df["concluiu"].notna()].copy()

X = labeled[FEATURE_COLS].fillna(0)
y = labeled["concluiu"].astype(int)

# Mesmo split e treino...
clf = GradientBoostingClassifier(random_state=42)
clf.fit(X_train, y_train)
```

---

## 5. Encodings aplicados

Todos os campos categóricos foram convertidos para valores numéricos inteiros ou floats. A tabela abaixo documenta cada mapeamento para garantir a interpretabilidade dos resultados de ML.

### Status da matrícula (`descricao` → `descricao_encoded`)

Usado internamente para construir `ECTxxxx_status` e as métricas de reprovação.

| Valor original | Encoded |
|----------------|---------|
| APROVADO, APROVADO POR NOTA | 1 |
| CUMPRIU, DISPENSADO | 1 |
| REPROVADO, REPROVADO POR MÉDIA | −1 |
| REPROVADO POR FALTAS | −1 |
| REPROVADO POR MÉDIA E POR FALTAS | −1 |
| REPROVADO POR NOTA, REPROVADO POR NOTA E FALTA | −1 |
| TRANCADO, DESISTENCIA, CANCELADO, EXCLUIDA | −1 |
| Não cursou / NaN | 0 |

### Status do curso (`status` → `status_curso_encoded`)

Target principal das bases sequencial e intermediária.

| Valor original | Encoded |
|----------------|---------|
| CONCLUÍDO, FORMADO | 1 |
| ATIVO, ATIVO - FORMANDO | 0 |
| CANCELADO | −1 |

### Sexo (`sexo` → `sexo_encoded`)

| Valor original | Encoded |
|----------------|---------|
| M | 1 |
| F | 0 |
| Não informado | −1 |

### Escola do ensino médio (`escola_ens_medio` → `escola_ens_medio_encoded`)

Encoding ordinal: maior valor = maior exposição ao ensino público.

| Valor original | Encoded |
|----------------|---------|
| Todo em escola pública | 2 |
| Parte pública, parte particular | 1 |
| Todo em escola particular | 0 |
| Não informado | −1 |

### Raça (`raca` → `raca_encoded`)

Label encoding simples (ordem alfabética). Para uso interpretativo, consulte a tabela original.

| Valor original | Exemplo de encoded |
|----------------|-------------------|
| Amarelo | 0 |
| Branco | 1 |
| Indígena | 2 |
| Negro | 3 |
| Pardo | 4 |
| Não declarado / NaN | −1 |

### Cotista (`cotista` → `cotista_encoded`)

| Valor original | Encoded |
|----------------|---------|
| `t` / `True` | 1 |
| `f` / `False` | 0 |
| NaN | −1 |

### Booleanos de auxílios

Convertidos de `True`/`False` para `1`/`0`. Valor `−1` indica não informado.

---

## 6. Lógica de equivalência de disciplinas

O BCT passou por reformas curriculares, gerando múltiplos códigos históricos para a mesma disciplina. Para cada registro histórico, um mapeamento `código_histórico → código_canônico` foi construído com base na coluna `equivalencia` do arquivo de mapeamento.


### Como o status canônico é determinado

Para cada aluno e cada semestre, o status de uma disciplina canônica é resolvido assim:

1. Busca-se no histórico do aluno todos os códigos (históricos ou canônicos) que fazem parte das equivalências daquela obrigatória.
2. Verifica-se se ao menos um grupo de equivalência foi inteiramente aprovado.
3. Se sim, `ECTxxxx_status = 1` e `ECTxxxx_nota` recebe a maior nota obtida em qualquer código do grupo satisfeito.

### Estatísticas de cobertura

- Disciplinas canônicas: **23**
- Códigos históricos mapeados (incluindo equivalências): **75**
- Matrículas em obrigatórias (após resolução): **113.981** de 182.132 totais

---

## 7. Guia de uso por tarefa de ML

| Tarefa | Base recomendada | Target | Observação |
|--------|-----------------|--------|------------|
| Classificação de evasão (binária) | `base_flat_por_aluno.csv` | `concluiu` | Filtre `concluiu.notna()` |
| Regressão — tempo de conclusão | `base_flat_por_aluno.csv` | `semestres_para_concluir` | Use apenas concluídos no treino |
| Classificação multiclasse do curso | `base_sequencial_por_semestre.csv` | `status_curso_encoded` | Agrupe por `id_discente` |
| Predição de evasão por semestre | `base_sequencial_por_semestre.csv` | `status_curso_encoded` | Cada linha = um momento |
| Clustering de perfis de alunos | `base_flat_por_aluno.csv` | — | Remova os targets antes de clusterizar |
| Modelos sequenciais (LSTM, GRU) | `base_sequencial_por_semestre.csv` | `status_curso_encoded` | Ordene por `semestre_cronologico` dentro do grupo |

### Separação treino / teste recomendada

Para evitar problemas de incompatibilidade de grades curriculares, separe por ano de ingresso em vez de aleatoriamente:

```python
# Alunos que ingressaram entre 2015 e 2024

test  = df[df["ano_ingresso"] >= 2015]
train = df[df["ano_ingresso"] < 2024]
```

---

## 8. Decisões de design e limitações conhecidas

**Semestres cumulativos, não instantâneos.** As colunas `ECTxxxx_nota` e `ECTxxxx_status` refletem o melhor estado histórico até aquele semestre. Isso é intencional para predição prospectiva, mas significa que o modelo não enxerga tentativas fracassadas anteriores — apenas o resultado corrente. Se o comportamento de retentativa for relevante, considere adicionar uma feature `ECTxxxx_n_tentativas`.

**Faltas por disciplina (`ECTxxxx_faltas`) somente na base intermediária.** Na base sequencial essas colunas foram omitidas para reduzir esparsidade. Elas estão disponíveis em `base_discentes_semestre_ml.csv` caso necessário.

**Pivot fixo em 4 semestres.** A escolha de 4 semestres no pivot da base flat é um ponto de partida: captura ~50% do percurso mediano e é compatível com o histórico disponível dos alunos ativos. O parâmetro `N_PIVOT` no script `gerar_bases_b.py` pode ser ajustado livremente.

**Alunos ativos sem label (`concluiu = NaN`).** São 130 alunos cujo desfecho ainda é desconhecido. Eles não devem integrar treino ou teste — apenas inferência. Em experimentos puramente didáticos, podem ser simplesmente descartados com `df.dropna(subset=["concluiu"])`.

**Encoding de raça é ordinal artificialmente.** O label encoding preserva os valores mas não captura distâncias semânticas entre grupos. Para modelos sensíveis a essa estrutura (regressão linear, KNN), considere substituir por one-hot encoding.

**Identificador anonimizado.** `id_discente` é um hash MD5 do ID original. Não é possível rastreá-lo de volta ao aluno real. O campo deve ser removido das features antes do treino:

```python
X = df.drop(columns=["id_discente", "concluiu", "semestres_para_concluir"])
```

---

*Documentação gerada automaticamente a partir dos scripts `gerar_base_ml.py` e `gerar_bases_b.py`.*
