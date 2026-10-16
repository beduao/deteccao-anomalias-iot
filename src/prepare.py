"""
Converte os CSVs brutos do ToN-IoT e do BoT-IoT para o esquema canonico.

Uso:
    python src/prepare.py --dataset toniot --input data/raw/toniot/ --output data/toniot.parquet
    python src/prepare.py --dataset botiot --input data/raw/botiot/ --output data/botiot.parquet

ATENCAO: os nomes das colunas variam entre as distribuicoes destas bases.
Rode primeiro com --inspect para ver as colunas reais do seu download e
ajuste os dicionarios COLMAP_* abaixo se necessario.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import (  # noqa: E402
    ALL_FEATURES, ATTACK_TYPE, LABEL,
    add_derived, map_proto, map_state,
)
from tableio import save_table  # noqa: E402

# --- ToN-IoT NETWORK (derivado do Zeek) ------------------------------------
# ATENCAO: Inuwa & Das (2024) NAO usaram esta versao. Eles usaram os arquivos
# ToN-IoT Windows 7 e Windows 10, que sao telemetria de SISTEMA OPERACIONAL
# (contadores de processo, memoria, registro), nao trafego de rede. Ver secao
# 4.3.1 do artigo. A versao Network entra aqui como SUA extensao: uma segunda
# base de rede, alinhavel com a captura ao vivo.
COLMAP_TONIOT_NET = {
    "duration": "duration",
    "src_bytes": "src_bytes",
    "dst_bytes": "dst_bytes",
    "src_pkts": "src_pkts",
    "dst_pkts": "dst_pkts",
    "proto": "proto",
    "state": "conn_state",
    LABEL: "label",
    ATTACK_TYPE: "type",
}

# --- BoT-IoT, versao "All features" do recorte de 5% (derivado do Argus) ---
# ATENCAO: use os arquivos da pasta  Dataset > 5% > All features.
# A versao "10 best features" (a que o artigo usou, e que vai para o
# replicate.py) NAO tem dur, sbytes, dbytes, spkts, dpkts nem state, entao nao
# serve para o esquema canonico nem para o Raspberry Pi.
COLMAP_BOTIOT = {
    "duration": "dur",
    "src_bytes": "sbytes",
    "dst_bytes": "dbytes",
    "src_pkts": "spkts",
    "dst_pkts": "dpkts",
    "proto": "proto",
    "state": "state",
    LABEL: "attack",
    ATTACK_TYPE: "category",
}

# --- CICIoT2023 (extrator proprio, tipo CICFlowMeter) ----------------------
# Base moderna (2023), NAO usada por Inuwa & Das. Entra como base de rede
# alternativa: treino adicional e, principalmente, teste cruzado (treina no
# BoT-IoT de 2019, testa aqui em ameacas de 2023).
#
# COMO PREENCHER: baixe a base, rode
#     python src/prepare.py --dataset ciciot2023 --input <pasta> --inspect
# e substitua cada "PREENCHER..." pelo nome REAL da coluna no seu download.
# Os nomes abaixo sao os tipicos da distribuicao de fluxos do CICIoT2023, mas
# variam entre versoes (fluxo vs. pacote, com ou sem espacos no nome). NAO
# confie neles sem conferir com --inspect. Nomes errados = base nao carrega.
#
# Diferencas em relacao as outras bases:
#  - Nao ha coluna de estado; ha CONTAGENS de flags (syn_count, fin_count...).
#    O estado sai de schema.state_from_flags, nao de map_state.
#  - Duracao costuma vir em "flow_duration" (as vezes em microssegundos!).
#  - Rotulo costuma ser texto na coluna "label" (BenignTraffic vs. ataques).
COLMAP_CICIOT2023 = {
    "duration": "flow_duration",   # PREENCHER/CONFERIR: cheque a unidade (s vs us)
    "src_bytes": "Tot sum",        # PREENCHER: bytes da origem, ou "Header_Length"+payload
    "dst_bytes": "Tot size",       # PREENCHER: bytes do destino
    "src_pkts": "Number",          # PREENCHER: contagem de pacotes (origem)
    "dst_pkts": "Rate",            # PREENCHER: contagem de pacotes (destino) - CONFERIR
    "proto": "Protocol Type",      # PREENCHER: protocolo (as vezes numerico IANA)
    # flags para inferir o estado (podem ser 0/1 ou contagens):
    "syn": "syn_flag_number",      # PREENCHER
    "synack": "ack_flag_number",   # PREENCHER (as vezes so ha ack, nao syn+ack)
    "fin": "fin_flag_number",      # PREENCHER
    "rst": "rst_flag_number",      # PREENCHER
    LABEL: "label",                # PREENCHER: coluna de rotulo textual
    ATTACK_TYPE: "label",          # no CICIoT2023 o proprio label ja e o tipo
}

CONFIG = {
    "toniot_net": (COLMAP_TONIOT_NET, "zeek"),
    "botiot": (COLMAP_BOTIOT, "argus"),
    "ciciot2023": (COLMAP_CICIOT2023, "ciciot"),
}


def to_canonical_ciciot(df: pd.DataFrame) -> pd.DataFrame:
    """Caminho dedicado ao CICIoT2023: estado vem de contagens de flags."""
    from schema import state_from_flags

    cm = COLMAP_CICIOT2023
    essential = ["duration", "src_bytes", "dst_bytes", "src_pkts", "dst_pkts",
                 "proto", LABEL]
    missing = [cm[k] for k in essential if cm[k] not in df.columns]
    if missing:
        raise KeyError(
            f"Colunas ausentes no CSV do CICIoT2023: {missing}\n"
            f"Colunas disponiveis: {sorted(df.columns.tolist())}\n"
            f"Preencha COLMAP_CICIOT2023 em src/prepare.py com os nomes reais "
            f"(rode antes com --inspect)."
        )

    out = pd.DataFrame()
    for canon in ["duration", "src_bytes", "dst_bytes", "src_pkts", "dst_pkts"]:
        out[canon] = pd.to_numeric(df[cm[canon]], errors="coerce").fillna(0.0)

    # Se a duracao vier em microssegundos, descomente a linha abaixo:
    # out["duration"] = out["duration"] / 1e6

    out["proto"] = df[cm["proto"]].map(map_proto)

    def flags_col(key):
        col = cm.get(key)
        if col and col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index)

    syn, synack = flags_col("syn"), flags_col("synack")
    fin, rst = flags_col("fin"), flags_col("rst")
    has_resp = out["dst_pkts"] > 0
    out["state"] = [
        state_from_flags(s, sa, f, r, hr, p)
        for s, sa, f, r, hr, p in zip(syn, synack, fin, rst, has_resp, out["proto"])
    ]

    raw_label = df[cm[LABEL]].astype(str).str.lower().str.strip()
    out[LABEL] = (~raw_label.isin({"benign", "benigntraffic", "normal", "0"})).astype(int)
    out[ATTACK_TYPE] = raw_label
    out["dataset"] = "ciciot2023"

    out = out[out["duration"] >= 0]
    out = add_derived(out)
    return out


def load_raw(path: str) -> pd.DataFrame:
    """Aceita um CSV unico ou um diretorio com varios CSVs."""
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.csv")))
        if not files:
            raise FileNotFoundError(f"Nenhum CSV encontrado em {path}")
        print(f"[prepare] Lendo {len(files)} arquivo(s) de {path}")
        return pd.concat(
            (pd.read_csv(f, low_memory=False) for f in files),
            ignore_index=True,
        )
    return pd.read_csv(path, low_memory=False)


def to_canonical(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    if dataset == "ciciot2023":
        return to_canonical_ciciot(df)

    colmap, state_source = CONFIG[dataset]

    missing = [src for src in colmap.values() if src not in df.columns]
    if missing:
        raise KeyError(
            f"Colunas ausentes no CSV: {missing}\n"
            f"Colunas disponiveis: {sorted(df.columns.tolist())}\n"
            f"Ajuste COLMAP_{dataset.upper()} em src/prepare.py."
        )

    out = pd.DataFrame()
    for canon in ["duration", "src_bytes", "dst_bytes", "src_pkts", "dst_pkts"]:
        out[canon] = pd.to_numeric(df[colmap[canon]], errors="coerce").fillna(0.0)

    out["proto"] = df[colmap["proto"]].map(map_proto)
    out["state"] = df[colmap["state"]].map(lambda v: map_state(v, state_source))

    raw_label = df[colmap[LABEL]]
    if not pd.api.types.is_numeric_dtype(raw_label):
        out[LABEL] = (~raw_label.astype(str).str.lower().isin(
            {"0", "normal", "benign", "false"})).astype(int)
    else:
        out[LABEL] = pd.to_numeric(raw_label, errors="coerce").fillna(0).astype(int)

    out[ATTACK_TYPE] = df[colmap[ATTACK_TYPE]].astype(str).str.lower()
    out["dataset"] = dataset

    out = out[out["duration"] >= 0]
    out = add_derived(out)
    return out


def sample_keep_rare(out: pd.DataFrame, n_total: int) -> pd.DataFrame:
    """Amostra de n_total fluxos que mantem a classe rara inteira.

    Mesma regra do replicate.py: classes com ate n_total // (numero de classes)
    fluxos entram inteiras; as maiores dividem o restante na proporcao original.
    No BoT-IoT isso mantem os 477 benignos e sorteia os ataques. Uma amostra
    proporcional deixaria uns 39 benignos em 300 mil, e o modelo do Pi
    aprenderia o trafego normal com quase nenhum exemplo.
    Consequencia que voce precisa declarar na apresentacao: a proporcao de
    benignos na amostra fica MAIOR que na base original.
    """
    counts = out[LABEL].value_counts()
    limite = n_total // len(counts)
    pequenas = [c for c in counts.index if counts[c] <= limite]
    grandes = [c for c in counts.index if counts[c] > limite]

    resto = n_total - int(sum(counts[c] for c in pequenas))
    total_grandes = int(sum(counts[c] for c in grandes))
    exato = {c: resto * int(counts[c]) / total_grandes for c in grandes}
    cotas = {c: int(exato[c]) for c in grandes}
    sobra = resto - sum(cotas.values())
    for c in sorted(grandes, key=lambda c: exato[c] - cotas[c], reverse=True)[:sobra]:
        cotas[c] += 1

    partes = [out[out[LABEL] == c] for c in pequenas]
    partes += [out[out[LABEL] == c].sample(n=cotas[c], random_state=42) for c in grandes]
    res = pd.concat(partes).reset_index(drop=True)

    nomes = {0: "benigno", 1: "ataque"}
    print(f"[prepare] Amostra: {len(res):,} fluxos")
    for c in counts.index:
        n = cotas.get(c, int(counts[c]))
        modo = "inteira" if c in pequenas else f"sorteada de {int(counts[c]):,}"
        print(f"[prepare]    {nomes.get(c, c):<8} {n:>9,} ({100 * n / len(res):6.3f}%)  {modo}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(CONFIG), required=True)
    ap.add_argument("--input", required=True, help="CSV ou diretorio de CSVs")
    ap.add_argument("--output", help="arquivo .parquet de saida "
                    "(nao obrigatorio quando se usa --inspect)")
    ap.add_argument("--inspect", action="store_true",
                    help="apenas lista as colunas do CSV e sai")
    ap.add_argument("--sample", type=int, default=0,
                    help="amostra de N linhas que mantem a classe rara inteira "
                         "(0 = tudo)")
    args = ap.parse_args()

    df = load_raw(args.input)
    print(f"[prepare] {len(df):,} linhas brutas")

    if args.inspect:
        print("[prepare] Colunas encontradas:")
        for c in sorted(df.columns):
            print("   ", c)
        return

    if not args.output:
        ap.error("--output e obrigatorio (exceto com --inspect)")

    out = to_canonical(df, args.dataset)

    if args.sample and args.sample < len(out):
        out = sample_keep_rare(out, args.sample)

    written = save_table(out, args.output)

    n_atk = int(out[LABEL].sum())
    print(f"[prepare] Salvo em {written}")
    print(f"[prepare] {len(out):,} fluxos | "
          f"benigno={len(out) - n_atk:,} ataque={n_atk:,} "
          f"({100 * n_atk / max(len(out), 1):.1f}% ataque)")
    print(f"[prepare] Tipos: {out[ATTACK_TYPE].value_counts().head(10).to_dict()}")


if __name__ == "__main__":
    main()
