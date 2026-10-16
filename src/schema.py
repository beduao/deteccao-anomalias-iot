"""
Esquema canonico de features.

Este e o nucleo do projeto. ToN-IoT foi gerada com Zeek/Bro, BoT-IoT com Argus,
e a captura ao vivo no Raspberry Pi produz um terceiro formato. Os tres precisam
ser projetados no MESMO vetor de features, senao o modelo treinado no PC nao
significa nada quando roda na borda.

Regra de ouro: nenhuma feature identificadora (IP, MAC, porta de origem,
timestamp, numero de sequencia). Elas causam vazamento e inflam a metrica.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Features canonicas
# ---------------------------------------------------------------------------

BASE_FEATURES = [
    "duration",    # duracao do fluxo em segundos
    "src_bytes",   # bytes enviados pela origem
    "dst_bytes",   # bytes enviados pelo destino
    "src_pkts",    # pacotes enviados pela origem
    "dst_pkts",    # pacotes enviados pelo destino
]

DERIVED_FEATURES = [
    "bytes_per_pkt_src",
    "bytes_per_pkt_dst",
    "pkts_per_sec",
    "bytes_ratio",
]

CATEGORICAL_FEATURES = [
    "proto",   # tcp | udp | icmp | other
    "state",   # ESTABLISHED | CLOSED | ATTEMPT | RESET | OTHER
]

NUMERIC_FEATURES = BASE_FEATURES + DERIVED_FEATURES
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

LABEL = "label"          # 0 = benigno, 1 = ataque
ATTACK_TYPE = "attack_type"   # so para analise, nunca entra no treino

PROTO_VALUES = ["tcp", "udp", "icmp", "other"]
STATE_VALUES = ["ESTABLISHED", "CLOSED", "ATTEMPT", "RESET", "OTHER"]


# ---------------------------------------------------------------------------
# Mapeamento de estado de conexao
# ---------------------------------------------------------------------------
# Zeek e Argus descrevem o estado da conexao com vocabularios diferentes.
# Reduzimos os dois a cinco classes semanticas comuns. Essa tabela e um
# resultado do trabalho: vale um slide na apresentacao final.

ZEEK_STATE_MAP = {
    "S1": "ESTABLISHED", "S2": "ESTABLISHED", "S3": "ESTABLISHED",
    "SF": "CLOSED",
    "S0": "ATTEMPT", "SH": "ATTEMPT", "SHR": "ATTEMPT",
    "REJ": "RESET", "RSTO": "RESET", "RSTR": "RESET",
    "RSTOS0": "RESET", "RSTRH": "RESET",
    "OTH": "OTHER",
}

ARGUS_STATE_MAP = {
    "CON": "ESTABLISHED", "ACC": "ESTABLISHED", "EST": "ESTABLISHED",
    "FIN": "CLOSED", "CLO": "CLOSED",
    "INT": "ATTEMPT", "REQ": "ATTEMPT",
    "RST": "RESET",
    "URP": "OTHER", "ECO": "OTHER", "NRS": "OTHER",
    "TST": "OTHER", "MAS": "OTHER", "TXD": "OTHER",
}


# CICIoT2023 nao traz um campo de estado de conexao pronto. O extrator deles
# (o CICFlowMeter adaptado) entrega, em vez disso, CONTAGENS de flags TCP por
# fluxo: quantos SYN, quantos FIN, quantos RST, etc. Entao o estado precisa ser
# INFERIDO dessas contagens, com a mesma logica do flowmeter ao vivo. A funcao
# state_from_flags abaixo faz isso e e usada tanto aqui quanto na captura.

def state_from_flags(syn=0, synack=0, fin=0, rst=0, has_response=False,
                     proto="tcp") -> str:
    """Infere o estado canonico a partir de contagens de flags TCP.

    Serve para o CICIoT2023 (que da contagens) e espelha a logica do
    FlowMeter em flowmeter.py, garantindo que as tres fontes concordem.
    """
    if str(proto).lower() != "tcp":
        return "CLOSED" if has_response else "ATTEMPT"
    if rst and int(rst) > 0:
        return "RESET"
    if fin and int(fin) > 0 and has_response:
        return "CLOSED"
    if synack and int(synack) > 0:
        return "ESTABLISHED"
    if syn and int(syn) > 0:
        return "ATTEMPT"
    return "OTHER"


def map_state(raw: str, source: str) -> str:
    """Traduz o estado bruto para o vocabulario canonico.

    Vale para Zeek e Argus, que trazem um codigo de estado textual. O
    CICIoT2023 nao usa esta funcao: la o estado sai de state_from_flags,
    chamado dentro do prepare.py.
    """
    if raw is None:
        return "OTHER"
    key = str(raw).strip().upper()
    table = ZEEK_STATE_MAP if source == "zeek" else ARGUS_STATE_MAP
    return table.get(key, "OTHER")


def map_proto(raw: str) -> str:
    """Normaliza o protocolo. Numeros IANA tambem sao aceitos."""
    if raw is None:
        return "other"
    key = str(raw).strip().lower()
    if key in {"6", "tcp"}:
        return "tcp"
    if key in {"17", "udp"}:
        return "udp"
    if key in {"1", "58", "icmp", "ipv6-icmp"}:
        return "icmp"
    return "other"


# ---------------------------------------------------------------------------
# Features derivadas
# ---------------------------------------------------------------------------

def add_derived(df):
    """Acrescenta as features derivadas. Divisoes protegidas contra zero."""
    import numpy as np

    dur = df["duration"].to_numpy(dtype="float64")
    sb = df["src_bytes"].to_numpy(dtype="float64")
    db = df["dst_bytes"].to_numpy(dtype="float64")
    sp = df["src_pkts"].to_numpy(dtype="float64")
    dp = df["dst_pkts"].to_numpy(dtype="float64")

    eps = 1e-6
    df["bytes_per_pkt_src"] = sb / np.maximum(sp, eps)
    df["bytes_per_pkt_dst"] = db / np.maximum(dp, eps)
    df["pkts_per_sec"] = (sp + dp) / np.maximum(dur, eps)
    df["bytes_ratio"] = sb / np.maximum(sb + db, eps)

    for col in DERIVED_FEATURES:
        df[col] = df[col].replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return df


def derive_live(duration, src_bytes, dst_bytes, src_pkts, dst_pkts):
    """Versao escalar das derivadas, para uso na inferencia ao vivo."""
    eps = 1e-6
    return {
        "bytes_per_pkt_src": src_bytes / max(src_pkts, eps),
        "bytes_per_pkt_dst": dst_bytes / max(dst_pkts, eps),
        "pkts_per_sec": (src_pkts + dst_pkts) / max(duration, eps),
        "bytes_ratio": src_bytes / max(src_bytes + dst_bytes, eps),
    }
