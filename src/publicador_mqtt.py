"""
Cliente MQTT que faz o papel do sensor quando o ESP32 nao pode ser gravado.

Uso (no PC, na mesma rede do Raspberry Pi):
    py src/publicador_mqtt.py --broker 192.168.18.123

Repete o padrao de esp32/publicador_mqtt: a cada leitura conecta ao broker,
publica e desconecta, e cada publicacao vira uma sessao TCP completa
(SYN ... FIN). So usa a biblioteca padrao: os pacotes MQTT 3.1.1 (CONNECT,
PUBLISH com QoS 0 e DISCONNECT) sao montados aqui mesmo.

Com --persistente, abre uma unica conexao e publica nela o tempo todo, como
os exemplos do PubSubClient. E o teste de controle de 02/11: mesmo sensor e
mesmo intervalo, so muda o padrao de conexao.
"""

from __future__ import annotations

import argparse
import json
import random
import socket
import struct
import time

DISCONNECT = bytes([0xE0, 0x00])


def _remaining_length(n: int) -> bytes:
    # Comprimento restante do MQTT: 7 bits por byte, bit alto = "tem mais".
    out = bytearray()
    while True:
        byte, n = n % 128, n // 128
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _string(s: str) -> bytes:
    data = s.encode("utf-8")
    return struct.pack("!H", len(data)) + data


def _packet(header: int, body: bytes) -> bytes:
    return bytes([header]) + _remaining_length(len(body)) + body


def connect_packet(client_id: str, keepalive: int = 60) -> bytes:
    # Protocolo "MQTT" nivel 4 (3.1.1), flag clean session.
    body = _string("MQTT") + bytes([4, 0x02]) + struct.pack("!H", keepalive)
    return _packet(0x10, body + _string(client_id))


def publish_packet(topic: str, payload: bytes) -> bytes:
    # QoS 0: sem identificador de pacote e sem resposta do broker.
    return _packet(0x30, _string(topic) + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("broker fechou a conexao antes do CONNACK")
        data += chunk
    return data


def connect(broker: str, port: int, client_id: str, keepalive: int = 60,
            timeout: float = 5.0) -> socket.socket:
    sock = socket.create_connection((broker, port), timeout=timeout)
    try:
        sock.sendall(connect_packet(client_id, keepalive))
        connack = _recv_exact(sock, 4)
        if connack[0] != 0x20 or connack[3] != 0:
            raise ConnectionError(f"broker recusou a conexao (CONNACK {connack.hex()})")
    except BaseException:
        sock.close()
        raise
    return sock


def disconnect(sock: socket.socket) -> None:
    with sock:
        sock.sendall(DISCONNECT)
        # Fecha o envio e espera o broker fechar o lado dele. Fechar com dado
        # nao lido faria o Windows mandar RST em vez de FIN.
        sock.shutdown(socket.SHUT_WR)
        while sock.recv(64):
            pass


def publish_once(broker: str, port: int, client_id: str, topic: str,
                 payload: bytes, timeout: float = 5.0) -> None:
    sock = connect(broker, port, client_id, timeout=timeout)
    try:
        sock.sendall(publish_packet(topic, payload))
    except BaseException:
        sock.close()
        raise
    disconnect(sock)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="192.168.18.123", help="IP do Raspberry Pi")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--topic", default="lab/pc/telemetria")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="segundos entre publicacoes")
    ap.add_argument("--count", type=int, default=0,
                    help="publicacoes antes de parar (0 = sem limite)")
    ap.add_argument("--persistente", action="store_true",
                    help="uma unica conexao aberta o tempo todo, em vez de "
                         "conectar e desconectar a cada publicacao")
    args = ap.parse_args()

    # O broker derruba o cliente que passa 1,5 keepalive sem mandar nada.
    keepalive = max(60, int(2 * args.interval) + 1)
    modo = "conexao persistente" if args.persistente else "uma conexao por publicacao"
    print(f"[publicador] {args.broker}:{args.port}, topico {args.topic}, "
          f"a cada {args.interval:g} s, {modo}. Ctrl+C para parar.")
    sent = 0
    sock = None
    try:
        while True:
            # Leitura sintetica, como no ESP32: o valor nao muda o resultado.
            payload = json.dumps({"n": sent,
                                  "temp": round(24.0 + random.uniform(0, 5), 1),
                                  "umid": round(55.0 + random.uniform(0, 10), 1)},
                                 separators=(",", ":")).encode()
            try:
                if args.persistente:
                    if sock is None:
                        sock = connect(args.broker, args.port, "pc-sensor", keepalive)
                        print("[publicador] Conectado.")
                    sock.sendall(publish_packet(args.topic, payload))
                else:
                    publish_once(args.broker, args.port, "pc-sensor", args.topic, payload)
                sent += 1
                print(f"Publicado: {payload.decode()}")
            except OSError as exc:
                print(f"Falha ao publicar: {exc}")
                if sock is not None:
                    # Reconecta na proxima leitura, como o PubSubClient.
                    sock.close()
                    sock = None
            if args.count and sent >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        if sock is not None:
            try:
                disconnect(sock)
            except OSError:
                pass
    print(f"\n[publicador] {sent} mensagens publicadas.")


if __name__ == "__main__":
    main()
