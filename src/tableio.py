"""
Leitura e escrita de tabelas sem depender de pyarrow.

O pyarrow e pesado e frequentemente problematico de compilar no Raspberry Pi.
Se ele existir, usamos parquet (menor e mais rapido). Se nao, caimos para
CSV comprimido, que funciona em qualquer lugar.
"""

from __future__ import annotations

import os
import pandas as pd


def _has_parquet() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        try:
            import fastparquet  # noqa: F401
            return True
        except ImportError:
            return False


def resolve_path(path: str) -> str:
    """Ajusta a extensao ao que o ambiente consegue escrever."""
    root, ext = os.path.splitext(path)
    if ext == ".parquet" and not _has_parquet():
        return root + ".csv.gz"
    return path


def save_table(df: pd.DataFrame, path: str) -> str:
    path = resolve_path(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if path.endswith(".parquet"):
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False, compression="infer")
    return path


def load_table(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        alt = resolve_path(path)
        if os.path.exists(alt):
            path = alt
        else:
            raise FileNotFoundError(f"Nao encontrei {path} nem {alt}")
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path, compression="infer", low_memory=False)
