"""
Analise de sensibilidade dos alarmes do Pi, feita no PC.

Uso:
    py src/sensibilidade.py results/pcap_flows.csv [outro.csv ...]

Le o CSV que o detect.py grava, refaz as features de cada fluxo e confere que
o modelo no PC da a mesma previsao que deu no Pi. Depois muda uma feature por
vez em todos os fluxos e conta quantos continuam marcados como ataque. Responde
a pergunta "o alarme vem do protocolo, do estado, da duracao ou do volume?".
"""

from __future__ import annotations

import argparse
import os
import sys

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import ALL_FEATURES, add_derived  # noqa: E402

BASE = ["duration", "src_bytes", "dst_bytes", "src_pkts", "dst_pkts", "proto", "state"]

# Cada variante muda uma coisa em todos os fluxos; as derivadas sao refeitas.
VARIANTS = {
    "protocolo udp": lambda d: d.assign(proto="udp"),
    "estado ESTABLISHED": lambda d: d.assign(state="ESTABLISHED"),
    "duracao x10": lambda d: d.assign(duration=d.duration * 10),
    "duracao x100": lambda d: d.assign(duration=d.duration * 100),
    "bytes x10": lambda d: d.assign(src_bytes=d.src_bytes * 10,
                                    dst_bytes=d.dst_bytes * 10),
    "pacotes e bytes x10": lambda d: d.assign(src_bytes=d.src_bytes * 10,
                                              dst_bytes=d.dst_bytes * 10,
                                              src_pkts=d.src_pkts * 10,
                                              dst_pkts=d.dst_pkts * 10),
}


def predict(model, base: pd.DataFrame):
    X = add_derived(base.copy())[ALL_FEATURES]
    attack = list(model.classes_).index(1)
    return model.predict(X), model.predict_proba(X)[:, attack]


def fmt(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def analyze(model, path: str) -> None:
    flows = pd.read_csv(path)
    base = flows[BASE].astype({c: "float64" for c in BASE[:5]})
    n = len(base)
    pred, proba = predict(model, base)

    print(f"\n== {path}: {n} fluxos")
    # O CSV guarda a duracao com 3 casas; num fluxo de 30 ms isso mexe um
    # pouco em pkts_per_sec e pode virar uma previsao que estava no limite.
    same = int((pred == flows["pred"].to_numpy()).sum())
    print(f"Pi e PC concordam em {same} de {n} previsoes")
    print(f"Alarmes: {int(pred.sum())} de {n}   P(ataque): mediana {fmt(pd.Series(proba).median())}, "
          f"min {fmt(proba.min())}, max {fmt(proba.max())}")
    med = base.median(numeric_only=True)
    print(f"Fluxo mediano: {fmt(med.duration)} s, {med.src_pkts:g}+{med.dst_pkts:g} pacotes, "
          f"{med.src_bytes:g}+{med.dst_bytes:g} bytes; "
          f"{', '.join(f'{k} {v}' for k, v in (base.proto + ' ' + base.state).value_counts().items())}")

    print("\nMudando uma coisa por vez em todos os fluxos:")
    print(f"  {'variante':22s} {'alarmes':>10s}   P(ataque) mediana")
    print(f"  {'(original)':22s} {int(pred.sum()):>4d} de {n:<4d}  {fmt(pd.Series(proba).median())}")
    for name, change in VARIANTS.items():
        p, pr = predict(model, change(base))
        print(f"  {name:22s} {int(p.sum()):>4d} de {n:<4d}  {fmt(pd.Series(pr).median())}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("flows", nargs="+", help="CSV(s) gravados pelo detect.py")
    ap.add_argument("--model", default="models/rf_edge.joblib")
    args = ap.parse_args()

    model = joblib.load(args.model)
    clf = model[-1] if hasattr(model, "steps") else model
    if hasattr(clf, "n_jobs"):
        clf.n_jobs = 1
    for path in args.flows:
        analyze(model, path)


if __name__ == "__main__":
    main()
