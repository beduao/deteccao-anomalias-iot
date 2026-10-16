"""
Agregador de fluxos para captura ao vivo.

Esta e a peca que falta na maioria dos trabalhos que tentam levar um IDS
treinado em CSV para a rede real. O modelo foi treinado com features de FLUXO
(Zeek/Argus), mas o PyShark entrega PACOTES. Sem esta camada de agregacao,
alimentar o modelo com dados de pacote produz lixo.

Um fluxo e identificado por (ip_origem, porta_origem, ip_destino, porta_destino,
protocolo), com direcao normalizada: quem envia o primeiro pacote e a origem.
O fluxo e emitido quando fica ocioso por IDLE_TIMEOUT ou vive mais que
ACTIVE_TIMEOUT.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import derive_live  # noqa: E402

IDLE_TIMEOUT = 15.0     # segundos sem pacote -> fecha o fluxo
ACTIVE_TIMEOUT = 120.0  # duracao maxima antes de emitir mesmo ativo


@dataclass
class Flow:
    proto: str
    first_ts: float
    last_ts: float
    src_bytes: int = 0
    dst_bytes: int = 0
    src_pkts: int = 0
    dst_pkts: int = 0
    flags: set = field(default_factory=set)  # 'SYN','SYNACK','FIN_S','FIN_D','RST'

    def state(self) -> str:
        """Infere o estado canonico. Espelha a semantica do Zeek conn_state."""
        if self.proto == "tcp":
            if "RST" in self.flags:
                return "RESET"
            if "FIN_S" in self.flags and "FIN_D" in self.flags:
                return "CLOSED"
            if "SYNACK" in self.flags:
                return "ESTABLISHED"
            if "SYN" in self.flags:
                return "ATTEMPT"
            return "OTHER"
        # UDP/ICMP nao tem handshake: bidirecional equivale a SF, unidirecional a S0.
        if self.dst_pkts > 0:
            return "CLOSED"
        return "ATTEMPT"

    def to_features(self) -> dict:
        duration = max(self.last_ts - self.first_ts, 0.0)
        feats = {
            "duration": duration,
            "src_bytes": float(self.src_bytes),
            "dst_bytes": float(self.dst_bytes),
            "src_pkts": float(self.src_pkts),
            "dst_pkts": float(self.dst_pkts),
            "proto": self.proto,
            "state": self.state(),
        }
        feats.update(derive_live(duration, self.src_bytes, self.dst_bytes,
                                 self.src_pkts, self.dst_pkts))
        return feats


class FlowMeter:
    """Consome pacotes do PyShark e devolve fluxos completos."""

    def __init__(self, idle=IDLE_TIMEOUT, active=ACTIVE_TIMEOUT):
        self.flows: dict[tuple, Flow] = {}
        self.idle = idle
        self.active = active

    @staticmethod
    def _parse(pkt):
        """Extrai o que interessa de um pacote PyShark. None se irrelevante."""
        try:
            if hasattr(pkt, "ip"):
                src_ip, dst_ip = pkt.ip.src, pkt.ip.dst
            elif hasattr(pkt, "ipv6"):
                src_ip, dst_ip = pkt.ipv6.src, pkt.ipv6.dst
            else:
                return None

            length = int(pkt.length)
            ts = float(pkt.sniff_timestamp)
            flags = set()

            if hasattr(pkt, "tcp"):
                proto = "tcp"
                sport, dport = int(pkt.tcp.srcport), int(pkt.tcp.dstport)
                syn = pkt.tcp.flags_syn == "1"
                ack = pkt.tcp.flags_ack == "1"
                if syn and ack:
                    flags.add("SYNACK")
                elif syn:
                    flags.add("SYN")
                if pkt.tcp.flags_reset == "1":
                    flags.add("RST")
                if pkt.tcp.flags_fin == "1":
                    flags.add("FIN")
            elif hasattr(pkt, "udp"):
                proto = "udp"
                sport, dport = int(pkt.udp.srcport), int(pkt.udp.dstport)
            elif hasattr(pkt, "icmp") or hasattr(pkt, "icmpv6"):
                proto, sport, dport = "icmp", 0, 0
            else:
                return None

            return src_ip, sport, dst_ip, dport, proto, length, ts, flags
        except AttributeError:
            return None

    def add(self, pkt) -> None:
        parsed = self._parse(pkt)
        if parsed is None:
            return
        src_ip, sport, dst_ip, dport, proto, length, ts, flags = parsed

        fwd_key = (src_ip, sport, dst_ip, dport, proto)
        rev_key = (dst_ip, dport, src_ip, sport, proto)

        if fwd_key in self.flows:
            flow, forward = self.flows[fwd_key], True
        elif rev_key in self.flows:
            flow, forward = self.flows[rev_key], False
        else:
            flow = Flow(proto=proto, first_ts=ts, last_ts=ts)
            self.flows[fwd_key] = flow
            forward = True

        flow.last_ts = ts
        if forward:
            flow.src_bytes += length
            flow.src_pkts += 1
            if "FIN" in flags:
                flow.flags.add("FIN_S")
        else:
            flow.dst_bytes += length
            flow.dst_pkts += 1
            if "FIN" in flags:
                flow.flags.add("FIN_D")
        flow.flags |= (flags - {"FIN"})

    def expire(self, now: float | None = None):
        """Emite (chave, features) dos fluxos que terminaram."""
        now = now if now is not None else time.time()
        done = []
        for key, flow in list(self.flows.items()):
            if (now - flow.last_ts) > self.idle or \
               (flow.last_ts - flow.first_ts) > self.active:
                done.append((key, flow.to_features()))
                del self.flows[key]
        return done

    def flush(self):
        """Emite tudo que sobrou (ao encerrar a captura)."""
        done = [(k, f.to_features()) for k, f in self.flows.items()]
        self.flows.clear()
        return done
