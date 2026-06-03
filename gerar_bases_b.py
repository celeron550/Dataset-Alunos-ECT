"""
GERADOR DE BASES PARA ML — OPÇÃO B
====================================
Gera duas bases a partir de base_discentes_semestre_ml.csv:

BASE 1 — base_flat_por_aluno.csv
  Uma linha por aluno. Features dos primeiros N semestres pivotadas.
  Inclui target numérico (semestres_para_concluir) e target binário (concluiu).
  Ideal para: regressão, classificação, clustering com sklearn.

BASE 2 — base_sequencial_por_semestre.csv
  Uma linha por (aluno × semestre) — mesma estrutura da base gerada antes,
  mas com colunas renomeadas de forma mais clara e coluna extra de flag.
  Ideal para: XGBoost com group, LSTM, análise de evasão por semestre.
"""

import pandas as pd
import numpy as np
import os

IN_PATH  = "./outputs/base_discentes_semestre_ml.csv"
OUT_DIR  = "./outputs"
os.makedirs(OUT_DIR, exist_ok=True)

print("Carregando base sequencial...")
df = pd.read_csv(IN_PATH, low_memory=False)
print(f"  {len(df):,} linhas | {df['id_discente'].nunique():,} discentes\n")

# ──────────────────────────────────────────────────────────────
# FEATURES FIXAS (não variam por semestre — características do aluno)
# ──────────────────────────────────────────────────────────────
FIXED_FEATURES = [
    "renda",
    "sexo_encoded",
    "ano_nascimento",
    "raca_encoded",
    "escola_ens_medio_encoded",
    "cotista_encoded",
    "possui_bolsa_pesquisa",
    "possui_auxilio_alimentacao",
    "possui_auxilio_transporte",
    "possui_auxilio_residencia_moradia",
    # ano_ingresso e periodo_ingresso vem do target_df (via groupby),
    # nao do fixed_df, para evitar colunas duplicadas no merge.
]

# Features que variam por semestre (performance acumulada + estado das disciplinas)
PERF_FEATURES = [
    "media_periodo",
    "faltas_no_periodo",
    "reprovacoes_no_periodo",
    "total_faltas_acumulado",
    "total_reprovacoes_acumulado",
]

# Notas e status acumulados das obrigatórias
DISC_FEATURES = [c for c in df.columns if c.endswith("_nota") or c.endswith("_status")]

SEQ_FEATURES = PERF_FEATURES + DISC_FEATURES


# ══════════════════════════════════════════════════════════════
# BASE 2 — SEQUENCIAL (refinamento da base atual)
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("GERANDO BASE 2 — Sequencial por semestre")
print("=" * 60)

# Adiciona coluna indicando se o aluno já concluiu (para uso como label em evasão)
df_seq = df.copy()

# Coluna auxiliar: semestre final de cada aluno (útil como contexto)
sem_max = df_seq.groupby("id_discente")["semestre_cronologico"].transform("max")
df_seq["semestre_final"] = sem_max

# Reorganiza colunas de forma didática:
# [identificação] → [fixas] → [target] → [performance do semestre] → [disciplinas]
cols_seq = (
    ["id_discente", "ano_ingresso", "periodo_ingresso", "semestre_cronologico"]
    + FIXED_FEATURES
    + ["status_curso_encoded"]
    + PERF_FEATURES
    + DISC_FEATURES
)
cols_seq = [c for c in cols_seq if c in df_seq.columns]
df_seq = df_seq[cols_seq].sort_values(
    ["id_discente", "semestre_cronologico"]
).reset_index(drop=True)

out_seq = os.path.join(OUT_DIR, "base_sequencial_por_semestre.csv")
df_seq.to_csv(out_seq, index=False)

print(f"  Linhas: {len(df_seq):,}")
print(f"  Discentes únicos: {df_seq['id_discente'].nunique():,}")
print(f"  Colunas: {len(df_seq.columns)}")
print(f"  Distribuição de status:")
print(f"    Concluído/Formado (+1): {(df_seq['status_curso_encoded']==1).sum():,}")
print(f"    Ativo              ( 0): {(df_seq['status_curso_encoded']==0).sum():,}")
print(f"    Cancelado          (-1): {(df_seq['status_curso_encoded']==-1).sum():,}")
print(f"  Arquivo: {out_seq}\n")


# ══════════════════════════════════════════════════════════════
# BASE 1 — FLAT (uma linha por aluno, pivot dos semestres)
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("GERANDO BASE 1 — Flat por aluno (pivot semestral)")
print("=" * 60)

# ── Parâmetros do pivot ──────────────────────────────────────
# Usamos apenas os primeiros N_PIVOT semestres como features,
# pois ao aplicar o modelo em alunos ativos só teremos esse histórico.
# A mediana de semestres para concluir é ~6, então 4 semestres
# já capturam ~50% do percurso e são acessíveis para todos os alunos.
N_PIVOT = 4

print(f"  Pivotando os {N_PIVOT} primeiros semestres de cada aluno...")

# ── Targets ─────────────────────────────────────────────────
# Para cada aluno: compute o número total de semestres cursados
target_df = (
    df.groupby("id_discente")
    .agg(
        status_curso_encoded=("status_curso_encoded", "first"),
        semestres_para_concluir=("semestre_cronologico", "max"),
        ano_ingresso=("ano_ingresso", "first"),
        periodo_ingresso=("periodo_ingresso", "first"),
    )
    .reset_index()
)

# Target binário: concluiu ou não (exclui ativos da análise supervisionada)
target_df["concluiu"] = target_df["status_curso_encoded"].map({1: 1, -1: 0, 0: np.nan})

# ── Features fixas (pega a primeira ocorrência por aluno) ────
fixed_df = (
    df[["id_discente"] + FIXED_FEATURES]
    .drop_duplicates(subset="id_discente", keep="first")
)

# ── Pivot das features sequenciais ──────────────────────────
# Filtra só os N_PIVOT primeiros semestres
df_pivot = df[df["semestre_cronologico"] <= N_PIVOT].copy()

# Features a pivotar: performance + notas acumuladas das disciplinas
# (omitimos _faltas por semestre para não explodir a largura; mantemos _nota e _status)
PIVOT_COLS = PERF_FEATURES + DISC_FEATURES

pivot_rows = []
for sem in range(1, N_PIVOT + 1):
    sub = df_pivot[df_pivot["semestre_cronologico"] == sem][
        ["id_discente"] + PIVOT_COLS
    ].copy()
    sub = sub.rename(columns={c: f"s{sem}_{c}" for c in PIVOT_COLS})
    pivot_rows.append(sub)

# Merge sequencial (outer para manter alunos que não chegaram ao semestre N)
from functools import reduce
pivot_merged = reduce(
    lambda a, b: a.merge(b, on="id_discente", how="outer"),
    pivot_rows
)

# ── Monta base final ─────────────────────────────────────────
base_flat = (
    target_df
    .merge(fixed_df,     on="id_discente", how="left")
    .merge(pivot_merged, on="id_discente", how="left")
)

# Remove coluna intermediária status_curso_encoded (redundante com 'concluiu')
# e mantém separados os targets
base_flat = base_flat.drop(columns=["status_curso_encoded"])

# Preenche NaN de disciplinas não cursadas com 0
disc_cols_flat = [c for c in base_flat.columns if any(
    c.endswith(suf) for suf in ("_nota", "_status", "_periodo", "_acumulado")
)]
base_flat[disc_cols_flat] = base_flat[disc_cols_flat].fillna(0)

# Ordena colunas: [id] → [targets] → [fixas] → [s1_...] → [s2_...] → ...
id_and_target = [
    "id_discente", "ano_ingresso", "periodo_ingresso",
    "concluiu", "semestres_para_concluir"
]
# Filtra apenas colunas de pivot (padrão s{n}_feature, onde n é um dígito)
s_cols = sorted([c for c in base_flat.columns
                 if len(c) > 2 and c[0] == "s" and c[1].isdigit() and c[2] == "_"])
final_cols = id_and_target + FIXED_FEATURES + s_cols
final_cols = [c for c in final_cols if c in base_flat.columns]
base_flat = base_flat[final_cols].reset_index(drop=True)

out_flat = os.path.join(OUT_DIR, "base_flat_por_aluno.csv")
base_flat.to_csv(out_flat, index=False)

# ── Estatísticas ─────────────────────────────────────────────
concluidos   = base_flat[base_flat["concluiu"] == 1]
cancelados   = base_flat[base_flat["concluiu"] == 0]
ativos       = base_flat[base_flat["concluiu"].isna()]

print(f"\n  Linhas (1 por aluno): {len(base_flat):,}")
print(f"  Colunas:              {len(base_flat.columns)}")
print(f"\n  Distribuição:")
print(f"    Concluídos  (concluiu=1):  {len(concluidos):,}  — uso: treino/teste do regressor e classificador")
print(f"    Cancelados  (concluiu=0):  {len(cancelados):,}  — uso: treino/teste do classificador")
print(f"    Ativos      (concluiu=NaN): {len(ativos):,}   — uso: inferência (sem label ainda)")
print(f"\n  Target numérico — semestres_para_concluir (concluídos):")
print(f"    Média:   {float(concluidos["semestres_para_concluir"].mean()):.1f} semestres")
print(f"    Mediana: {float(concluidos["semestres_para_concluir"].median()):.0f} semestres")
print(f"    Min/Max: {float(concluidos["semestres_para_concluir"].min()):.0f} / {float(concluidos["semestres_para_concluir"].max()):.0f}")
print(f"\n  Arquivo: {out_flat}")

print("\n" + "=" * 60)
print("RESUMO FINAL")
print("=" * 60)
print(f"""
  base_flat_por_aluno.csv
    → {len(base_flat):,} linhas × {len(base_flat.columns)} colunas
    → Target regressão:      semestres_para_concluir
    → Target classificação:  concluiu  (1 / 0 / NaN para ativos)
    → Features temporais:    s1_... até s{N_PIVOT}_...
    → Treinar com:           concluiu não é NaN
    → Inferir em:            concluiu is NaN (ativos)

  base_sequencial_por_semestre.csv
    → {len(df_seq):,} linhas × {len(df_seq.columns)} colunas
    → Target:                status_curso_encoded
    → Ideal para:            XGBoost (group_by aluno), LSTM, análise de evasão
    → Cada linha representa: 1 aluno em 1 semestre específico
""")
