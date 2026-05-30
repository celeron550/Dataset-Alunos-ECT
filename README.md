# Dataset-Alunos-ECT

Repositório dedicado ao tratamento, documentação e estudo de dados acadêmicos dos discentes do curso de Bacharelado em Ciência e Tecnologia (BCT) da UFRN.

## Conteúdo do repositório

- `matriculas_com_detalhes_componentes_dados_socio_economicos_complementares_discentes_bct_cleaned.csv`
  - Base de entrada principal. Contém histórico de matrículas, informações socioeconômicas e resultados acadêmicos anonimizados.
- `mapeamento_niveis_equivalencias.csv`
  - Mapeamento de disciplinas obrigatórias e seus códigos históricos equivalentes.
- `base_discentes_semestre_ml.csv`
  - Base intermediária para aprendizado de máquina com registros por aluno e semestre cronológico.
- `base_vetorizada_final_corrigida.csv`
  - Versão vetorizada ou finalizada da base de dados para uso em modelos e análises.
- `DOCUMENTACAO_BASES.md`
  - Documentação detalhada do pipeline de preparação, tratamentos aplicados e estrutura dos dados.


## Objetivo

Este repositório tem como objetivo fornecer uma base tratada para estudo de desempenho acadêmico e tarefas de machine learning no contexto do curso de Ciência e Tecnologia da UFRN.

As bases foram preparadas para suportar análises de: 

- predição de situação no curso (conclusão, evasão, cancelamento)
- avaliação de trajetória por semestre
- modelos sequenciais e de séries temporais
- estudos de impacto socioeconômico sobre desempenho acadêmico

## Como usar

1. Abra o arquivo `DOCUMENTACAO_BASES.md` para entender o pipeline de preparação e o significado de cada coluna.
2. Carregue as bases em sua ferramenta preferida, por exemplo, pandas em Python:

```python
import pandas as pd

df = pd.read_csv("base_discentes_semestre_ml.csv")
print(df.head())
```

3. Para identificar equivalências entre disciplinas, utilize `mapeamento_niveis_equivalencias.csv`.
4. Use `base_discentes_semestre_ml.csv` como ponto de partida para treino de modelos ou exploração de dados.

## Estrutura geral

- Dados de entrada:
  - `matriculas_com_detalhes_componentes_dados_socio_economicos_complementares_discentes_bct_cleaned.csv`
  - `mapeamento_niveis_equivalencias.csv`
- Dados processados:
  - `base_discentes_semestre_ml.csv`
  - `base_vetorizada_final_corrigida.csv`

## Observações

- Os IDs dos discentes estão anonimizados.
- A documentação em `DOCUMENTACAO_BASES.md` explica o cálculo do semestre cronológico, o tratamento de equivalências e as métricas acumuladas.

