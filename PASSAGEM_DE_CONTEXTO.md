# Passagem de contexto: Raspberry Pi, teste de controle e preparação (01 a 03/11/2026)

Escrito em 03/11/2026 no notebook onde rodaram os testes com o Raspberry Pi.
É para o chat principal do Claude Code no outro PC: resume tudo o que foi
feito, medido e descoberto aqui, para que ele atualize o material e ajude a
preparar a apresentação.

---

## 0. Leia primeiro

- **A apresentação é hoje, 03/11/2026.** A prioridade é a apresentação, não o
  repositório.
- **Já está na conta, e você vê daí:** o deck,
  https://claude.ai/artifact/111ATASkggREaNeymkATMM, versão 18. Leia com o
  Artifact (`action: "read"`) antes de editar qualquer coisa.
- **No GitHub, no branch `resultados-pi` (03/11):** as mudanças de código e os
  documentos novos (seção 6). O `main` continua no commit `ce8770c`, de 16/10.
  Para trazer, no outro PC: `git fetch origin` e `git switch resultados-pi`.
- **Só existe no Pi:** os três `.pcap` e os resultados da segunda captura
  persistente:
  - `results/pcap_flows_persistente2.csv`;
  - `results/resumo_pcap_persistente2.txt`.
- **Os testes no Pi terminaram.** Não proponha refazê-los antes da apresentação:
  os números abaixo são os finais e já estão nos slides.

**Combinados com a Beatriz:**
- Não editar slides sem o ok dela. O ok de 02/11 valeu só para os slides 3, 4,
  10 e 12.
- Não fazer commit nem push sem ela pedir.
- A senha do Wi-Fi fica só em `esp32/publicador_mqtt/segredos.h`, que está no
  `.gitignore`. Nunca no chat, no repositório ou nos slides.
- Nenhum tráfego de ataque na rede de casa. Não houve janela de ataque.

---

## 1. A história em cinco linhas

1. O Random Forest de 60 árvores (120 KB) rodou no Raspberry Pi 3 sobre tráfego
   MQTT real e benigno. O custo cabe: 58 ms por fluxo e 151 MB de pico para o
   processo inteiro.
2. Com o sensor abrindo e fechando a conexão a cada envio, **os 350 fluxos
   benignos viraram alarme falso** (100%).
3. **Teste de controle:** mesmo sensor, broker, intervalo e mensagens; mudou só o
   padrão de conexão, que ficou persistente. Resultado: 6 alarmes em 25 fluxos.
   **Os 19 trechos de operação normal passaram todos.** Os 6 alarmes vieram de
   quedas da conexão e de um trecho cortado no fim da gravação.
4. **Causa:** o modelo julga pelo formato do fluxo. Ele aprendeu, no BoT-IoT, que
   fluxo pequeno é ataque (o formato do DoS e do DDoS), e a sessão MQTT curta tem
   esse formato. Não é o TCP: trocar TCP por UDP não desfaz nenhum alarme.
5. **Conclusão:** o F1 de 0,99 do laboratório não garante um detector útil na
   rede real. Mesmo na conexão persistente, os fluxos passam por pouco: P(ataque)
   de 0,38 a 0,45, com o corte em 0,5.

---

## 2. Linha do tempo

**01/11**
- Pi 3 preparado: Mosquitto, tshark, ambiente virtual com as versões do
  `requirements-pi.txt`, e o modelo carregando sem aviso de versão.
- Não houve roteador isolado. Tudo rodou na rede de casa, com o filtro
  `tcp port 1883`. O Pi é o `192.168.18.123` e o PC, o `192.168.18.7`.
- O ESP32 não foi reconhecido pelo USB, com nenhum dos dois cabos. Plano B: o
  `src/publicador_mqtt.py` no PC faz o papel do sensor.
- Duas correções de código (seção 5): as flags TCP do tshark e o `--n-jobs`.

**02/11**
- **Captura principal:** `teste.pcap`, 30 min, conexão que abre e fecha →
  350/350 alarmes.
- Uma sonda com fluxos montados à mão indicou que a causa era o formato do
  fluxo, não o TCP.
- **Teste de controle, 1ª captura persistente:** 2 alarmes em 11 fluxos. A
  conexão caiu, e por isso a captura foi repetida.
- **2ª captura persistente:** 4 alarmes em 14 fluxos.
- **Análise de sensibilidade** no PC, sobre os fluxos reais
  (`src/sensibilidade.py`).
- Os slides 3, 4, 10 e 12 foram atualizados e publicados (versão 18).
- Criado o `GUIA_APRESENTACAO.md`, o guia de estudo e de fala.

**03/11:** estudo dos conceitos e este documento.

---

## 3. Resultados

### 3.1 Custo no Pi 3 (`teste.pcap`, 30 min, 350 fluxos)

| Medida | Valor |
|---|---|
| Modelo | Random Forest, 60 árvores, `max_depth` 18, `min_samples_leaf` 4, `balanced_subsample`, 120 KB |
| Pacotes processados | 3.856 |
| Fluxos classificados | 350 |
| Latência média por fluxo | **57,9 ms** (57.929,7 µs) |
| Latência p95 | **58,4 ms** (58.375,3 µs) |
| Vazão teórica | **17 fluxos/s** |
| Pico de RAM | **151,3 MB** (o processo Python inteiro, não o modelo) |
| Carga do modelo | 7,2 s |
| Tempo total | 172,1 s |

**Como ler esses números:**
- A latência mede só a chamada ao modelo, um fluxo por vez, com `--n-jobs 1`.
  Com `n_jobs=-1`, que é como o modelo foi salvo, passou de 100 ms por fluxo:
  dividir 60 árvores entre os núcleos custa mais do que economiza.
- 17 fluxos/s sobram para um sensor que gera 1 fluxo a cada 5 s.

### 3.2 Alarmes falsos (todo o tráfego era benigno, rótulo por construção)

| Padrão de conexão | Captura | Pacotes | Fluxos | Alarmes falsos | Latência média / p95 | RAM |
|---|---|---|---|---|---|---|
| Abre e fecha a cada envio | `teste.pcap` | 3.856 | 350 | **350 (100%)**, todos com P = 0,983 | 57,9 / 58,4 ms | 151,3 MB |
| Persistente, 1ª captura | `teste_persistente.pcap` | 649 | 11 | 2 | 55,5 / 62,4 ms | 150,4 MB |
| Persistente, 2ª captura | `teste_persistente2.pcap` | 733 | 14 | 4 | 54,3 / 61,1 ms | 150,7 MB |
| **Persistente, as duas** | | | **25** | **6 (24%)** | | |
| **Persistente, só trechos normais** | | | **19** | **0** | | |

**Os 6 alarmes da conexão persistente, um a um:**
- **1ª captura:**
  - um trecho com RESET (123 s, P = 0,701);
  - outro trecho com RESET (135 s, P = 0,619).
- **2ª captura:**
  - um trecho com RESET (P = 0,551);
  - um trecho só com pacotes do broker sem resposta, estado `OTHER` (P = 1,000);
  - um SYN sem resposta, estado `ATTEMPT` (P = 0,971);
  - um trecho `ESTABLISHED` de 15 s, cortado no fim da gravação (P = 0,834).

**Os 19 trechos normais** tiveram P(ataque) entre 0,38 e 0,45. A conexão
persistente vira trechos de cerca de 2 min, porque o `ACTIVE_TIMEOUT` do
`flowmeter.py` é de 120 s.

**A sessão MQTT típica do abre e fecha** (mediana dos 350 fluxos):
- 0,026 s de duração;
- 6 pacotes do PC e 5 do broker;
- 431 bytes do PC e 286 do broker;
- estado `CLOSED`.

A sequência é SYN, SYN-ACK e ACK; CONNECT e CONNACK; PUBLISH; DISCONNECT; e FIN
dos dois lados.

### 3.3 Análise de sensibilidade (`src/sensibilidade.py`, fluxos reais)

Muda uma feature por vez, em todos os fluxos, e recalcula a previsão com as
mesmas versões de bibliotecas do Pi. **O PC reproduziu as previsões do Pi em
100% dos fluxos.**

**Abre e fecha.** O `pcap_flows.csv` tem cada fluxo duas vezes (ver seção 5),
mas as proporções não mudam.

| Variante | Alarmes | P(ataque) mediana |
|---|---|---|
| original | 350 de 350 | 0,983 |
| protocolo `udp` | 350 de 350 | 0,783 |
| estado `ESTABLISHED` | 350 de 350 | 0,750 |
| duração × 10 | 350 de 350 | 0,983 |
| duração × 100 | 350 de 350 | 0,983 |
| bytes × 10 | 350 de 350 | 0,685 |
| pacotes e bytes × 10 | 350 de 350 | 0,717 |

**Persistente, 1ª captura (11 fluxos):**

| Variante | Alarmes | P(ataque) mediana |
|---|---|---|
| original | 2 de 11 | 0,435 |
| protocolo `udp` | 2 de 11 | 0,419 |
| estado `ESTABLISHED` | 1 de 11 | 0,335 |
| duração × 10 | 2 de 11 | 0,402 |
| duração × 100 | 3 de 11 | 0,485 |
| bytes × 10 | 0 de 11 | 0,051 |
| pacotes e bytes × 10 | 0 de 11 | 0,269 |

**Leitura:**
- Nenhuma mudança isolada desfaz o alarme do abre e fecha.
- O que mais pesa é o volume (bytes e pacotes).
- A duração sozinha não muda nada.
- A conexão persistente passa porque muda tudo junto: mais tempo, muito mais
  pacotes e mais bytes.

---

## 4. Descobertas e correções de interpretação

1. **A causa dos alarmes é o formato do fluxo, não o TCP.**
   - A frase antiga do slide 10, "só 47 dos 477 benignos do treino são TCP",
     explicava mal o resultado e foi trocada.
   - O número 47 continua certo como fato da base e aparece nas limitações
     (slide 12).
2. **Um detalhe para corrigir se a Beatriz quiser:** as notas do slide 10 dizem
   "o que pesa é o tamanho e a duração do fluxo". As seções 3.13 e 3.14 do
   `GUIA_APRESENTACAO.md` dizem "pequeno e curto" e "combinação de pouco volume e
   pouca duração".
   - **Os dados:** a duração sozinha não move a previsão (× 100 continua em
     0,983); o volume sozinho reduz, mas não desfaz.
   - **A forma mais exata:** "o que pesa é o fluxo ter poucos pacotes e poucos
     bytes; nenhuma mudança isolada desfaz o alarme".
   - O texto visível do slide ("fluxo pequeno e curto é ataque, o formato do
     DoS") continua correto, porque descreve o DoS da base. Mudar o slide exige o
     ok dela.
3. **O teste de controle isola a causa.**
   - **O que mudou:** só o padrão de conexão.
   - **O resultado:** de 350/350 para 0/19 nos trechos normais.
   - **O que ele não controla:** as quedas de conexão e o fim da gravação, que
     geraram os 6 alarmes.
   - **Tamanho:** a amostra é pequena, 25 fluxos.
4. **O modelo é frágil mesmo quando acerta.** Os trechos normais saem com
   P(ataque) de 0,38 a 0,45, perto do corte de 0,5.
5. **As quedas de conexão não vieram do sensor nem do broker.**
   - **Na 2ª captura:** o publicador registrou 4 resets (WinError 10054) e 1
     timeout ao conectar, mesmo rodando sem janela. Logo, não foi o QuickEdit do
     PowerShell.
   - **No broker:** o log do Mosquitto mostra "Client pc-sensor already
     connected, closing old connection" a cada reconexão. O broker nunca
     derrubou o cliente; a conexão antiga se perdeu na rede.
   - **Causa provável, não comprovada:** o Wi-Fi do Pi está com
     `Power Management:on`. Para testar, rodar `sudo iwconfig wlan0 power off`
     antes de capturar.
   - **Implicação:** numa implantação real, cada queda de conexão vira alarme.
6. **Artefatos do `flowmeter.py`, de efeito pequeno:**
   - **Trechos que continuam uma conexão** depois dos 120 s não têm SYN e saem
     com estado `OTHER`. Às vezes saem também com o sentido invertido (origem no
     broker), porque o primeiro pacote do trecho foi do broker. Forçar
     `ESTABLISHED` muda pouco (mediana de 0,435 para 0,335).
   - **UDP:** um fluxo UDP com resposta sai `CLOSED` no `flowmeter.py`, mas o
     Argus marca `CON`, que o `schema.py` traduz para `ESTABLISHED`. Fica como
     limitação; não afeta o MQTT.

---

## 5. Problemas técnicos encontrados e como foram resolvidos

| Problema | Solução |
|---|---|
| O tshark do Pi escreve as flags TCP como `True`/`False`, e o `flowmeter.py` só reconhecia `"1"`. Nenhum SYN ou FIN era visto, e todo fluxo TCP saía `OTHER`. | Função `_flag()` no `flowmeter.py` (01/11). |
| O modelo foi salvo com `n_jobs=-1`, e assim a latência passava de 100 ms por fluxo. | Opção `--n-jobs` no `detect.py`, com padrão 1. |
| Rodado com `sudo`, o tshark dava "Permission denied" ao gravar. | Capturar sem `sudo`, com o usuário no grupo `wireshark`. |
| O ESP32 não foi reconhecido pelo USB. | O `src/publicador_mqtt.py` no PC faz o papel do sensor, com o mesmo padrão do sketch do ESP32. |
| O scikit-learn do PC era o 1.5.0 e o modelo foi salvo com o 1.8.0. | Um ambiente virtual com as versões do `requirements-pi.txt`. As previsões do PC batem com as do Pi. |
| O `results/resumo_pcap_4nucleos.txt` tem nome enganoso: é uma segunda rodada do `teste.pcap` com `n_jobs=1`. Deu 59,4 ms de média, p95 de 60,1 ms e 151,4 MB, perto da primeira. Ela também acrescentou mais 350 linhas ao `pcap_flows.csv`, que ficou com 700. | Não existe resultado com 4 núcleos. O arquivo ficou fora do commit e só existe no notebook. Tirar as linhas duplicadas do CSV depois da apresentação; as proporções não mudam. |

---

## 6. Mudanças no repositório (branch `resultados-pi`, 03/11)

| Arquivo | Situação | O que é |
|---|---|---|
| `src/flowmeter.py` | modificado | `_flag()` para as flags TCP (seção 5). |
| `src/detect.py` | modificado | `--n-jobs` (padrão 1), aplicado ao classificador dentro do pipeline. |
| `.gitignore` | modificado | ignora `esp32/**/segredos.h`. |
| `src/publicador_mqtt.py` | novo | Sensor simulado (detalhes abaixo). |
| `src/sensibilidade.py` | novo | Análise de sensibilidade (detalhes abaixo). |
| `esp32/publicador_mqtt/publicador_mqtt.ino` | novo | Sketch do ESP32: conecta, publica em `lab/esp32/telemetria` e desconecta. Não foi gravado na placa. |
| `esp32/publicador_mqtt/segredos.h` | novo, **ignorado pelo git** | Nome e senha do Wi-Fi. Não copiar nem mostrar. |
| `PROXIMOS_PASSOS.md` | novo | Plano de 01 a 03/11: Passos 1 a 9 do Pi, com os comandos e o resultado do teste de controle. |
| `GUIA_APRESENTACAO.md` | novo | Guia de estudo e de fala (detalhes abaixo). |
| `results/resumo_pcap.txt` | novo | Resumo da captura de abre e fecha. |
| `results/resumo_pcap_persistente.txt` | novo | Resumo da 1ª captura persistente. |
| `results/resumo_pcap_4nucleos.txt` | **fora do commit**, só no notebook | Enganoso (seção 5). |
| `results/pcap_flows.csv` e `results/pcap_flows_persistente.csv` | **ignorados pelo git** (`results/*.csv`) | Fluxos com as previsões. |
| `PASSAGEM_DE_CONTEXTO.md` | novo | Este documento. |

**`src/publicador_mqtt.py`**
- Usa só a biblioteca padrão: monta os pacotes MQTT 3.1.1 à mão (CONNECT,
  PUBLISH com QoS 0, DISCONNECT).
- **Modo padrão:** conecta, publica e desconecta a cada 5 s, no tópico
  `lab/pc/telemetria`.
- **Com `--persistente`:** mantém uma única conexão, com keepalive de
  `max(60, 2 × intervalo + 1)` segundos. Depois de um erro, reconecta na leitura
  seguinte, como o PubSubClient.

**`src/sensibilidade.py`**
- **Uso:** `py src/sensibilidade.py results/pcap_flows.csv [outro.csv]`.
- Recalcula as features derivadas com o `schema.add_derived` e confere se o PC
  concorda com a coluna `pred` do Pi.
- Aplica as variantes da seção 3.3.
- Precisa das versões do `requirements-pi.txt`.

**`GUIA_APRESENTACAO.md`**
- A história em cinco frases.
- A fala de cada slide, com tempo.
- Os conceitos 3.1 a 3.15.
- Os números para decorar.
- As perguntas prováveis, com resposta.
- O que não dizer.
- O checklist do dia.
- O que está desatualizado no `GUIA_DE_DOMINIO.md`.

**Como chegou ao outro PC:** tudo isso está no branch `resultados-pi`, em dois
commits. O `main` não foi mexido; juntar o branch ao `main` só se a Beatriz
pedir. Ficaram de fora do git:
- o `segredos.h` e os CSVs, porque estão no `.gitignore`;
- o `resumo_pcap_4nucleos.txt`, pelo nome enganoso.

Se precisar dos CSVs, copie à mão.

---

## 7. O deck (versão 18, já na conta)

| Slide | Arquivo | O que mudou em 02/11 |
|---|---|---|
| 3 | `objetivo.html` | A validação em hardware está marcada como "Concluído em 02/11". |
| 4 | `metodo.html` | "Pi 3 como broker MQTT; cliente MQTT no PC simulando o sensor". As notas explicam que o ESP32 não foi reconhecido pelo USB. |
| 10 | `raspberry.html` | Reescrito (detalhes abaixo). |
| 12 | `conclusao.html` | Conclusões e limitações novas (detalhes abaixo). |

**Slide 10**
- **Título:** "Raspberry Pi: custo e alarmes no tráfego real".
- **Quatro cartões:** 120 KB, 58 ms (p95 de 58 ms), 151 MB e 17 fluxos/s.
- **Tabela:** "Abre e fecha a cada envio", 350 fluxos, 350 alarmes (100%);
  "Persistente (2 capturas)", 25 fluxos, 6 alarmes (24%).
- **Quadro "O modelo julga pelo formato do fluxo":** fluxo pequeno e curto é o
  formato do DoS no BoT-IoT; a sessão de abre e fecha tem 26 ms e 11 pacotes;
  trocar TCP por UDP não desfaz nenhum alarme; na persistente, os 19 trechos
  normais passaram.
- **Notas:** cerca de 60 s.
- Não há mais espaço para foto do Pi.

**Slide 12**
- **Nova conclusão:** "No Pi 3, o custo cabe (58 ms por fluxo, 151 MB), mas o
  alarme falso depende de como o sensor se conecta."
- **Nova limitação:** "Um único sensor, simulado por um cliente MQTT no PC, e
  poucos fluxos no teste persistente."
- **Notas:** trabalho futuro inclui retreinar o modelo do Pi com tráfego benigno
  da própria rede.

**Ainda em aberto no deck:**
- **Slide 13:** a referência do CICIoT2023 ainda tem
  "[periódico, volume e DOI: conferir antes de apresentar]". Deve ser
  *Sensors*, v. 23, n. 13, art. 5941, 2023, DOI 10.3390/s23135941, mas a Beatriz
  precisa abrir https://doi.org/10.3390/s23135941 e confirmar antes. Uma
  referência errada pode custar até 6 pontos.
- **Revisão de gramática** de todos os slides.
- **Ensaio:** as notas somam cerca de 8 min 15 s, para um limite de 5 a 9 min.
  Se passar de 9 min, cortar o slide 11.

---

## 8. O que está desatualizado no repositório

- **`STATUS.md`:** parado em 16/10. Faltam todos os resultados do Pi (seções 3
  e 4).
- **`GUIA_DE_DOMINIO.md`:** escrito antes dos experimentos.
  - "100 árvores": o modelo do Pi tem 60; o da trilha A, 100.
  - Docker, ESP32 e janela de ataque: não foram feitos.
  - "Como você sabe que o tráfego capturado era realmente ataque?": não se
    aplica, porque todo o tráfego real foi benigno.
  - "Por que o F1 caiu tanto em relação ao artigo?": a queda no BoT-IoT vem da
    retirada dos identificadores.
  - "Nenhum trabalho comparou...": não afirmar.
  - "µs por fluxo" e "5.000 fluxos/s": os números reais são 58 ms e 17
    fluxos/s.
- **Datas:** documentos que dizem "perto de 05/11" estão errados; a
  apresentação é 03/11.
- **`PROXIMOS_PASSOS.md`:** a tabela "O que falta nos slides" está quase toda
  cumprida. Sobram o slide 13 e a foto, que foi abandonada.

---

## 9. O que falta

**Hoje, antes de apresentar, nesta ordem:**
1. Confirmar a referência do CICIoT2023 e completar o slide 13 (com o ok da
   Beatriz).
2. Abrir e conferir as outras quatro referências: autores, título, periódico,
   volume, páginas e DOI.
3. Revisar a gramática dos slides.
4. Fazer dois ensaios com cronômetro, entre 5 e 9 min.
5. Exportar o PDF e enviar pelo SIGAA **antes** de apresentar. Levar uma cópia
   no celular ou num pen drive.
6. Estudar, nesta prioridade (as seções são do `GUIA_APRESENTACAO.md`):
   1. precisão, revocação e F1; F1 ponderado × macro (3.1 e 3.2);
   2. desbalanceamento e vazamento por identificadores (3.3 e 3.5);
   3. como o Random Forest funciona, e os outros cinco classificadores (3.6 e
      3.7);
   4. pacote × fluxo, as 11 features e os estados TCP (3.10);
   5. mudança de domínio, teste de controle e análise de sensibilidade (3.13 e
      3.14).

   Depois, a Parte 4 (números) e a Parte 5 (perguntas prováveis).

**Depois da apresentação:**
- Juntar o branch `resultados-pi` ao `main`, se a Beatriz pedir.
- Atualizar o `STATUS.md` e corrigir o `GUIA_DE_DOMINIO.md`.
- Tirar as linhas duplicadas do `pcap_flows.csv`.
- Trazer do Pi os arquivos da 2ª captura persistente.
- Limpar o Pi (seção 10).
- **Opcionais:**
  - repetir a captura persistente com `sudo iwconfig wlan0 power off`;
  - retreinar o modelo do Pi com tráfego benigno da própria rede;
  - validação cruzada;
  - testar a hipótese da regressão logística (normalização no Orange-3);
  - gravar o ESP32 quando houver um cabo de dados.

---

## 10. Estado do Pi

- O projeto está em `~/iot` e o ambiente virtual em `~/iot-venv`.
- **O Mosquitto ficou ligado na rede de casa**, com
  `/etc/mosquitto/conf.d/lab.conf` (`listener 1883` e `allow_anonymous true`).
  Isso só era aceitável durante o teste. Para desfazer, no Pi:

  ```bash
  sudo rm /etc/mosquitto/conf.d/lab.conf
  sudo systemctl restart mosquitto
  ```

  Ou, para desligar de vez:

  ```bash
  sudo systemctl disable --now mosquitto
  ```
