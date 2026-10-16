"""
Treina e compara os classificadores, e exporta o modelo para o Raspberry Pi.

Uso:
    python src/train.py --train data/toniot.parquet --test-extra data/botiot.parquet

Produz:
    models/rf_edge.joblib   modelo escolhido para embarcar
    models/metadata.json    versoes das bibliotecas e ordem das colunas
    results/metrics.csv     tabela comparativa para os slides
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import (  # noqa: E402
    ALL_FEATURES, CATEGORICAL_FEATURES, LABEL, NUMERIC_FEATURES,
)
from tableio import load_table  # noqa: E402

RANDOM_STATE = 42


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def make_models() -> dict:
    """Os cinco do artigo original mais o Random Forest, que e a extensao."""
    return {
        "DecisionTree": DecisionTreeClassifier(
            max_depth=20, min_samples_leaf=5, random_state=RANDOM_STATE),
        "NaiveBayes": GaussianNB(),
        "kNN": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "LinearSVM": SGDClassifier(
            loss="hinge", max_iter=2000, tol=1e-3, random_state=RANDOM_STATE),
        "MLP": MLPClassifier(
            hidden_layer_sizes=(64, 32), max_iter=60, early_stopping=True,
            random_state=RANDOM_STATE),
        # --- a extensao ---
        # Limites de profundidade e folhas mantem o modelo pequeno o bastante
        # para o Raspberry Pi 3 (1 GB de RAM).
        # class_weight e obrigatorio aqui: no BoT-IoT a classe benigna tem
        # 429 registros contra 3,3 milhoes de ataque. Sem reponderar, o
        # modelo aprende a dizer "ataque" sempre e acerta 99,99%.
        "RandomForest": RandomForestClassifier(
            n_estimators=60, max_depth=18, min_samples_leaf=4,
            class_weight="balanced_subsample",
            n_jobs=-1, random_state=RANDOM_STATE),
    }


def evaluate(name, pipe, X_te, y_te, split_name):
    t0 = time.perf_counter()
    y_pred = pipe.predict(X_te)
    infer_s = time.perf_counter() - t0

    try:
        score = pipe.predict_proba(X_te)[:, 1]
        auc = roc_auc_score(y_te, score)
    except (AttributeError, ValueError):
        auc = float("nan")

    tn, fp, fn, tp = confusion_matrix(y_te, y_pred, labels=[0, 1]).ravel()
    return {
        "model": name,
        "split": split_name,
        "f1_macro": f1_score(y_te, y_pred, average="macro"),
        "f1_attack": f1_score(y_te, y_pred, pos_label=1, zero_division=0),
        "roc_auc": auc,
        "false_positive_rate": fp / max(fp + tn, 1),
        "false_negative_rate": fn / max(fn + tp, 1),
        "infer_us_per_flow": 1e6 * infer_s / max(len(X_te), 1),
        "n_test": len(X_te),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True, help="parquet da base principal")
    ap.add_argument("--test-extra", default=None,
                    help="parquet de uma segunda base, para teste cruzado")
    ap.add_argument("--outdir", default="models")
    ap.add_argument("--results", default="results")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(args.results, exist_ok=True)

    df = load_table(args.train)
    X, y = df[ALL_FEATURES], df[LABEL]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE)
    print(f"[train] treino={len(X_tr):,} teste={len(X_te):,} "
          f"| ataque no treino={100 * y_tr.mean():.1f}%")

    extra = None
    if args.test_extra:
        extra = load_table(args.test_extra)
        print(f"[train] base cruzada={len(extra):,} linhas")

    rows, fitted = [], {}
    for name, clf in make_models().items():
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", clf)])
        t0 = time.perf_counter()
        pipe.fit(X_tr, y_tr)
        train_s = time.perf_counter() - t0

        r = evaluate(name, pipe, X_te, y_te, "holdout")
        r["train_s"] = train_s
        rows.append(r)
        fitted[name] = pipe
        print(f"[train] {name:<14} F1-macro={r['f1_macro']:.4f} "
              f"FPR={r['false_positive_rate']:.4f} ({train_s:.1f}s)")

        # Generalizacao entre bases: treina em uma, testa na outra.
        # Costuma derrubar muito a metrica, e esse desabamento e um
        # resultado legitimo e interessante para a apresentacao.
        if extra is not None:
            rx = evaluate(name, pipe, extra[ALL_FEATURES], extra[LABEL], "cross_dataset")
            rows.append(rx)
            print(f"[train] {name:<14} cruzado F1-macro={rx['f1_macro']:.4f}")

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(args.results, "metrics.csv"), index=False)

    best = fitted["RandomForest"]
    model_path = os.path.join(args.outdir, "rf_edge.joblib")
    joblib.dump(best, model_path, compress=3)

    print("\n[train] Relatorio do Random Forest (holdout):")
    print(classification_report(y_te, best.predict(X_te),
                                target_names=["benigno", "ataque"], digits=4))

    meta = {
        "features": ALL_FEATURES,
        "label": LABEL,
        "trained_on": os.path.basename(args.train),
        "sklearn": __import__("sklearn").__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "model_size_kb": round(os.path.getsize(model_path) / 1024, 1),
    }
    with open(os.path.join(args.outdir, "metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    print(f"[train] Modelo salvo: {model_path} ({meta['model_size_kb']} KB)")
    print("[train] IMPORTANTE: instale EXATAMENTE estas versoes no Raspberry Pi:")
    print(f"        scikit-learn=={meta['sklearn']}  numpy=={meta['numpy']}")


if __name__ == "__main__":
    main()
