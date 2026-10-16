"""
Inferencia na borda: roda no Raspberry Pi.

Uso:
    python src/detect.py --model models/rf_edge.joblib --iface eth0
    python src/detect.py --model models/rf_edge.joblib --pcap captura.pcap  # offline

Registra cada fluxo classificado em CSV, com latencia de inferencia por fluxo.
Esses numeros sao o resultado principal do trabalho: o artigo original nao tem
latencia, memoria nem vazao, porque nunca saiu do Orange-3.
"""

from __future__ import annotations

import argparse
import csv
import os
import resource
import signal
import sys
import time

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flowmeter import FlowMeter  # noqa: E402
from schema import ALL_FEATURES  # noqa: E402

RUNNING = True


def _stop(signum, frame):
    global RUNNING
    RUNNING = False
    print("\n[detect] Encerrando...")


def peak_rss_mb() -> float:
    # No Linux ru_maxrss vem em kilobytes.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def classify(model, features: dict):
    row = pd.DataFrame([features])[ALL_FEATURES]
    t0 = time.perf_counter()
    pred = int(model.predict(row)[0])
    latency_us = 1e6 * (time.perf_counter() - t0)
    try:
        conf = float(model.predict_proba(row)[0][pred])
    except (AttributeError, ValueError):
        conf = float("nan")
    return pred, conf, latency_us


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--iface", default=None, help="interface de captura, ex: eth0")
    ap.add_argument("--pcap", default=None, help="arquivo .pcap (modo offline)")
    ap.add_argument("--bpf", default="ip", help="filtro BPF, ex: 'tcp port 1883'")
    ap.add_argument("--out", default="results/live_flows.csv")
    ap.add_argument("--phase", default="unlabeled",
                    help="rotulo por construcao: benign | attack")
    args = ap.parse_args()

    if not (args.iface or args.pcap):
        ap.error("informe --iface ou --pcap")

    import pyshark  # importado aqui para o modo offline nao exigir tshark antes

    print(f"[detect] Carregando {args.model} ...")
    t0 = time.perf_counter()
    model = joblib.load(args.model)
    print(f"[detect] Modelo carregado em {time.perf_counter() - t0:.2f}s")

    meter = FlowMeter()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fh = open(args.out, "a", newline="")
    writer = csv.writer(fh)
    if fh.tell() == 0:
        writer.writerow(["ts", "src_ip", "src_port", "dst_ip", "dst_port", "proto",
                         "state", "duration", "src_pkts", "dst_pkts",
                         "src_bytes", "dst_bytes", "pred", "confidence",
                         "latency_us", "phase"])

    signal.signal(signal.SIGINT, _stop)

    if args.pcap:
        cap = pyshark.FileCapture(args.pcap, keep_packets=False)
    else:
        cap = pyshark.LiveCapture(interface=args.iface, bpf_filter=args.bpf)

    n_pkts = n_flows = n_alerts = 0
    latencies = []
    started = time.time()

    def emit(pairs):
        nonlocal n_flows, n_alerts
        for key, feats in pairs:
            pred, conf, lat = classify(model, feats)
            latencies.append(lat)
            n_flows += 1
            writer.writerow([
                f"{time.time():.3f}", key[0], key[1], key[2], key[3], key[4],
                feats["state"], f"{feats['duration']:.3f}",
                int(feats["src_pkts"]), int(feats["dst_pkts"]),
                int(feats["src_bytes"]), int(feats["dst_bytes"]),
                pred, f"{conf:.4f}", f"{lat:.1f}", args.phase,
            ])
            if pred == 1:
                n_alerts += 1
                print(f"[ALERTA] {key[0]}:{key[1]} -> {key[2]}:{key[3]} "
                      f"{key[4]} {feats['state']} conf={conf:.3f}")
        fh.flush()

    try:
        for pkt in cap.sniff_continuously() if not args.pcap else cap:
            if not RUNNING:
                break
            meter.add(pkt)
            n_pkts += 1
            if n_pkts % 50 == 0:
                # No .pcap, o "agora" e o horario do pacote lido: os pacotes
                # gravados tem horario do passado e, comparados ao relogio,
                # toda conexao pareceria ociosa e seria fechada aos pedacos.
                emit(meter.expire(now=float(pkt.sniff_timestamp) if args.pcap else None))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        emit(meter.flush())
        fh.close()
        try:
            cap.close()
        except Exception:
            pass

    elapsed = time.time() - started
    print("\n" + "=" * 58)
    print(f"  Pacotes processados : {n_pkts:,}")
    print(f"  Fluxos classificados: {n_flows:,}")
    print(f"  Alertas (ataque)    : {n_alerts:,}")
    if latencies:
        s = sorted(latencies)
        print(f"  Latencia media      : {sum(s) / len(s):.1f} us/fluxo")
        print(f"  Latencia p95        : {s[int(0.95 * len(s))]:.1f} us/fluxo")
        print(f"  Vazao teorica       : {1e6 / (sum(s) / len(s)):,.0f} fluxos/s")
    print(f"  Pico de RAM         : {peak_rss_mb():.1f} MB")
    print(f"  Tempo total         : {elapsed:.1f}s")
    print("=" * 58)
    print(f"  Log salvo em: {args.out}")


if __name__ == "__main__":
    main()
