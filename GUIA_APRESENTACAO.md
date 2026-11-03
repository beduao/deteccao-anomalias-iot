# Guia da apresentação (03/11/2026)

Tudo o que você precisa falar, entender e responder na apresentação de
resultados. Os números conferem com o deck publicado em 02/11
(https://claude.ai/artifact/111ATASkggREaNeymkATMM) e com o `STATUS.md`.

## Como usar este guia hoje

| Ordem | O quê | Tempo |
|---|---|---|
| 1 | Parte 1: a história em cinco frases. Decore. | 10 min |
| 2 | Parte 3: os conceitos, começando pelos marcados como **essencial** | 1 h 30 |
| 3 | Parte 2: a fala de cada slide, em voz alta, com o deck aberto | 40 min |
| 4 | Partes 4 a 6: números, perguntas e o que não dizer | 40 min |
| 5 | Dois ensaios com cronômetro (de 5 a 9 min) | 25 min |

Não decore a fala palavra por palavra: decore a **mensagem central** e os
**números** de cada slide e fale com as suas palavras. A banca percebe texto
decorado.

O `GUIA_DE_DOMINIO.md` foi escrito antes dos experimentos e tem partes
desatualizadas. A lista do que mudou está no fim deste guia.

---

# Parte 1 — A história em cinco frases

1. **O artigo** (Inuwa & Das, 2024) comparou cinco classificadores no Orange-3 e
   concluiu que a rede neural é a melhor, com F1 de 0,999.
2. **Replicando em Python**, mostrei que esse 0,999 é F1 *ponderado*, que quase
   não enxerga a classe benigna, e que no BoT-IoT ele só reaparece quando os
   *identificadores* (IP, número de sequência) ficam entre as features.
3. **O Random Forest**, que acrescentei, é o que melhor acerta a classe rara (a
   benigna), justamente a que importa num detector.
4. **No Raspberry Pi 3**, o custo cabe (58 ms por fluxo, 151 MB), mas no tráfego
   real o modelo marcou como ataque 100% do tráfego normal. Um teste de controle
   mostrou a causa: ele julga pelo formato do fluxo.
5. **A lição que amarra tudo:** número alto de laboratório pode esconder
   problemas. Mostrei três: na métrica, nas features e na generalização para a
   rede real.

Se der branco no meio da apresentação, volte à frase 5.

---

# Parte 2 — O que dizer em cada slide

Tempo total previsto: cerca de 8 min e 15 s. O limite é de 5 a 9 min. Se o ensaio
passar de 9 min, corte o slide 11.

## Slide 1 — Capa (20 s)

**Mensagem:** o título é o mesmo da primeira apresentação, porque o objetivo foi
seguido.

> Bom dia. Sou a Beatriz e vou apresentar os resultados do meu trabalho, uma
> extensão do artigo de Inuwa e Das, de 2024, sobre detecção de anomalias em
> redes IoT. Vou mostrar três coisas: a replicação do artigo em Python, o Random
> Forest que acrescentei aos cinco classificadores e o modelo rodando num
> Raspberry Pi 3.

## Slide 2 — O artigo-base (40 s)

**Mensagem:** o que o artigo fez e concluiu, sem erros de leitura.

> O artigo parte de um problema: métodos baseados em regras e assinaturas não
> acompanham a variedade dos ataques em redes IoT. Os autores compararam cinco
> classificadores (SVM, k-NN, árvore de decisão, regressão logística e rede
> neural) numa ferramenta visual, o Orange-3, em duas bases: o ToN-IoT, com dados
> de sistema do Windows, e o BoT-IoT, com tráfego de rede. A conclusão foi que a
> rede neural é a melhor, com F1 de 0,999 e o menor número de falsos positivos e
> negativos.

**Cuidado:** o artigo não fala em firewall. E não diga que o BoT-IoT é um
subconjunto do ToN-IoT: o artigo afirma isso, mas são bases distintas.

## Slide 3 — O objetivo proposto (30 s)

**Mensagem:** as três extensões prometidas foram cumpridas, e houve acréscimos.

> Na primeira etapa, propus três extensões. Primeiro, sair do Orange e programar
> em Python com scikit-learn, controlando os hiperparâmetros. Segundo, inserir o
> Random Forest, que o artigo não comparou com a rede neural. Terceiro, embarcar
> o modelo num Raspberry Pi, medindo memória e tempo de inferência. As três foram
> feitas. Além disso, acrescentei uma base de 2023, o CICIoT2023, e um teste de
> vazamento por identificadores.

**Cuidado:** não diga que o Random Forest é "inédito". O próprio artigo cita um
estudo com ele.

## Slide 4 — Método em duas trilhas (45 s)

**Mensagem:** por que há duas trilhas, e como os dados foram amostrados.

> O trabalho tem duas trilhas. Na trilha A, replico o artigo no PC: os cinco
> classificadores mais o Random Forest, com os hiperparâmetros da Seção 4.3.2,
> sem IP, porta e número de sequência, classificando o tipo de ataque, como o
> artigo faz. Cada experimento usa 300 mil linhas: as classes raras entram
> inteiras, e a divisão é 70% para treino e 30% para teste, estratificada. Na
> trilha B, treino um Random Forest com 11 features de fluxo que o próprio Pi
> consegue medir. O Pi é o broker MQTT, e um cliente MQTT no PC faz o papel do
> sensor, porque o ESP32 não foi reconhecido pela porta USB.

**Por que duas trilhas:** a versão do BoT-IoT que o artigo usou ("10 best
features") não tem duração, bytes nem pacotes por sentido, que é o que o Pi
consegue medir. A trilha B usa a versão "All features".

## Slide 5 — Replicação (50 s)

**Mensagem:** os dados são os mesmos do artigo; no ToN-IoT os números batem, no
BoT-IoT não.

> Aqui estão os nossos números ao lado dos do artigo, em F1 ponderado e
> multiclasse. Primeiro, confirmei que os dados são os mesmos: no ToN-IoT, as
> proporções de classe batem com a Tabela 5; no BoT-IoT, os totais da Tabela 10
> correspondem a 90% das nossas contagens. No ToN-IoT, quatro modelos ficam a
> menos de 0,006 do artigo. No BoT-IoT, SVM e rede neural ficam bem abaixo dos
> 0,999: 0,86 e 0,95. A regressão logística destoa nas duas bases. E a árvore
> falhou no Orange nessa base. O próximo slide mostra por que o BoT-IoT fica
> abaixo.

## Slide 6 — Achado principal: identificadores (45 s)

**Mensagem:** o 0,999 do artigo no BoT-IoT depende de identificadores. É um
indício, não uma prova.

> Este é o achado principal. No BoT-IoT, os 0,999 do artigo só reaparecem quando
> os identificadores ficam entre as features: endereço IP, número de sequência e
> ID do registro. O SVM vai de 0,86 para 0,999, e a rede neural, de 0,95 para
> 0,9998. Com identificadores, o modelo memoriza quem atacou, em vez de aprender
> como é o ataque: funciona no teste e falha em qualquer outra rede. Há uma
> segunda pista: a árvore do Orange falhou com "atributos com mais de 16 valores",
> e nessa base só IPs e portas passam disso. É um indício, não uma prova, porque o
> artigo não diz quais colunas usou.

**Frase obrigatória:** "os números do artigo se reproduzem quando os
identificadores são mantidos". **Nunca:** "o artigo usou identificadores".

## Slide 7 — Por que o F1 ponderado engana (40 s)

**Mensagem:** com 0,013% de benignos, o F1 ponderado fica perto de 1 em qualquer
modelo; o F1 da classe benigna é o que separa os modelos.

> Outro ponto é a métrica. No BoT-IoT, só 0,013% dos registros são benignos: 477
> em 3,67 milhões. Um modelo que diz "ataque" para tudo acerta 99,987%. O F1
> ponderado pesa cada classe pelo tamanho, então fica perto de 1 em qualquer
> modelo: aqui, entre 0,9996 e 0,9999. Já o F1 da classe benigna separa os
> modelos, de 0,87 a 0,96. Para um detector de intrusão, que existe para separar
> o normal do malicioso, essa é a métrica que importa. O eixo do gráfico começa
> em 0,80.

**Cuidado:** este gráfico é da rodada *binária* (benigno × ataque). Nela, a
árvore (0,9556) e o Random Forest (0,9547) estão praticamente empatados.

## Slide 8 — Random Forest (40 s)

**Mensagem:** o Random Forest se destaca na classe rara.

> O Random Forest se destaca justamente na classe rara. No BoT-IoT, ele empata
> com a árvore e o k-NN no F1 ponderado, 0,994, mas tem o melhor F1 da classe
> normal, 0,976. No CICIoT2023, tem o melhor F1 da classe benigna, 0,902. No
> ToN-IoT, a base é fácil demais e não separa os modelos. Escolhi o Random Forest
> por três motivos: os autores sugerem métodos de ensemble como trabalho futuro,
> a árvore do Orange falhou no BoT-IoT, e ele é leve para hardware limitado.

## Slide 9 — CICIoT2023 (45 s)

**Mensagem:** o método aplicado a uma base de 2023, e por que não deu para
treinar numa base e testar na outra.

> Acrescentei o CICIoT2023, uma base de 2023 com 34 classes: 33 tipos de ataque e
> o tráfego benigno. Ela é menos desequilibrada, com 2,3% de benignos, mas é mais
> difícil: o melhor F1 da classe benigna é 0,90, do Random Forest. Usei 1 dos 63
> arquivos, porque comparei quatro deles e são equivalentes. A ideia inicial era
> treinar no BoT-IoT e testar aqui, mas a versão pública descreve janelas de
> pacotes, não fluxos: não tem duração nem separa os dois sentidos. Então apliquei
> o método dentro da própria base.

## Slide 10 — Raspberry Pi (60 s)

**Mensagem:** o custo cabe na borda; o modelo não generaliza para a rede real.

> Aqui está a terceira promessa. O modelo do Pi tem 120 KB. Lendo uma captura de
> 30 minutos no próprio Pi 3, cada fluxo leva 58 ms para ser classificado; o
> processo usa no máximo 151 MB; e a vazão é de 17 fluxos por segundo, quando o
> sensor gera um a cada 5 segundos. Ou seja, o custo cabe. Mas, no tráfego real,
> todos os 350 fluxos benignos viraram alarme. Para achar a causa, fiz um teste
> de controle: mesmo sensor, mesmo intervalo, só que com a conexão aberta o tempo
> todo. Aí, os 19 trechos de operação normal passaram, e os 6 alarmes vieram de
> quedas da conexão. O modelo aprendeu que fluxo pequeno e curto é ataque, que é
> o formato do DoS no BoT-IoT. Conclusão: o F1 de 0,99 do laboratório não garante
> um detector útil na rede real.

**Não tenha medo deste slide.** O resultado negativo é a parte mais interessante
do trabalho, porque está explicado e testado. Fale com segurança.

## Slide 11 — O que a replicação revelou (40 s; corte se faltar tempo)

**Mensagem:** replicar revelou problemas no artigo. Tom sóbrio, sem crítica aos
autores.

> A replicação também revelou quatro pontos no artigo. A versão do ToN-IoT não é
> informada, mas as proporções da Tabela 5 batem com o arquivo
> Train_Test_Windows_10. As AUCs das Tabelas 3 e 4 estão fora do intervalo
> possível, que vai de 0 a 1. A regressão logística destoa, e a minha hipótese é
> que o Orange não normalizou as features. E o ToN-IoT é citado com uma referência
> trocada. Mostro isso como evidência de que replicar tem valor, não como crítica
> aos autores.

## Slide 12 — Conclusões e limitações (40 s)

**Mensagem:** volte ao objetivo e diga as limitações sem receio.

> Para concluir: o F1 ponderado de 0,999 esconde a classe benigna, e o F1 dessa
> classe é o que separa os modelos. No BoT-IoT, os números do artigo dependem de
> identificadores. O Random Forest se destaca na classe rara. E, no Pi 3, o custo
> cabe, mas o alarme falso depende de como o sensor se conecta. As limitações:
> uma única divisão treino/teste, amostras com as classes raras inteiras, poucos
> benignos no BoT-IoT e um único sensor, simulado no PC. As três extensões
> prometidas foram feitas. Obrigada.

## Slide 13 — Referências

Não leia. Deixe na tela enquanto responde às perguntas.

---

# Parte 3 — Conceitos que você precisa dominar

Para cada um: o que é, como explicar em voz alta e onde ele aparece no seu
trabalho. Os marcados como **essencial** quase certamente vão aparecer nas
perguntas.

## 3.1 Matriz de confusão, precisão, revocação e F1 (essencial)

A **matriz de confusão** cruza a classe real com a classe prevista. Com "ataque"
como classe positiva:

| | Previsto ataque | Previsto benigno |
|---|---|---|
| **Real ataque** | verdadeiro positivo (VP) | falso negativo (FN): ataque que passou |
| **Real benigno** | falso positivo (FP): alarme falso | verdadeiro negativo (VN) |

- **Precisão** = VP / (VP + FP): dos alarmes, quantos eram ataque mesmo.
  Precisão baixa = muito alarme falso.
- **Revocação** (*recall*) = VP / (VP + FN): dos ataques reais, quantos foram
  pegos. Revocação baixa = ataque passando despercebido.
- **F1** = 2 × precisão × revocação / (precisão + revocação). É a média
  *harmônica*, que pune o desequilíbrio: com precisão 1 e revocação 0, a média
  comum seria 0,5, mas o F1 é 0.
- **Taxa de falso positivo** = FP / (FP + VN): da parte benigna, quanto virou
  alarme.

**No seu trabalho:**
- No Pi, só havia tráfego benigno: 350 FP e 0 VN, ou seja, taxa de falso positivo
  de 100%. Sem tráfego de ataque, não dá para medir a revocação no Pi.
- O "F1 da classe benigna" trata a classe benigna como a positiva. É a mesma
  fórmula, com outra classe no papel de positiva.

## 3.2 F1 ponderado × F1 macro (essencial: é o slide 7)

Com várias classes, calcula-se um F1 para cada classe e depois se faz a média:

- **Ponderado:** cada classe pesa pela sua quantidade de exemplos.
- **Macro:** todas as classes pesam igual.

Exemplo para explicar na hora: 99,987% de ataques com F1 = 1,0 e 0,013% de
benignos com F1 = 0,5.
- Ponderado ≈ 0,99994, porque a classe benigna quase não pesa.
- Macro = (1,0 + 0,5) / 2 = 0,75.

**Frase para a banca:** "o F1 ponderado responde 'quão bem o modelo acerta o
tráfego típico'; num detector, o que interessa é se ele separa o normal do
ataque, e isso o F1 da classe benigna ou o macro mostram".

Um caso do seu trabalho: no teste do modelo do Pi no PC, o Random Forest não
marcou nenhum dos 143 benignos como ataque, mas deixou passar uns 280 ataques
(0,31%) como benignos. A precisão da classe benigna caiu para 0,34 (143 de 423)
e o F1 macro, para 0,75, mesmo com o F1 ponderado perto de 1.

## 3.3 Desbalanceamento, amostragem e `class_weight` (essencial)

**Desbalanceamento:** uma classe é muito mais rara que as outras. No BoT-IoT, são
477 benignos em 3,67 milhões (0,013%). Um modelo preguiçoso aprende a dizer
"ataque" sempre e acerta 99,987%.

**O que você fez:**
- **Amostragem:** cada experimento usa 300 mil linhas. As classes raras entram
  inteiras, e os ataques são sorteados para completar. Sem isso, uma amostra
  aleatória teria uns 39 benignos.
  - **Custo:** a amostra tem 0,159% de benignos, contra 0,013% na base. Isso está
    declarado no slide 12.
- **Divisão estratificada:** a separação 70/30 mantém a mesma proporção de cada
  classe no treino e no teste.
- **`class_weight="balanced_subsample"`** no Random Forest do Pi: cada erro na
  classe rara custa mais no treino, na proporção inversa da frequência da classe,
  calculada na amostra de cada árvore.

## 3.4 Treino, teste e validação cruzada

- **Treino e teste:** o modelo aprende com uma parte (70%) e é avaliado na outra
  (30%), que ele nunca viu. Avaliar nos dados de treino mede memorização.
- **Validação cruzada (k-fold):** divide os dados em k partes, treina em k−1 e
  testa na que sobrou, k vezes, e tira a média. Ela mostra se o resultado varia
  com a divisão.
- **No seu trabalho:** foi uma divisão por base. É uma limitação declarada, e a
  validação cruzada é o primeiro "o que faria com mais tempo".

## 3.5 Vazamento de dados por identificadores (essencial: é o slide 6)

**Vazamento** (*data leakage*): uma feature carrega a resposta por um motivo que
não existe fora do conjunto de dados.

**No BoT-IoT:** no testbed, os atacantes eram máquinas fixas. Com o IP de origem
como feature, o modelo aprende "este IP é ataque". Ele acerta no teste, que vem
do mesmo testbed, e falha em qualquer outra rede. O mesmo vale para o número de
sequência (`seq`, praticamente um carimbo de tempo) e o ID do registro
(`pkSeqID`). Nenhum deles descreve **comportamento**; todos descrevem
**identidade**.

**O seu experimento:** rodar com e sem identificadores (`--keep-identifiers`).
- Com eles, todos os modelos sobem, e o Random Forest chega a 1,0000.
- Na rodada com identificadores ficaram `pkSeqID`, `seq` e `saddr`. Já `daddr`,
  `sport` e `dport` são texto com valores demais e o script os descarta.

## 3.6 Os seis classificadores em uma frase cada (essencial)

| Modelo | Como decide | Hiperparâmetros na trilha A |
|---|---|---|
| **k-NN** | olha os 5 exemplos de treino mais parecidos (distância euclidiana) e fica com a classe da maioria | k = 5 |
| **Árvore de decisão** | uma sequência de perguntas sim/não sobre as features ("pkts_per_sec > 80?") até chegar a uma folha com a classe | profundidade máx. 100 |
| **SVM (linear)** | traça a fronteira que separa as classes com a maior margem possível | C = 1 |
| **Regressão logística** | um modelo linear que transforma uma soma ponderada das features numa probabilidade (função sigmoide), com regularização L2 | C = 1 |
| **Rede neural (MLP)** | camadas de neurônios com ativação não linear (ReLU), ajustadas por gradiente (Adam) | 1 camada de 100 neurônios |
| **Random Forest** | muitas árvores, cada uma treinada numa amostra sorteada dos dados e com features sorteadas; a resposta é a média dos votos | 100 árvores, profundidade 20 |

Os hiperparâmetros seguem a Seção 4.3.2 do artigo quando ele os informa. Se
perguntarem um que você não sabe, diga que estão no `replicate.py`.

## 3.7 Random Forest em detalhe (essencial)

- **Por que muitas árvores:** uma árvore sozinha decora o treino. Cada árvore da
  floresta vê dados e features sorteados, então elas erram em lugares diferentes,
  e a média dos votos cancela os erros.
- **Probabilidade e limiar:** o Random Forest devolve uma probabilidade de
  ataque (a média das árvores). Acima de 0,5, é alarme. No Pi, os fluxos normais
  da conexão persistente ficaram entre 0,38 e 0,45: passaram, mas perto do
  limite.
- **Importância das features:** o modelo diz quanto cada feature pesa nas
  decisões. No modelo do Pi, as mais importantes são `src_bytes` (0,26),
  `src_pkts` (0,16), `pkts_per_sec` (0,15) e `duration` (0,12): volume e
  duração, que é o que o teste no Pi confirmou.
- **Os dois Random Forests do trabalho:**
  - trilha A, para comparar com o artigo: 100 árvores, profundidade 20;
  - trilha B, para o Pi: 60 árvores, profundidade 18, folhas de pelo menos 4
    exemplos, com `class_weight`. Ficou com 120 KB.
- **Por que ele, e não aprendizado profundo:** dados tabulares, hardware de 1 GB,
  inferência feita só de comparações e a lacuna da árvore no artigo.

## 3.8 Normalização e codificação

- **Normalização** (`StandardScaler`): transforma cada feature para média 0 e
  desvio-padrão 1. Modelos baseados em distância ou gradiente (k-NN, SVM,
  regressão logística, rede neural) precisam disso; árvores, não.
- **Codificação one-hot:** transforma uma feature de texto em colunas de 0 e 1.
  Por exemplo, `proto` vira `proto_tcp`, `proto_udp` e `proto_icmp`.
- **A hipótese da regressão logística:** o artigo tem cerca de 0,775 nas duas
  bases, e você tem de 0,89 a 0,9998. Uma regressão logística sem normalização
  sofre com features em escalas muito diferentes. Hipótese: o Orange não
  normalizou. **Não foi testada**, diga isso.

## 3.9 AUC (para o slide 11)

A **curva ROC** mostra a taxa de verdadeiros positivos contra a de falsos
positivos para todos os limiares possíveis. A **AUC** é a área sob essa curva:
- 0,5 = acerto ao acaso;
- 1,0 = perfeito.

Como é a área de um quadrado de lado 1, ela **sempre** fica entre 0 e 1. O artigo
traz −8,114 (Tabela 3) e 1,055 (Tabela 4): valores impossíveis, provavelmente
erro de digitação ou de exportação.

## 3.10 Pacote, fluxo e as 11 features (essencial para o slide 10)

- **Pacote:** a unidade que trafega na rede.
- **Fluxo:** a conversa entre dois pontos, identificada pela **5-tupla**: IP de
  origem, porta de origem, IP de destino, porta de destino e protocolo.
- O modelo foi treinado com fluxos (o BoT-IoT foi gerado com a ferramenta Argus),
  mas o Pi captura pacotes. Por isso existe o `flowmeter.py`: ele junta os
  pacotes em fluxos e calcula as mesmas 11 features do treino.

As 11 features:

| Feature | O que é |
|---|---|
| `duration` | duração do fluxo, em segundos |
| `src_bytes`, `dst_bytes` | bytes enviados por cada lado |
| `src_pkts`, `dst_pkts` | pacotes enviados por cada lado |
| `bytes_per_pkt_src`, `bytes_per_pkt_dst` | tamanho médio do pacote de cada lado |
| `pkts_per_sec` | pacotes por segundo |
| `bytes_ratio` | fração dos bytes que saiu da origem |
| `proto` | tcp, udp, icmp ou outro |
| `state` | estado da conexão (abaixo) |

**Estado TCP**, que o `flowmeter.py` deduz das flags:
- Abrir uma conexão: o cliente manda SYN, o servidor responde SYN-ACK, o cliente
  confirma com ACK.
- Fechar: cada lado manda FIN.
- RST derruba a conexão na hora.

| Estado | Quando |
|---|---|
| `CLOSED` | os dois lados mandaram FIN: a conexão abriu e fechou direito |
| `ESTABLISHED` | houve SYN-ACK, mas ainda não fechou |
| `ATTEMPT` | só SYN, sem resposta |
| `RESET` | apareceu um RST |
| `OTHER` | nada disso (por exemplo, o trecho do meio de uma conexão longa) |

**Quando o fluxo termina:**
- depois de 15 s sem pacotes (`IDLE_TIMEOUT`);
- ou, numa conexão longa, a cada 120 s (`ACTIVE_TIMEOUT`). Por isso a conexão
  persistente virou trechos de uns 2 minutos.

**Uma armadilha que você corrigiu e pode contar:** a versão nova do tshark
escreve as flags TCP como "True"/"False", e o código esperava "1"/"0". Na primeira
rodada, todo fluxo saiu como `OTHER`. Conferir os estados antes de aceitar o
resultado pegou o erro.

## 3.11 MQTT e Mosquitto

- **MQTT** é um protocolo leve de publicação e assinatura, muito usado em IoT. O
  sensor **publica** uma mensagem num **tópico** (`lab/pc/telemetria`); quem
  **assina** o tópico recebe.
- O **broker** recebe e distribui as mensagens. Você usou o **Mosquitto** no Pi,
  na porta 1883.
- **QoS 0:** a mensagem vai uma vez, sem confirmação do broker.
- **Keepalive (60 s):** se o broker passa 1,5 × 60 = 90 s sem ouvir o cliente,
  encerra a conexão.
- **Por que o broker fica no Pi:** todo o tráfego MQTT termina nele, então a
  captura enxerga tudo sem precisar de espelhamento de porta.
- **Os dois padrões de conexão que você testou:**
  - **abre e fecha a cada envio:** cada publicação vira um fluxo de uns 26 ms, com
    11 pacotes e uns 700 bytes. É como funcionam sensores a bateria, que acordam,
    publicam e dormem;
  - **persistente:** uma conexão aberta o tempo todo, com 1 envio a cada 5 s.

## 3.12 IA na borda: o que cada medida diz (essencial para o slide 10)

**Treinar** é caro e acontece uma vez; **inferir** é barato e acontece o tempo
todo. Por isso se treina no PC e se infere no Pi.

| Medida | Valor | O que responde |
|---|---|---|
| Tamanho do modelo | 120 KB | cabe em dispositivos pequenos? |
| Latência média | 57,9 ms por fluxo | dá para classificar em tempo real? |
| Latência p95 | 58,4 ms | e o pior caso? 95% dos fluxos levaram até isso |
| Vazão teórica | 17 fluxos/s (= 1 ÷ 0,058 s) | aguenta o volume da rede? |
| Pico de memória | 151 MB | cabe no 1 GB do Pi 3? |

Detalhes que mostram domínio:
- **A latência mede só a chamada ao modelo,** não a captura.
- **Os 151 MB são do processo Python inteiro** (Python, pandas, scikit-learn,
  PyShark), não só do modelo.
- **A p95 quase igual à média** mostra um tempo estável, sem picos.
- **Usar 1 núcleo em vez de 4 baixou a latência** de uns 100 ms para 58 ms. Com
  um fluxo por vez, dividir 60 árvores entre os núcleos custa mais do que
  economiza.
- **Boa parte dos 58 ms deve ser custo fixo de cada chamada** (montar a tabela e
  pré-processar), não das árvores. Classificar vários fluxos de uma vez deve
  aumentar a vazão, mas isso você não mediu.

## 3.13 Mudança de domínio: por que o modelo falhou na rede real (essencial)

**Mudança de domínio** (*dataset shift*): o modelo é treinado num ambiente e
usado noutro, onde os dados têm outra distribuição. O desempenho medido no
laboratório deixa de valer.

**O seu caso:**
- **Treino:** testbed do BoT-IoT, com 477 benignos (só 47 deles TCP) e milhões de
  fluxos de DoS e DDoS, que são pequenos e curtos.
- **Uso:** uma rede Wi-Fi doméstica com MQTT.
- **O que o modelo aprendeu:** "fluxo pequeno e curto = ataque". A sessão MQTT que
  abre e fecha tem exatamente esse formato: P(ataque) = 0,98.

**Como se corrigiria** (trabalho futuro):
- retreinar com tráfego benigno da própria rede onde o modelo vai rodar;
- usar bases com tráfego benigno mais variado;
- ajustar o limiar de decisão;
- ou treinar um modelo só com tráfego normal, para detectar o que foge dele
  (detecção de anomalia de uma classe).

## 3.14 Teste de controle e análise de sensibilidade (essencial para o slide 10)

- **Teste de controle:** muda uma única condição e mantém o resto igual, para
  isolar a causa. Você manteve sensor, broker, intervalo e mensagens, e mudou só
  o padrão de conexão.

  | Padrão de conexão | Fluxos | Alarmes falsos |
  |---|---|---|
  | abre e fecha | 350 | 350 (100%) |
  | persistente | 25 | 6 (24%) |
  | persistente, só os trechos normais | 19 | 0 |

- **Análise de sensibilidade:** muda uma feature por vez nos fluxos reais e vê o
  que acontece com a previsão (`src/sensibilidade.py`). Nos 350 fluxos de abrir
  e fechar, **nenhuma mudança isolada desfaz o alarme**:
  - TCP → UDP: a probabilidade cai de 0,98 para 0,78;
  - estado → `ESTABLISHED`: cai para 0,75;
  - bytes × 10: cai para 0,69.

  O alarme vem da **combinação** de pouco volume e pouca duração.
- **Conferência:** o PC recalculou as previsões dos fluxos do Pi e deu a mesma
  resposta em 100% dos casos. Os dois rodam as mesmas versões do scikit-learn,
  numpy e pandas.
- **As quedas de conexão:** aconteceram nas duas capturas, mesmo com o publicador
  rodando sem janela. O log do Mosquitto mostra que o broker não encerrou
  nenhuma: elas se perderam na rede. O Wi-Fi do Pi está com economia de energia
  ligada, uma causa provável, **não comprovada**.

## 3.15 As bases e o Orange-3

| Base | Origem | O que tem | O que você usou |
|---|---|---|---|
| **BoT-IoT** | UNSW Canberra (Koroniotis et al., 2019) | tráfego de rede de um testbed com dispositivos IoT simulados; DDoS, DoS, reconhecimento, roubo de dados; fluxos gerados pelo Argus | recorte de 5% (3,67 milhões de fluxos); "10 best features" na trilha A, "All features" na trilha B |
| **ToN-IoT** | UNSW Canberra (Moustafa, 2021; Alsaedi et al., 2020) | telemetria de IoT e de sistemas operacionais, logs e rede | `Train_Test_Windows_10`: 21.104 registros, 8 classes (normal, DDoS, password, XSS, injection, DoS, scanning, MITM) |
| **CICIoT2023** | Canadian Institute for Cybersecurity (Neto et al., 2023) | 33 ataques numa rede de dispositivos IoT reais | 1 dos 63 arquivos `Merged` (712 mil linhas, 34 classes, 2,3% benignos) |

**Orange-3:** ferramenta visual de mineração de dados, em que se monta o fluxo
arrastando blocos. É fácil de usar, mas esconde decisões de pré-processamento
(quais colunas entram, se normaliza), e isso dificulta replicar o trabalho.

---

# Parte 4 — Números para ter na ponta da língua

| Assunto | Número |
|---|---|
| Benignos no BoT-IoT | 477 em 3,67 milhões = 0,013% |
| Benignos no BoT-IoT que são TCP | 47 |
| Benignos na amostra | 0,159% |
| Benignos no CICIoT2023 | 2,3% |
| Amostra por experimento | 300 mil linhas, divisão 70/30 estratificada |
| F1 ponderado do artigo | 0,999 (rede neural) |
| BoT-IoT sem identificadores | SVM 0,8617; rede neural 0,9527 |
| BoT-IoT com identificadores | SVM 0,9992; rede neural 0,9998; Random Forest 1,0000 |
| F1 ponderado binário no BoT-IoT | 0,9996 a 0,9999 |
| F1 benigno binário no BoT-IoT | 0,87 a 0,96 |
| Random Forest, BoT-IoT, classe normal | 0,976 (multiclasse) |
| Random Forest, CICIoT2023, benigno | 0,902 (segundo: rede neural, 0,874) |
| Regressão logística | ~0,775 no artigo; 0,89 a 0,9998 aqui |
| Modelo do Pi | 60 árvores, 120 KB |
| Latência no Pi 3 | média de 57,9 ms; p95 de 58,4 ms |
| Memória no Pi 3 | 151 MB |
| Vazão | 17 fluxos/s |
| Alarmes falsos, abre e fecha | 350 em 350 |
| Alarmes falsos, persistente | 6 em 25; 0 nos 19 trechos normais |
| P(ataque) dos trechos normais | 0,38 a 0,45 (limiar 0,5) |
| Sessão MQTT de abre e fecha | ~26 ms, 11 pacotes, ~700 bytes |

---

# Parte 5 — Perguntas prováveis e como responder

**Então o seu modelo não serve para nada?**
Ele serve para mostrar o problema. No PC, com dados do mesmo testbed, ele não
marcou nenhum benigno como ataque; na rede real, marcou todos. Essa distância é
exatamente o que a avaliação só em CSV esconde. Para usar de verdade, ele teria
que ser retreinado com tráfego benigno da rede onde vai rodar.

**Por que ele marcou todo o tráfego normal como ataque?**
Porque ele julga pelo formato do fluxo. No BoT-IoT, quase todo fluxo pequeno e
curto é DoS ou DDoS, e a sessão MQTT que abre e fecha tem esse formato: 26 ms e
11 pacotes. Testei isso de duas formas. Mudando só o padrão de conexão, os
trechos normais passaram. E mudando uma feature por vez nos fluxos reais,
nenhuma mudança isolada desfez o alarme.

**Não era só por ser TCP? A base tem só 47 benignos TCP.**
Essa era a minha hipótese inicial, mas o teste mostrou que não é o principal:
trocando só TCP por UDP, a probabilidade de ataque cai de 0,98 para 0,78 e
continua alarme. O volume e a duração pesam mais.

**Você testou se o modelo detecta ataques reais?**
Não. Gerar ataques só é seguro numa rede isolada, e eu estava na rede de casa.
Além disso, enquanto o tráfego normal vira alarme, uma matriz de confusão só
mostraria "tudo é ataque" e não diria nada sobre a detecção. Esse é o próximo
passo, numa rede isolada.

**Por que não usou o ESP32?**
Ele não foi reconhecido pela USB do PC com nenhum dos dois cabos, nem numa porta
que funciona: provavelmente cabo só de carga ou defeito na USB da placa. Escrevi
um cliente MQTT no PC que faz o mesmo que o programa do ESP32: conecta, publica e
desconecta a cada 5 s. Para o modelo, o que importa é o padrão do fluxo, e ele é
o mesmo.

**58 ms não é muito para um modelo tão leve?**
Para o volume do sensor, sobra: ele gera um fluxo a cada 5 s e o Pi classifica 17
por segundo. Boa parte do tempo deve ser custo fixo de cada chamada do
scikit-learn, não das árvores. Usar um núcleo em vez de quatro já reduziu de uns
100 para 58 ms, e classificar vários fluxos de uma vez deve ajudar mais.

**Os 151 MB são do modelo?**
Não. São do processo Python inteiro, com pandas, scikit-learn e PyShark. O modelo
tem 120 KB.

**Por que os seus números do BoT-IoT são menores que os do artigo?**
Porque eu tirei os identificadores. Com eles, os 0,999 reaparecem. O artigo não
diz quais colunas usou, então não posso afirmar que ele usou identificadores:
digo que os números se reproduzem quando eles são mantidos.

**Qual métrica você recomendaria?**
O F1 da classe benigna, ou o F1 macro, junto com a taxa de falso positivo. São as
que mostram se o detector separa o normal do ataque.

**O Random Forest é o melhor na classe benigna em todas as rodadas?**
No multiclasse do BoT-IoT (0,976) e no CICIoT2023 (0,902), sim. Na rodada binária
do BoT-IoT, a árvore (0,9556) e o Random Forest (0,9547) empatam na prática. E no
ToN-IoT todos ficam perto de 1.

**O Random Forest é uma contribuição inédita?**
Não. O artigo cita um estudo com ele. A contribuição é compará-lo com os cinco
nas mesmas bases e no mesmo pipeline, e levá-lo ao hardware.

**Por que não fez validação cruzada?**
Tempo de processamento: são seis modelos, várias bases e rodadas com e sem
identificadores. É a primeira coisa que eu faria com mais tempo. Os resultados
vêm de uma única divisão, e isso está nas limitações.

**Manter os benignos inteiros na amostra não distorce o resultado?**
Muda a proporção (0,159% na amostra, contra 0,013% na base), e por isso eu
declaro. Sem isso, a amostra teria uns 39 benignos, e o teste, uns 12: o F1 da
classe benigna seria só ruído.

**Por que a regressão logística deu tão diferente?**
A diferença aparece nas duas bases, então parece configuração, não dados. A
minha hipótese é que o Orange não normalizou as features. Não testei.

**Por que não treinou no BoT-IoT e testou no CICIoT2023?**
A versão pública do CICIoT2023 descreve janelas de 10 a 100 pacotes, não fluxos:
não tem duração nem separa os dois sentidos. Só protocolo e flags seriam
comparáveis. Então apliquei o método dentro da própria base.

**O que o flowmeter faz?**
Junta os pacotes capturados em fluxos pela 5-tupla, soma bytes e pacotes de cada
lado, deduz o estado da conexão pelas flags TCP e emite o fluxo depois de 15 s
sem pacotes, ou a cada 120 s numa conexão longa. A saída tem as mesmas 11
features do treino.

**Como você garante que o Pi rodou o mesmo modelo do PC?**
O Pi usa as mesmas versões de scikit-learn, numpy e pandas do treino. E recalculei
no PC as previsões dos fluxos do Pi: deram iguais em 100% dos casos.

**Por que as conexões caíram no teste persistente?**
O log do Mosquitto mostra que o broker não encerrou nenhuma conexão: elas se
perderam na rede. O Wi-Fi do Pi está com economia de energia ligada, uma causa
conhecida desse tipo de falha. É provável, mas não comprovei. Para o resultado,
isso mostra que cada queda vira alarme.

**25 fluxos não é pouco?**
É pouco para estimar uma taxa com precisão, e está nas limitações. Mas o
contraste é grande: 350 em 350 contra 0 em 19 trechos normais.

**O que faria com mais tempo?**
Validação cruzada; testar a hipótese da regressão logística; retreinar o modelo
do Pi com tráfego benigno da própria rede; capturar com o ESP32 real e mais
dispositivos; e uma janela de ataque numa rede isolada, para medir a detecção.

**Se não souber responder:**
"Não testei isso, mas a forma de testar seria…", ou "Não sei com certeza; o que
os meus dados mostram é…". Nunca invente um número.

---

# Parte 6 — O que não dizer

| Não diga | Diga |
|---|---|
| "O artigo usou identificadores." | "Os números do artigo se reproduzem quando os identificadores são mantidos." |
| "O BoT-IoT é um subconjunto do ToN-IoT." | São bases distintas, do mesmo grupo (UNSW Canberra). |
| "O Random Forest é inédito." | "Comparei o Random Forest com os cinco nas mesmas bases." |
| "O modelo detecta ataques no tráfego real." | O tráfego real testado era só benigno. |
| "O artigo fala em firewall." | "Métodos baseados em regras e assinaturas." |
| "O modelo ocupa 151 MB." | O modelo tem 120 KB; os 151 MB são do processo inteiro. |
| "O modelo tem 100 árvores." | O do Pi tem 60; o da trilha A, 100. |
| "Testei no ESP32." | "Um cliente MQTT no PC fez o papel do sensor." |
| "O Wi-Fi derrubou as conexões." | "O broker não encerrou as conexões; a causa provável é o Wi-Fi." |
| "O artigo errou." | "Os valores de AUC estão fora do intervalo possível." |

---

# Parte 7 — Antes de sair de casa

- [ ] Referência do CICIoT2023 conferida em https://doi.org/10.3390/s23135941 e
      completada no slide 13.
- [ ] As outras quatro referências abertas e conferidas (autores, título,
      periódico, volume, páginas, DOI).
- [ ] Revisão de gramática em todos os slides.
- [ ] Dois ensaios com cronômetro, entre 5 e 9 min.
- [ ] PDF exportado e enviado pelo SIGAA **antes** de apresentar.
- [ ] Uma cópia do PDF num pen drive ou no celular.
- [ ] Este guia aberto no celular, para revisar a Parte 4 antes de entrar.

---

# O que está desatualizado no `GUIA_DE_DOMINIO.md`

Esse guia foi escrito antes dos experimentos. Ao estudar por ele, corrija:

- **"você usa 100 árvores":** o modelo do Pi tem 60. O da trilha A tem 100.
- **Docker, ESP32 e janela de ataque:** não foram feitos. O sensor foi um
  cliente MQTT no PC, e não houve janela de ataque.
- **A resposta "Como você sabe que o tráfego capturado era realmente ataque?":**
  não se aplica. Todo o tráfego real foi benigno.
- **A resposta "Por que o F1 caiu tanto em relação ao artigo?":** os slides
  comparam ponderado com ponderado. A queda no BoT-IoT vem da retirada dos
  identificadores.
- **"nenhum trabalho comparou nessas bases junto com esses cinco":** não afirme
  isso. Diga só o que você fez.
- **"latência por fluxo (µs)" e "5.000 fluxos por segundo":** os números reais
  são 58 ms e 17 fluxos/s.
