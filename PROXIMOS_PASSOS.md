# Próximos passos (atualizado em 01/11/2026)

Apresentação: **03/11**. Hoje (01/11): Raspberry Pi. Amanhã (02/11): slides,
referências, ensaio e PDF.

Este plano cumpre os níveis P1 e P2 da contingência (`ROTEIRO_IMPLEMENTACAO.md`,
Parte 4). A janela de ataque (P3) ficou opcional: nenhum slide depende dela.

Apresentação: https://claude.ai/artifact/111ATASkggREaNeymkATMM

---

## O que falta nos slides

| Slide | Campo em aberto | De onde sai |
|---|---|---|
| 3 | data de conclusão da validação em hardware | o dia em que o Passo 6 der certo |
| 10 | foto do Pi 3 com o ESP32 | celular, no Passo 4 |
| 10 | latência média e p95 (µs por fluxo) | resumo do `detect.py` |
| 10 | pico de memória (MB) | resumo do `detect.py` |
| 10 | fluxos por segundo | resumo do `detect.py` ("Vazao teorica") |
| 10 | alarmes falsos em N fluxos benignos | resumo do `detect.py` ("Alertas" e "Fluxos classificados") |
| 10 | causa dos alarmes falsos (trocar a frase "só 47 dos 477 benignos são TCP") | Passo 9 e `src/sensibilidade.py` |
| 12 | síntese de latência e memória | depois do slide 10 |
| 13 | periódico, volume e DOI do CICIoT2023 | abrir o artigo (Parte 2) |

---

# Parte 1 — Raspberry Pi (hoje)

Os comandos usam `wlan0`. Se o Pi estiver no cabo, troque por `eth0`.

## Passo 1 — Com internet: conferir o Pi e instalar tudo

O `apt` e o `pip` precisam de internet, e a rede isolada não tem. Faça este passo
com o Pi **e o PC** na rede de casa, e só depois mude para o roteador isolado.

```bash
uname -m                 # esperado: aarch64 (64 bits)
vcgencmd get_throttled   # esperado: throttled=0x0
python3 --version        # 3.11 a 3.13
```

Se `get_throttled` não der `0x0`, a fonte está fraca: troque antes de medir,
porque o Pi reduz o clock e a latência sai inflada.

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients tshark
```

O instalador do tshark pergunta se usuários comuns podem capturar pacotes:
responda **Sim**. Depois ponha o seu usuário no grupo `wireshark` e entre de novo
no SSH (o grupo só vale num login novo):

```bash
sudo dpkg-reconfigure wireshark-common
sudo usermod -aG wireshark $USER
```

Capture **sem `sudo`**. Com `sudo`, o tshark do Pi deu "Permission denied" ao
gravar o arquivo (01/11).

Crie a pasta do projeto no Pi:

```bash
mkdir -p ~/iot/results
```

No **PowerShell do PC**, dentro da pasta do projeto, copie o código e o modelo:

```
scp -r src models requirements-pi.txt <usuario>@<ip-do-pi>:~/iot/
```

De volta ao Pi, crie o ambiente virtual e instale as bibliotecas (demora no Pi 3):

```bash
python3 -m venv ~/iot-venv
~/iot-venv/bin/pip install -r ~/iot/requirements-pi.txt
```

Confira que o modelo carrega:

```bash
cd ~/iot
~/iot-venv/bin/python -c "import joblib; print(joblib.load('models/rf_edge.joblib'))"
```

- **Imprimiu o modelo, sem aviso** → siga.
- **`InconsistentVersionWarning`** → as versões do Pi e do PC divergem. Pare e
  confira o `pip` contra o `requirements-pi.txt`: um modelo carregado em outra
  versão pode dar previsões erradas em silêncio.

## Passo 2 — Mosquitto aceitando o ESP32

O Mosquitto 2 só aceita conexões da própria máquina. `allow_anonymous true` só é
aceitável porque a rede é isolada.

```bash
printf 'listener 1883\nallow_anonymous true\n' | sudo tee /etc/mosquitto/conf.d/lab.conf
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
```

## Passo 3 — Mudar para a rede isolada

Ligue o Pi, o ESP32 e o PC ao roteador isolado. No Pi:

```bash
hostname -I
```

Anote o IP. Se o roteador permitir, reserve esse IP para o Pi: o ESP32 aponta
para ele.

**Sem o roteador isolado (decidido em 01/11):** pule este passo e use a rede de
casa (não a de convidados, que bloqueia a comunicação entre aparelhos). O filtro
`tcp port 1883` deixa o tráfego dos outros aparelhos fora da captura. A janela
de ataque fica proibida nessa rede. O Pi está em `192.168.18.123`.

## Passo 4 — ESP32 publicando

A forma como o ESP32 se conecta decide quantos fluxos você terá para medir:

- **Conexão persistente** (o padrão dos exemplos do PubSubClient): uma única
  conexão TCP aberta o tempo todo. O `flowmeter.py` corta um fluxo ativo a cada
  120 s (`ACTIVE_TIMEOUT`), então 30 minutos dão uns **15 fluxos**. É pouco para
  falar em taxa de alarme falso.
- **Conectar, publicar e desconectar a cada leitura** (recomendado): cada
  publicação vira uma sessão TCP completa (SYN, dados, FIN), com estado
  `CLOSED`. Publicando a cada 5 s, 30 minutos dão uns **360 fluxos**. É como
  funcionam sensores a bateria, que acordam, publicam e dormem. Diga essa
  escolha na apresentação.

O programa (modo recomendado) está em `esp32/publicador_mqtt/`. Nome e senha do
Wi-Fi vão em `segredos.h`, que está no `.gitignore`.

**Plano B (adotado em 01/11):** o ESP32 não foi reconhecido pelo PC com nenhum
dos dois cabos, nem numa porta USB que funciona. Enquanto não houver cabo de
dados, o PC faz o papel do sensor com o mesmo padrão (conecta, publica,
desconecta a cada 5 s), no tópico `lab/pc/telemetria`:

```
py src/publicador_mqtt.py
```

Deixe rodando durante toda a captura (Passos 5 a 7), com o notebook na tomada e
sem entrar em suspensão. Se o ESP32 for gravado depois, refaça os Passos 5 e 6
com ele e troque os números nos slides. Sem o ESP32, os slides 4, 10 e 12
precisam dizer "cliente MQTT no PC simulando o sensor".

Confira no Pi que as mensagens chegam (Portão A do Pi):

```bash
mosquitto_sub -h localhost -t '#' -v
```

Ctrl+C para sair. **Tire a foto do Pi com o ESP32 agora** (slide 10).

## Passo 5 — Gravar o `teste.pcap` (Portão B)

```bash
cd ~/iot
tshark -i wlan0 -f "tcp port 1883" -a duration:1800 -w teste.pcap
```

Grava 30 minutos e para sozinho. Sem `sudo`: ver o Passo 1.

Opcional: copie para o PC (`scp <usuario>@<ip-do-pi>:~/iot/teste.pcap .`) e abra
no Wireshark para ver os pacotes MQTT.

## Passo 6 — Modelo sobre o `teste.pcap` (P1: garante os números do slide 10)

```bash
cd ~/iot
~/iot-venv/bin/python src/detect.py --model models/rf_edge.joblib --pcap teste.pcap --phase benign --out results/pcap_flows.csv | tee results/resumo_pcap.txt
```

Ao terminar, ele imprime o resumo que vai para o slide 10: latência média, p95,
vazão teórica, pico de RAM, alertas e fluxos classificados.

Antes de aceitar os números, abra `results/pcap_flows.csv` e confira: a
quantidade de fluxos bate com o Passo 4 (uns 15 ou uns 360), as durações são
plausíveis e o estado é `CLOSED` no modo recomendado.

O pico de RAM é do processo Python inteiro (Python, pandas, scikit-learn,
PyShark). O tshark que o PyShark abre roda em outro processo e não entra na conta.

## Passo 7 — Captura ao vivo (P2, se der tempo hoje)

Mesmo modelo, lendo da interface em vez do arquivo. Com o ESP32 publicando,
deixe rodar 30 minutos e encerre com Ctrl+C. O resumo sai ao encerrar.

```bash
cd ~/iot
~/iot-venv/bin/python src/detect.py --model models/rf_edge.joblib --iface wlan0 --bpf "tcp port 1883" --phase benign --out results/live_flows.csv
```

O `--bpf "tcp port 1883"` não é opcional: o filtro padrão (`ip`) também captura a
sua sessão SSH, que entraria no CSV como tráfego benigno.

Se o Ctrl+C encerrar com erro e sem resumo, os fluxos já estão gravados no CSV, e
os números do slide 10 continuam vindo do Passo 6.

**Pule o Docker.** Os slides não falam dele, e o build no Pi 3 é lento. O
ambiente virtual mede a mesma inferência.

## Passo 8 — Trazer os resultados para o PC

No PowerShell do PC (ainda na rede isolada), dentro da pasta do projeto:

```
scp "<usuario>@<ip-do-pi>:~/iot/results/*" results/
```

Envie ao Claude o `resumo_pcap.txt`, a foto e, se houver, o resumo da captura ao
vivo, para preencher os slides 3, 10 e 12.

## Passo 9 — Teste de controle: conexão persistente (02/11)

**Por quê.** O Passo 6 deu 350 alarmes falsos em 350 fluxos. Uma sonda com
fluxos montados à mão indicou que a causa principal não é o TCP: é o fluxo ser
pequeno e curto, como os de DoS e DDoS do BoT-IoT. Trocar só `tcp` por `udp`
leva a probabilidade de ataque de 0,98 para 0,77, ainda alarme. Uma conexão
persistente, que fica aberta e acumula as publicações, sairia benigna, mas no
limite (0,38 a 0,47). Este passo testa isso com tráfego real: mesmo sensor,
mesmo broker, mesmo intervalo de 5 s; muda só o padrão de conexão.

Feche o publicador anterior, se ainda estiver aberto. **Primeiro** no Pi (para
o primeiro fluxo ter o SYN):

```bash
cd ~/iot
tshark -i wlan0 -f "tcp port 1883" -a duration:1800 -w teste_persistente.pcap
```

**Depois** no PowerShell do PC, dentro da pasta do projeto:

```
py src/publicador_mqtt.py --persistente
```

Deve aparecer `[publicador] Conectado.` uma vez só. Quando o tshark parar
sozinho (30 min), encerre o publicador com Ctrl+C. No Pi:

```bash
rm -f results/pcap_flows_persistente.csv
~/iot-venv/bin/python src/detect.py --model models/rf_edge.joblib --pcap teste_persistente.pcap --phase benign --out results/pcap_flows_persistente.csv | tee results/resumo_pcap_persistente.txt
cut -d, -f7-10,13,14 results/pcap_flows_persistente.csv
```

Esperado: uns 14 fluxos de cerca de 2 minutos (o `ACTIVE_TIMEOUT` de 120 s corta
a conexão em trechos). O primeiro sai `ESTABLISHED` e os outros `OTHER`, porque
o trecho que continua uma conexão não tem SYN; a sonda indica que isso muda
pouco. Qualquer resultado serve para o slide: se os alarmes caírem, a causa
está mostrada; se não caírem, o modelo é ainda mais frágil.

Depois, refaça o Passo 8 e rode no PC a análise sobre os fluxos reais (precisa
das mesmas versões do `requirements-pi.txt`):

```
py src/sensibilidade.py results/pcap_flows.csv results/pcap_flows_persistente.csv
```

Ela confere que o PC dá as mesmas previsões que o Pi e, mudando uma feature por
vez em todos os fluxos, mostra qual delas sustenta o alarme.

**Resultado (02/11), duas capturas de 30 min:** 6 alarmes falsos em 25 fluxos,
contra 350 em 350 no Passo 6. Os 19 trechos de operação normal passaram, com
P(ataque) de 0,38 a 0,45. Os 6 alarmes são quedas de conexão (RESET, SYN sem
resposta, pacotes do broker sem resposta) e um trecho de 15 s cortado no fim da
gravação. A conexão caiu mesmo com o publicador rodando sem janela, e o log do
Mosquitto mostra que o broker não encerrou nenhuma conexão. O Wi-Fi do Pi está
com `Power Management:on`, uma causa provável. Para testar isso, rode
`sudo iwconfig wlan0 power off` antes de capturar.

## Opcional — Janela de ataque (P3)

Só se todo o resto estiver pronto até amanhã cedo; exige um slide novo. Os
comandos estão em `DIAGNOSTICO_MAQUINA_ATAQUE.md` ("O que você vai rodar de
verdade"). Dois cuidados:

- **Desligue o ESP32** durante a janela, senão os fluxos dele entram rotulados
  como ataque.
- No Pi, use `--phase attack` e um filtro com todas as portas, menos o SSH:
  `--bpf "ip and not port 22"`.

---

# Parte 2 — Apresentação (amanhã, 02/11)

1. **Preencher os slides 3, 10 e 12** com os números do Pi.
2. **Referências** (de 0 a 6 pontos perdidos por uma citação errada). Abra cada
   uma e confira autores, título, periódico, volume, páginas e DOI. Falta
   completar a do CICIoT2023: deve ser *Sensors*, v. 23, n. 13, art. 5941, 2023,
   DOI 10.3390/s23135941. Confirme em https://doi.org/10.3390/s23135941 antes de
   pôr no slide.
3. **Gramática** (vale 1,5 de 5,0): revisar o texto de todos os slides.
4. **Ensaiar com cronômetro**: de 5 a 9 minutos (vale 1,5 de 5,0). As notas dos
   slides somam cerca de 8 minutos. Se passar de 9, corte o slide 11
   ("O que a replicação revelou").
5. **Exportar em PDF e enviar pelo SIGAA** antes de apresentar.

Ficam para depois da apresentação: atualizar o `STATUS.md` (parado em 16/10) e os
dois opcionais dele (CICIoT2023 em outros arquivos e a hipótese da regressão
logística).
