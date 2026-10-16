# Roteiro de implementação

Documento operacional. Marque cada caixa antes de avançar.

Atualizado em 06/10/2026. Apresentação de resultados: 05/11 a 19/11/2026.
Você é a 8ª no sorteio, então planeje para apresentar perto de **05/11**.
Prazo útil: **4 semanas.** O plano original de 8 semanas foi comprimido na Parte 3.

Já pronto: Ubuntu de ataque testado (nmap e hping3), Raspberry Pi com OS 64 bits,
roteador isolado disponível, estudo do `ROTEIRO_ESTUDO.md` concluído.
Falta: **as bases de dados.** É o caminho crítico.

---

# Parte 1 — O que você precisa TER

## 1.1 Hardware

| Item | Situação | Observação |
|---|---|---|
| Raspberry Pi 3 Model B | você tem | 1 GB de RAM, ARM Cortex-A53. É o gargalo do projeto |
| ESP32 | você tem | qualquer variante serve |
| Cartão microSD 16 GB+ | **confirmar** | classe 10 ou melhor. Cartão lento trava o Pi |
| Fonte 5V 2,5A para o Pi | **confirmar** | crítico. Fonte fraca causa subtensão, throttling e falhas aleatórias que parecem bug de software |
| Cabo USB de **dados** para o ESP32 | **confirmar** | muito cabo de celular é só carga. Se o computador não reconhecer a porta serial, é isso |
| Roteador ou ponto de acesso dedicado | **decisão** | ver seção 1.4 |
| Máquina para gerar tráfego de ataque | **decisão** | ver seção 1.4 |
| Cabo de rede | opcional | captura em `eth0` é mais estável que em `wlan0` |
| Sensor físico (DHT22, BMP280) | opcional | o ESP32 pode publicar valores sintéticos. Não muda o resultado |

## 1.2 Software no PC (Windows 11 Pro)

| Item | Para quê |
|---|---|
| Python 3.11 ou 3.12 | treino. Evite a 3.13, algumas rodas científicas ainda atrasam |
| `requirements-pc.txt` instalado | scikit-learn, pandas, numpy, joblib, matplotlib |
| Git | versionar. Você vai quebrar coisas e vai querer voltar |
| Raspberry Pi Imager | gravar o sistema no cartão |
| Cliente SSH | já vem no Windows 11, use pelo PowerShell |
| Wireshark | **essencial**. Antes de depurar PyShark, veja os pacotes com os próprios olhos |
| Arduino IDE ou PlatformIO | programar o ESP32 |

## 1.3 Software no Raspberry Pi

| Item | Detalhe |
|---|---|
| **Raspberry Pi OS 64 bits** | obrigatório. Em 32 bits não existem rodas prontas de numpy e scikit-learn para ARM, e o pip tenta compilar do zero — horas de espera, com chance grande de falhar por falta de RAM |
| Docker | `curl -sSL https://get.docker.com \| sh` |
| Mosquitto | broker MQTT, roda no próprio Pi |
| tshark | backend do PyShark |

## 1.4 As duas decisões que você precisa tomar agora

### Decisão A — como isolar a rede

Você precisa de uma rede onde só existam os seus equipamentos. Opções, da melhor
para a mais improvisada:

1. **Roteador Wi-Fi antigo dedicado**, sem cabo na WAN. Melhor opção: isolamento
   real, controle total, DHCP funcionando.
2. **Raspberry Pi como ponto de acesso** (hostapd + dnsmasq). Funciona, mas dá
   trabalho de configurar e sobrecarrega o Pi, que já vai capturar e classificar.
3. **Roteador de viagem** ou repetidor em modo AP. Barato e resolve.
4. **Hotspot do celular**. Última opção: você não controla o DHCP, pode haver
   tráfego de fundo do próprio celular contaminando a captura, e alguns operadores
   bloqueiam comunicação entre clientes.

Não use a rede da universidade nem a rede de casa compartilhada. Além da questão
legal e ética, tráfego de terceiros entrando nas janelas de coleta contamina o
rótulo por construção e invalida toda a medição.

### Decisão B — de onde sai o tráfego de ataque

Aqui mora o problema prático que mais pega gente desprevenida: **o Windows não roda
as ferramentas padrão**. O `nmap` tem versão Windows, mas o `hping3` é só Linux, e
o WSL2 usa NAT por padrão, o que impede enviar pacotes crus para a rede local.

Opções:

1. **Máquina virtual Linux com adaptador em modo bridge** (VirtualBox ou VMware).
   Mais acessível. O modo bridge faz a VM aparecer como um host próprio na rede.
   Recomendo esta.
2. **Pendrive com Ubuntu live** num notebook. Funciona e não mexe no seu sistema.
3. **Segundo Raspberry Pi ou notebook antigo com Linux**, se você tiver.
4. **Só `nmap` no Windows**, com Npcap. Dá para fazer varredura (categoria
   *scanning* / *reconnaissance*), mas não inundação. Reduz o escopo do ataque a
   uma categoria só. Aceitável como plano B.

> Resolva a decisão B **esta semana**. Ela é o item com maior chance de te travar
> em outubro, quando já não há tempo de mudar de estratégia.

## 1.5 As bases de dados

**BoT-IoT, versão "10 best features"** — é a que importa. São 4 arquivos CSV,
aproximadamente 0,78 GB, cerca de 3,6 milhões de linhas. A base completa tem 69,3
GB; você **não** precisa dela.

**ToN-IoT Windows 7 e Windows 10** — os arquivos que Inuwa e Das realmente usaram.
São pequenos, dezenas de MB.

**ToN-IoT Network** — opcional, é a sua segunda base de rede para a avaliação
cruzada.

Todas são mantidas pelo grupo de pesquisa da UNSW Canberra. O acesso costuma exigir
preencher um formulário, e o link muda de tempos em tempos. **Procure a página
oficial e confira antes de baixar** — não confie em espelho de terceiros, porque
versões modificadas circulam por aí e você não vai saber o que mudou.

Peça acesso **nesta semana**. Aprovação por formulário pode demorar dias.

Espaço em disco: reserve 10 GB no PC com folga.

---

# Parte 2 — O que você precisa SABER

Autoavaliação honesta. Para cada item, decida: domino, sei o básico, ou nunca vi.
Onde faltar, o tempo estimado é de estudo focado, não de curso completo.

## 2.1 Indispensável antes de começar

**Python com pandas** — ler CSV, entender o que é um DataFrame, filtrar linhas,
selecionar colunas, agrupar. Se nunca usou pandas, reserve 4 a 6 horas. Não precisa
saber escrever os scripts do zero, mas precisa conseguir ler e modificar.

**Linha de comando** — navegar entre pastas, rodar script com argumentos, instalar
pacote com pip, ler mensagem de erro até o fim. 2 horas se for novo.

**Conceitos de ML supervisionado** — divisão treino/teste e por que ela existe,
sobreajuste, matriz de confusão, precisão, revocação, F1. Se você não consegue
explicar a diferença entre precisão e revocação para alguém, estude isso primeiro.
É o que a banca mais provavelmente vai perguntar. 3 a 4 horas.

**Redes básicas** — o que é IP, porta, protocolo. O handshake TCP de três vias
(SYN, SYN-ACK, ACK) e o que significa um SYN sem resposta. O que um switch faz e
por que ele não entrega tudo para todo mundo. Você é de Engenharia de Computação,
provavelmente já viu; revise o handshake. 2 horas.

## 2.2 Pode aprender durante o caminho

**Linux no Raspberry Pi** — ssh, apt install, systemctl, sudo, editar arquivo com
nano. Aprende fazendo, na semana 5.

**Docker** — build, run, e o que fazem as flags `--net=host`, `--cap-add`, `-v`.
Aprende na semana 5. Só precisa do essencial.

**MQTT** — modelo publicador/assinante, broker, tópico. Conceito simples, 30
minutos de leitura.

**ESP32** — conectar ao Wi-Fi e publicar via MQTT. A biblioteca PubSubClient tem
exemplos prontos. 2 a 3 horas contando a frustração inicial com driver de porta
serial.

## 2.3 Do projeto

Leia o `GUIA_DE_DOMINIO.md` inteiro antes de escrever a primeira linha. As sete
seções da Parte 2 são o que você vai defender oralmente.

Leia o artigo de novo, com atenção especial às Seções 4.3.1 (quais arquivos eles
usaram), 4.3.2 (hiperparâmetros) e às Tabelas 3, 4 e 10.

---

# Parte 3 — Roteiro comprimido com portões de verificação

A regra continua: **não avance sem passar no portão da etapa atual.**

A diferença em relação ao plano original: com 4 semanas em vez de 8, as duas
trilhas andam **em paralelo**. A trilha de dados (PC) e a trilha de hardware (Pi)
não dependem uma da outra até a semana C. Enquanto as bases não chegam, você
adianta o Pi.

---

### Semana A (06 a 12/10) — Bases e replicação

**Hoje, antes de tudo:** pedir acesso às bases (BoT-IoT "10 best features",
ToN-IoT Windows 7/10, CICIoT2023). Procure as páginas oficiais, confira o link,
preencha os formulários. A aprovação pode levar dias, por isso é a primeira coisa.

Enquanto espera a liberação, adiante a trilha de hardware:
- Instalar Python e o `requirements-pc.txt` no PC.
- No Pi: instalar Mosquitto (`sudo apt install -y mosquitto mosquitto-clients`) e
  habilitar no boot.
- Programar o ESP32 para conectar ao roteador isolado e publicar a cada poucos
  segundos.

Quando as bases chegarem:
- `python src/prepare.py --dataset botiot --input data/raw/botiot/ --inspect`
- Conferir os nomes reais contra o `COLMAP_BOTIOT`. Ajustar se divergir.
- Rodar `replicate.py` no BoT-IoT e no ToN-IoT Windows.

**Portão A:** a tabela com F1 ponderado e macro lado a lado existe para o BoT-IoT,
e o ponderado fica perto de 0,99. Se vier muito abaixo, o pré-processamento está
errado: pare e investigue.

**Portão A (Pi):** `mosquitto_sub -h localhost -t '#' -v` mostra as mensagens do
ESP32 chegando.

---

### Semana B (13 a 19/10) — Modelo e captura bruta

No PC:
- Rodar `replicate.py --keep-identifiers` e comparar com a rodada anterior.
- CICIoT2023 (feito em 08/10): replicação com as features nativas da base,
  `replicate.py` sobre um arquivo do `MERGED_CSV`, com e sem a feature `IAT`.
  Opcional: repetir em 2 ou 3 outros arquivos para mostrar que o resultado não
  depende do arquivo escolhido.
- Rodar `prepare.py` e `train.py` com o BoT-IoT "All features". O CICIoT2023
  **não** entra como `--test-extra` (ver o quadro abaixo).
- Anotar as versões que o `train.py` imprime e copiar para o `requirements-pi.txt`.

No Pi:
- Instalar tshark.
- Capturar sem Docker e sem Python:
  `sudo tshark -i wlan0 -f "tcp port 1883" -w teste.pcap`
- Abrir o `.pcap` no Wireshark do PC e confirmar os pacotes MQTT.

**Portão B:** `models/rf_edge.joblib` existe, e o `teste.pcap` mostra tráfego MQTT
real do ESP32.

> **Por que o CICIoT2023 não entra na avaliação cruzada (decidido em 08/10):** a
> versão pública atual (`MERGED_CSV`, 40 colunas) descreve janelas de 10 a 100
> pacotes, não fluxos. Não tem duração (`flow_duration` não existe) nem separa
> bytes e pacotes por sentido, e `Tot size` é igual a `AVG` (tamanho médio do
> pacote). Só o protocolo e as flags teriam correspondência com o esquema
> canônico. Por isso ele entra na trilha A (replicação com as próprias
> features) e não na trilha B. Diga isso na apresentação.

---

### Semana C (20 a 26/10) — Inferência no Pi e janela benigna

- Copiar o modelo para o Pi. Rodar `python src/detect.py --model ... --pcap teste.pcap`.
- Conferir os fluxos: durações plausíveis, estado `CLOSED` ou `ESTABLISHED` nas
  sessões MQTT normais.
- `docker build` e `docker run` com `--net=host --cap-add=NET_RAW --cap-add=NET_ADMIN`.
- Coletar a janela benigna: `--phase benign`, 30 a 60 minutos.

**Portão C:** `results/live_flows.csv` com centenas de linhas `phase=benign` e a
coluna `latency_us` preenchida.

> **Ponto de decisão em 22/10:** se o `detect.py --pcap` ainda não funcionar,
> assuma o nível P1 da contingência e siga. Ver Parte 4.

---

### Semana D (27/10 a 02/11) — Ataque, análise e slides

- Do Ubuntu, na rede isolada, gerar varredura e inundação contra os seus próprios
  dispositivos, com o `detect.py` rodando em `--phase attack`.
- Cruzar `phase` com `pred`: F1, taxa de falso positivo, taxa de falso negativo.
- Consolidar latência, RAM e vazão.
- Montar gráficos e slides. Conferir gramática (vale 1,5 de 5,0).
- **Conferir cada referência abrindo o documento original.**
- Ensaiar com cronômetro: 5 a 9 minutos (tempo vale 1,5 de 5,0).
- Exportar em PDF e enviar pelo SIGAA **antes** de apresentar.

**Portão D:** matriz de confusão do tráfego real, números de custo do Pi, e o PDF
enviado.

Os dias 03 e 04/11 ficam como folga. Não planeje nada para eles.

---

# Parte 4 — Plano de contingência

Algo vai dar errado. Esta é a ordem de prioridade: se o tempo apertar, corte de
baixo para cima.

| Nível | Entrega | Sem isso |
|---|---|---|
| **P0** | Replicação + Random Forest nas duas bases, F1 ponderado vs macro | não há trabalho |
| **P1** | Modelo rodando no Pi sobre arquivo `.pcap`, com latência e RAM medidas | perde a validação em hardware |
| **P2** | Captura ao vivo do tráfego do ESP32 | perde o "tráfego real" do objetivo |
| **P3** | Janela de ataque rotulada por construção | perde a matriz de confusão real |
| **P4** | Replicação no CICIoT2023, base de 2023, com as features nativas (feita em 08/10) | perde a comparação com uma base recente |

Se em 22/10 o `detect.py --pcap` não estiver funcionando, **assuma o P1 e siga**. Medir no Pi
usando um `.pcap` gravado ainda é validação em hardware real, ainda produz
latência, memória e vazão, e ainda cumpre o essencial do objetivo declarado.
Explique a limitação na apresentação. É muito melhor que chegar em novembro com
uma captura ao vivo quebrada e nenhum número.

---

# Parte 5 — Erros que custam tempo

**Fonte fraca no Raspberry Pi.** Subtensão causa travamento aleatório e corrupção
de cartão. Se aparecer o ícone de raio ou `Under-voltage detected` no `dmesg`, é
isso. Muita hora perdida procurando bug de software.

**Raspberry Pi OS de 32 bits.** Você vai descobrir só na hora de instalar o
scikit-learn, na semana 5, e vai ter que refazer o cartão.

**Versão diferente de scikit-learn entre PC e Pi.** O `.joblib` pode carregar em
silêncio e dar previsões erradas. Trave as versões.

**Docker sem `--net=host`.** O container enxerga só a rede virtual interna e a
captura vem vazia, sem erro nenhum. Você fica procurando problema no PyShark.

**Cabo USB só de carga no ESP32.** A porta serial não aparece e parece defeito da
placa.

**Deixar identificadores nas features.** F1 de 0,999 que desaba na rede real.

**Treinar sem `class_weight` no BoT-IoT.** O modelo aprende a dizer "ataque"
sempre e marca todo o tráfego do seu ESP32 como malicioso.

**Amostrar sem estratificar.** Com 429 registros benignos em 3,3 milhões, uma
amostra aleatória simples pode não pegar nenhum.

---

# Parte 6 — Faça hoje

1. Pedir acesso às bases. Tudo da semana A depende disso.
2. Instalar Mosquitto no Pi.
3. Começar o programa do ESP32.

Os itens 2 e 3 não dependem das bases. Faça enquanto espera a liberação.
