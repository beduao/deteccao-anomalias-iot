"""
Descobre qual versao do ToN-IoT Windows o artigo de Inuwa & Das usou.

O artigo nao diz se usou os arquivos "Processed" ou "Train_Test". Mas a
Tabela 5 informa quantos registros ha de cada classe (linha "Sum" lida na
coluna de totais). Este script compara a PROPORCAO de classes de cada arquivo
com a da tabela. A versao com a menor diferenca e a candidata.

Tambem mostra o numero de colunas, para comparar com o que o artigo informa
(Windows 7: 133 propriedades; Windows 10: 125).

Uso (da pasta iot):
    python src/identify_toniot.py data/raw/toniot_win_processed/*.csv
    python src/identify_toniot.py data/raw/toniot_win_traintest/*.csv
"""

from __future__ import annotations

import glob
import sys

import pandas as pd

# Tabela 5 de Inuwa & Das (2024): total de registros por classe no ToN-IoT.
PAPER_TABLE5 = {
    "ddos": 15670, "dos": 1790, "injection": 2080, "mitm": 50,
    "normal": 34000, "password": 12340, "scanning": 1520, "xss": 4310,
}
TYPE_CANDIDATES = ["type", "category", "attack_cat"]


def find_type_col(df: pd.DataFrame):
    lower = {c.lower().strip(): c for c in df.columns}
    for cand in TYPE_CANDIDATES:
        if cand in lower:
            return lower[cand]
    return None


def analyse(path: str) -> None:
    df = pd.read_csv(path, low_memory=False)
    print("=" * 70)
    print(f"Arquivo : {path}")
    print(f"Linhas  : {len(df):,}")
    print(f"Colunas : {len(df.columns)}   (artigo: Windows 7 = 133, Windows 10 = 125)")

    col = find_type_col(df)
    if col is None:
        print("Nao achei coluna de tipo de ataque. Colunas disponiveis:")
        print("   ", sorted(df.columns.tolist()))
        return

    counts = df[col].astype(str).str.lower().str.strip().value_counts()
    total_file = counts.sum()
    total_paper = sum(PAPER_TABLE5.values())

    print(f"\n{'classe':<12}{'arquivo':>10}{'% arquivo':>12}{'% artigo':>11}{'diferenca':>11}")
    max_diff = 0.0
    for cls in sorted(set(counts.index) | set(PAPER_TABLE5)):
        n = int(counts.get(cls, 0))
        p_file = 100 * n / total_file
        p_paper = 100 * PAPER_TABLE5.get(cls, 0) / total_paper
        diff = p_file - p_paper
        max_diff = max(max_diff, abs(diff))
        print(f"{cls:<12}{n:>10,}{p_file:>11.2f}%{p_paper:>10.2f}%{diff:>+10.2f}")

    print(f"\nMaior diferenca de proporcao: {max_diff:.2f} pontos percentuais")
    print("Quanto mais perto de zero, mais provavel que seja a versao do artigo.")


def main() -> None:
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(sorted(glob.glob(arg)) or [arg])
    if not paths:
        print(__doc__)
        sys.exit(1)
    for p in paths:
        analyse(p)


if __name__ == "__main__":
    main()
