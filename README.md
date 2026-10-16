# Detecção de Intrusão em IoT com Edge AI

Extensão do artigo-base: acréscimo do Random Forest aos classificadores comparados,
avaliação em duas bases e validação da inferência em Raspberry Pi 3 com tráfego real.

Autora: Beatriz Oliveira Eduão — Engenharia de Computação

---

## Os três problemas que esta estrutura resolve

**1. As features do treino e da captura não batem.**
ToN-IoT vem do Zeek, BoT-IoT vem do Argus e o PyShark entrega pacotes soltos. São
três vocabulários diferentes. `src/schema.py` define um vetor canônico de 11 features
que os três conseguem produzir, e `src/flowmeter.py` reconstrói fluxos a partir de
pacotes. Sem essa camada, o modelo treinado no PC recebe lixo no Pi.

**2. O Raspberry Pi não enxerga o tráfego que precisa classificar.**
Numa rede comutada, o switch entrega ao Pi apenas os quadros destinados a ele. O
tráfego entre o ESP32 e um broker externo passa longe. Solução: **rode o broker
Mosquitto no próprio Raspberry Pi**. Todo tráfego MQTT passa a terminar nele e a
captura em `eth0`/`wlan0` vê tudo, sem espelhamento de porta nem modo promíscuo.

**3. Tráfego ao vivo não vem rotulado.**
Sem rótulo não há métrica. A solução é rotular por construção: separe a coleta em
janelas limpas e passe a fase pelo parâmetro `--phase`. Numa janela só o ESP32
publica (tudo benigno); na outra, você gera tráfego de ataque a partir de outra
máquina contra os seus próprios dispositivos. Ferramentas padrão de teste como
`nmap` (varredura) e `hping3` (inundação SYN/UDP) bastam para reproduzir as
categorias `scanning` e `ddos` que existem nas duas bases.

> **Isolamento obrigatório.** Gere tráfego de ataque exclusivamente contra os seus
> próprios equipamentos, numa rede separada (roteador dedicado ou VLAN isolada).
> Nunca na rede da universidade ou em qualquer rede compartilhada. Além da questão
> legal, tráfego de terceiros contamina o rótulo por construção e invalida a métrica.

---

## Estrutura

```
src/schema.py      vetor canônico de features + mapeamento Zeek/Argus
src/tableio.py     I/O que funciona com ou sem pyarrow
src/prepare.py     CSV bruto -> esquema canônico
src/train.py       6 classificadores, avaliação cruzada, exporta o modelo
src/flowmeter.py   pacotes -> fluxos (roda no Pi)
src/detect.py      inferência ao vivo + medição de latência/RAM/vazão
docker/Dockerfile.pi
```

## Ordem de execução

### No PC

```bash
pip install -r requirements-pc.txt

# 1. Confira os nomes reais das colunas do seu download antes de tudo
python src/prepare.py --dataset toniot --input data/raw/toniot/ --inspect

# 2. Converta as duas bases
python src/prepare.py --dataset toniot --input data/raw/toniot/ \
    --output data/toniot.parquet --sample 400000
python src/prepare.py --dataset botiot --input data/raw/botiot/ \
    --output data/botiot.parquet --sample 400000

# 3. Treine, compare e exporte
python src/train.py --train data/toniot.parquet --test-extra data/botiot.parquet
```

Anote as versões que o `train.py` imprime no final e replique-as em
`requirements-pi.txt`. Divergência de versão no pickle do scikit-learn é a falha
mais comum ao embarcar modelo.

### No Raspberry Pi

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto      # broker na própria borda

docker build -f docker/Dockerfile.pi -t ids-edge .
docker run --rm --net=host \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD/results:/app/results" \
    ids-edge --iface wlan0 --phase benign
```

`--net=host` e as capacidades `NET_RAW`/`NET_ADMIN` não são opcionais: sem elas o
container enxerga apenas a rede virtual do Docker e a captura sai vazia.

Aponte o ESP32 para o IP do Raspberry Pi na porta 1883 e deixe publicando.

### Coleta rotulada

```bash
# Janela 1 — só o ESP32 publicando, ~30 min
docker run ... ids-edge --iface wlan0 --phase benign

# Janela 2 — tráfego de ataque a partir de outra máquina da bancada isolada
docker run ... ids-edge --iface wlan0 --phase attack
```

O CSV resultante traz a coluna `phase` como verdade de campo. Compare com a coluna
`pred` para obter F1, taxa de falso positivo e taxa de falso negativo no tráfego real.

---

## O resultado que provavelmente vai aparecer

Espere a métrica cair bastante do holdout para o tráfego real, e cair de novo na
avaliação cruzada entre bases. Isso é esperado e é um bom resultado, não um fracasso:
o F1 altíssimo relatado na literatura depende de tráfego sintético gerado em testbed,
onde os ataques têm assinatura estatística muito mais limpa do que na prática.

O falso positivo é onde mora a história. Reconexão do ESP32 depois de queda de Wi-Fi,
keepalive do MQTT e mDNS produzem fluxos curtos e unidirecionais, que é exatamente a
forma de uma varredura. Um IDS com 1% de falso positivo numa rede que abre milhares de
fluxos por hora é inutilizável. Meça, mostre a matriz de confusão e discuta.

O enunciado do trabalho é explícito: resultado ruim é resultado, desde que
justificado. Resultado ruim bem explicado vale mais que 99,9% sem explicação.

## Métricas a coletar para a apresentação final

| Métrica | Onde sai |
|---|---|
| F1-macro por classificador, nas 2 bases | `results/metrics.csv` |
| Degradação na avaliação cruzada entre bases | `results/metrics.csv`, linhas `cross_dataset` |
| F1 no tráfego real vs. holdout | `results/live_flows.csv` |
| Latência média e p95 por fluxo no Pi | saída do `detect.py` |
| Pico de RAM e tamanho do modelo | saída do `detect.py` e `models/metadata.json` |
| Vazão em fluxos/s | saída do `detect.py` |

As quatro últimas linhas não existem no artigo original. São a contribuição própria.

---

## Verificação de referências

O enunciado prevê perda de 0 a 6 pontos se qualquer citação for fictícia ou não
corresponder ao que foi afirmado. Antes da apresentação final, abra o PDF do artigo
e confirme uma a uma: autores, ano, periódico, volume, páginas, DOI, quais bases
foram usadas, quais classificadores foram comparados, qual ferramenta foi usada e
qual métrica exata foi relatada. Cite o periódico original, nunca o repositório
onde você baixou a cópia.
