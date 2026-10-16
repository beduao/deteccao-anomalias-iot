# Guia de domínio do projeto

Documento de estudo. Não é para apresentar — é para você entender a ponto de
responder qualquer pergunta sem consultar slide.

---

# Parte 1 — A história em uma página

Dispositivos IoT são muitos, baratos e fracos. Uma lâmpada inteligente tem menos
poder computacional que um celular de 2010, mas está conectada à internet 24 horas
por dia e raramente recebe atualização. Isso faz deles alvo preferencial: a botnet
Mirai derrubou boa parte da internet em 2016 usando câmeras e roteadores
domésticos comprometidos.

Detectar ataque em rede IoT é, no fundo, um problema de classificação. Você observa
uma conversa de rede e decide: normal ou malicioso. Machine learning resolve isso
bem, desde que você tenha dados rotulados.

**O que o artigo fez.** Inuwa e Das pegaram duas bases públicas rotuladas, jogaram
em cinco algoritmos clássicos dentro do Orange-3 (uma ferramenta visual, sem
programação) e compararam. A rede neural venceu, com F1 de 0,999.

**A lacuna.** Tudo aconteceu num PC, dentro de uma interface gráfica, lendo arquivos
CSV estáticos. Nenhum dispositivo foi ligado. Nenhum pacote real trafegou. E nada
foi medido sobre o custo de rodar aquilo: quanto de memória, quanto de latência,
se caberia num hardware barato. Os próprios autores admitem isso na conclusão,
quando listam como trabalho futuro "criar um protótipo funcional" e "conduzir um
teste piloto num ambiente IoT real".

**O que você faz.** Duas coisas. Acrescenta um sexto algoritmo que eles não
compararam, o Random Forest. E tira o modelo do CSV, embarca num Raspberry Pi 3 e
mede o que acontece quando ele encontra tráfego de verdade, gerado por um ESP32
que você mesmo configurou.

Em uma frase: **você converte um estudo de comparação de algoritmos numa prova de
conceito de engenharia.**

---

# Parte 2 — Os sete conceitos que você precisa dominar

Se você entender esta seção, responde qualquer pergunta da banca.

## 2.1 Pacote e fluxo: a distinção que sustenta o projeto

Este é o conceito central. Se você só puder decorar um, decore este.

Um **pacote** é a unidade que trafega no cabo. Tem cabeçalho (de onde vem, para
onde vai, qual protocolo) e conteúdo. Uma requisição HTTP simples pode gerar
dezenas de pacotes.

Um **fluxo** é a conversa inteira. Todos os pacotes trocados entre o mesmo par de
endereços e portas, no mesmo protocolo, dentro de uma janela de tempo. O fluxo é
identificado pela chamada *5-tupla*: IP de origem, porta de origem, IP de destino,
porta de destino, protocolo.

> Analogia: pacotes são palavras, fluxos são frases. O modelo foi treinado para
> classificar frases. O PyShark te entrega palavras soltas.

**Por que isso importa.** As bases de dados (ToN-IoT, BoT-IoT) não contêm pacotes.
Elas contêm fluxos, porque foram geradas por ferramentas de agregação: o Zeek no
caso do ToN-IoT, o Argus no caso do BoT-IoT. Cada linha do CSV é uma conversa
inteira já resumida em números: durou tanto, trocou tantos bytes, tantos pacotes.

Quando você captura ao vivo com PyShark, recebe pacotes individuais. Se alimentar
o modelo com eles, está entregando palavras a um classificador de frases. O
resultado é ruído.

**A solução é o `flowmeter.py`.** Ele mantém um dicionário de conversas em
andamento. Cada pacote que chega é atribuído à sua conversa (ou abre uma nova).
Quando a conversa fica quieta por 15 segundos, ou passa de 120 segundos de vida,
ela é considerada encerrada e vira uma linha com as mesmas colunas do CSV de
treino.

Essa camada é a sua contribuição de engenharia mais original. A maioria dos
trabalhos de graduação que tentam embarcar um IDS treinado em CSV falha exatamente
aqui, sem perceber.

## 2.2 As onze features e o que cada uma significa

O modelo não vê a rede. Ele vê onze números e categorias. Você precisa saber o que
cada um representa fisicamente.

**Cinco features brutas**, lidas diretamente:

| Feature | O que é |
|---|---|
| `duration` | segundos entre o primeiro e o último pacote do fluxo |
| `src_bytes` | total de bytes que a origem enviou |
| `dst_bytes` | total de bytes que o destino enviou |
| `src_pkts` | quantidade de pacotes da origem |
| `dst_pkts` | quantidade de pacotes do destino |

**Quatro features derivadas**, calculadas a partir das brutas. Estas carregam a
assinatura dos ataques:

| Feature | Fórmula | O que revela |
|---|---|---|
| `bytes_per_pkt_src` | src_bytes ÷ src_pkts | tamanho médio do pacote. Varredura usa pacotes minúsculos, só cabeçalho, sem conteúdo |
| `bytes_per_pkt_dst` | dst_bytes ÷ dst_pkts | idem, do lado do destino |
| `pkts_per_sec` | (src_pkts + dst_pkts) ÷ duration | taxa. Inundação DDoS tem taxa altíssima |
| `bytes_ratio` | src_bytes ÷ (src_bytes + dst_bytes) | direcionalidade. Perto de 1,0 significa que a origem fala e ninguém responde — exatamente o que acontece numa varredura |

Repare que as derivadas não acrescentam informação nova em teoria: são combinações
das brutas. Mas elas facilitam muito a vida do modelo, porque expressam
diretamente o padrão que distingue ataque de tráfego normal. Um modelo linear, em
particular, não conseguiria formar uma razão sozinho.

**Duas features categóricas:**

- `proto`: tcp, udp, icmp ou other
- `state`: o estado da conexão, explicado a seguir

## 2.3 O mapeamento de estado: tradução semântica, não sintática

Zeek e Argus descrevem o estado de uma conexão com vocabulários diferentes e
incompatíveis. O Zeek usa códigos como `S0`, `SF`, `REJ`, `RSTO`. O Argus usa
`INT`, `CON`, `FIN`, `RST`, `REQ`.

Você não pode simplesmente concatenar os dois. Precisa traduzir ambos para um
vocabulário comum de cinco classes:

| Classe canônica | Significa | Zeek | Argus |
|---|---|---|---|
| `ESTABLISHED` | conexão aberta e ativa | S1, S2, S3 | CON, ACC |
| `CLOSED` | abriu e fechou normalmente | SF | FIN, CLO |
| `ATTEMPT` | tentou abrir, ninguém respondeu | S0, SH, SHR | INT, REQ |
| `RESET` | recusada ou abortada | REJ, RSTO, RSTR | RST |
| `OTHER` | resto | OTH | demais |

**Por que `ATTEMPT` é a classe mais importante.** Uma varredura de portas funciona
mandando um pacote SYN para cada porta e vendo quem responde. Nas portas fechadas,
ninguém responde. Milhares de fluxos com um único pacote, sem resposta, duração
quase zero. É a assinatura mais limpa de reconhecimento que existe.

E no `flowmeter.py` você reproduz essa mesma semântica a partir dos flags TCP
observados ao vivo: viu SYN sem SYN-ACK, é `ATTEMPT`. Viu SYN e SYN-ACK, é
`ESTABLISHED`. Viu FIN nos dois sentidos, é `CLOSED`. Viu RST, é `RESET`.

**Isso fecha o triângulo**: Zeek, Argus e captura ao vivo produzindo o mesmo
vocabulário. Se te perguntarem qual é a contribuição técnica do trabalho, é esta.

## 2.4 Desbalanceamento e por que acurácia mente

Suponha 10.000 fluxos, dos quais 3 são ataque. Um modelo que responda "normal"
para tudo acerta 9.997 de 10.000. Acurácia de 99,97%. E é completamente inútil,
porque não detectou nada.

No BoT-IoT como usado no artigo, o problema é o inverso e ainda mais extremo:
**429 registros normais contra 3.301.671 no total** (Tabela 10). Dizer "ataque"
sempre dá 99,987%.

As métricas que importam:

- **Precisão** = dos que marquei como ataque, quantos eram mesmo. Precisão baixa
  significa muito alarme falso.
- **Recall** (revocação) = dos ataques reais, quantos eu peguei. Recall baixo
  significa ataque passando despercebido.
- **F1** = média harmônica das duas. Harmônica, não aritmética, porque pune
  desequilíbrio: se a precisão é 1,0 e o recall é 0,0, a média aritmética seria
  0,5, mas o F1 é 0.

E agora o ponto decisivo, **como se calcula o F1 quando há várias classes**:

- **F1 ponderado** (*weighted*): média dos F1 de cada classe, ponderada pela
  quantidade de exemplos de cada uma. Com 429 registros normais contra milhões de
  ataque, a classe normal contribui com 0,013% do resultado. Ela desaparece.
- **F1 macro**: média simples dos F1 de cada classe. A classe normal vale tanto
  quanto a classe DDoS, mesmo tendo mil vezes menos exemplos.

O artigo reporta o ponderado (o Orange chama de "average over classes"). Por isso
0,999. Seu `replicate.py` reporta os dois lado a lado. **A distância entre eles é o
seu resultado principal.**

Isso não é uma pegadinha nem má fé dos autores. É uma armadilha metodológica
conhecida, e apontá-la com números próprios é contribuição científica legítima.

## 2.5 Vazamento de dados

Vazamento (*data leakage*) acontece quando uma feature carrega, sem querer, a
resposta.

Exemplo concreto nesta área: os arquivos do BoT-IoT trazem as colunas `saddr` e
`daddr`, os endereços IP. No testbed, o atacante era sempre a mesma máquina. Se
você deixar o IP como feature, o modelo aprende "o endereço 192.168.100.150 é
ataque". Acerta 100% no teste, porque o conjunto de teste veio do mesmo testbed. E
acerta 0% na sua rede, onde esse endereço não existe.

O mesmo vale para porta de origem, endereço MAC, timestamp e número de sequência.
Nenhum deles descreve *comportamento*; todos descrevem *identidade*.

Por isso o `schema.py` exclui identificadores por princípio, e o `replicate.py` tem
a flag `--keep-identifiers`: rodando com e sem, você mede quanto do desempenho
relatado vem de memorizar endereço.

O artigo não informa quais colunas foram descartadas no widget Select Columns. Isso
torna o resultado não reprodutível nesse ponto, e é uma observação justa a fazer.

## 2.6 Edge AI: por que treinar num lugar e inferir noutro

Treinar um modelo é caro e acontece uma vez. Usar o modelo (inferência) é barato e
acontece o tempo todo. Essa assimetria é o que torna a IA de borda viável.

Seu Raspberry Pi 3 tem 1 GB de RAM e um processador de 2016. Treinar um Random
Forest sobre milhões de linhas ali levaria horas ou simplesmente não caberia na
memória. Mas classificar um único fluxo é percorrer algumas dezenas de árvores
fazendo comparações numéricas. Isso é trivial.

As alternativas seriam:

- **Tudo na nuvem**: manda o tráfego para um servidor classificar. Custa banda,
  adiciona latência, e expõe dados da rede a terceiros.
- **Tudo na borda**: impossível treinar num Pi 3.
- **Híbrido** (o seu): treina onde tem recurso, infere onde tem o dado. É o padrão
  da indústria.

**O que você mede no Pi, e que o artigo não tem:**

| Métrica | Por que importa |
|---|---|
| latência por fluxo (µs) | dá para classificar em tempo real? |
| latência p95 | o pior caso é aceitável, ou trava? |
| pico de RAM (MB) | cabe em 1 GB junto com o sistema? |
| tamanho do modelo (KB) | cabe em dispositivos ainda menores? |
| vazão (fluxos/s) | aguenta o volume de uma rede real? |

A vazão é a mais eloquente. Se o Pi classifica 5.000 fluxos por segundo e sua rede
abre 50 por segundo, sobra folga de duas ordens de grandeza — e você pode afirmar,
com número, que a arquitetura é viável.

## 2.7 Por que Random Forest

Uma **árvore de decisão** é uma sequência de perguntas do tipo "pkts_per_sec é
maior que 80?". Cada resposta leva a outra pergunta, até uma folha que diz a
classe. É interpretável e rápida, mas decora o conjunto de treino com facilidade.

Um **Random Forest** treina muitas árvores (você usa 100), cada uma sobre uma
amostra aleatória dos dados e um subconjunto aleatório das features. A resposta
final é o voto da maioria. A aleatoriedade descorrelaciona os erros das árvores
individuais, e a votação os cancela.

Contra o MLP (a rede neural que venceu no artigo):

| | MLP | Random Forest |
|---|---|---|
| operação na inferência | multiplicação de matrizes | comparações numéricas |
| precisa normalizar features? | sim, obrigatoriamente | não |
| interpretável? | não | sim, via importância das features |
| sensível a desbalanceamento? | muito | menos, e aceita `class_weight` |

**A justificativa mais forte, que você descobriu lendo o artigo:** na Tabela 3, a
árvore do Orange falhou por completo no BoT-IoT, com o erro *"Exhaustive
binarization does not handle attributes with more than 16 values"*. A linha inteira
está preenchida com `error`. Ou seja, a comparação naquela base teve quatro
modelos, não cinco, e a família de árvores ficou sem representante nenhum.

Seu Random Forest não é um sexto algoritmo arbitrário. Ele **repara uma falha
documentada no trabalho original**. E a falha era da ferramenta, não do algoritmo:
o scikit-learn não tem essa limitação de binarização.

---

# Parte 3 — A arquitetura, peça por peça

## 3.1 As duas trilhas e por que elas existem

Você descobriu, lendo a Seção 4.3.1, que os autores usaram os arquivos **ToN-IoT
Windows 7 e Windows 10** — telemetria de sistema operacional, com contadores de
processo, memória e registro. Isso é dado de *host*, não de rede.

Não existe tradução possível entre "tempo de processador do processo X" e um
pacote MQTT. Então essa parte do artigo não pode alimentar o Raspberry Pi.

Daí a separação:

**Trilha A — replicação** (`replicate.py`). Roda os cinco classificadores do artigo
mais o Random Forest, sobre as features nativas de cada base, incluindo a ToN-IoT
Windows. Objetivo: reproduzir a comparação, ver se os números batem, e expor a
diferença entre F1 ponderado e macro.

**Trilha B — borda** (`prepare.py` → `train.py` → `detect.py`). Só bases de rede,
sob o esquema canônico. Treina no BoT-IoT, embarca no Pi, classifica tráfego vivo.

As duas trilhas respondem ao objetivo que você declarou. A trilha A entrega o novo
classificador comparado; a trilha B entrega a validação em hardware. Apresentar a
separação como decisão metodológica consciente é muito melhor que escondê-la.

## 3.2 Os arquivos e o que cada um faz

```
schema.py      Define o contrato: as 11 features e os mapeamentos Zeek/Argus.
               Tudo mais depende dele. É o arquivo mais importante do projeto.

tableio.py     Lê e grava tabelas sem exigir pyarrow, que é problemático de
               instalar no Pi. Detalhe de engenharia, não de pesquisa.

prepare.py     Pega o CSV bruto de uma base e o projeta no esquema canônico.
               Descarta identificadores, normaliza protocolo e estado, calcula
               as derivadas.

train.py       [PC] Treina os 6 modelos sobre o esquema canônico, faz avaliação
               cruzada entre bases, e exporta o Random Forest em .joblib.

replicate.py   [PC] Trilha A. Replicação fiel com os hiperparâmetros declarados
               na Seção 4.3.2 do artigo. Reporta F1 ponderado, macro e da classe
               benigna.

flowmeter.py   [Pi] Agrega pacotes em fluxos. A peça que falta na literatura.

detect.py      [Pi] Carrega o modelo, roda o flowmeter, classifica, e mede
               latência, memória e vazão.
```

## 3.3 O caminho do dado, do começo ao fim

**No PC, uma vez:**

```
CSV bruto do BoT-IoT
   ↓  prepare.py: mapeia colunas, descarta IP/porta/MAC/tempo,
   ↓              traduz estado Argus → canônico, calcula derivadas
tabela canônica (11 colunas + rótulo)
   ↓  train.py: divide 70/30, treina 6 modelos, compara
modelo rf_edge.joblib (dezenas de KB)
```

**No Raspberry Pi, continuamente:**

```
ESP32 publica MQTT → broker Mosquitto rodando no próprio Pi
   ↓
PyShark captura pacotes na interface do Pi
   ↓  flowmeter.py: agrupa por 5-tupla, acumula bytes e pacotes,
   ↓                observa flags TCP, expira por timeout
fluxo completo → 11 features, as mesmas do treino
   ↓  detect.py: model.predict()
0 (benigno) ou 1 (ataque) + confiança + latência medida
   ↓
linha no live_flows.csv
```

O ponto a fixar: **as 11 colunas que saem do flowmeter são idênticas, em nome,
ordem e semântica, às que entraram no treino.** É isso que faz o sistema funcionar.

## 3.4 A topologia física e por que o broker fica no Pi

Numa rede comutada, o switch entrega a cada porta apenas os quadros destinados
àquele dispositivo. Se o ESP32 conversa com um broker externo, o Pi nunca vê esse
tráfego, por mais que você ative modo promíscuo.

Colocando o Mosquitto no próprio Raspberry Pi, todo o tráfego MQTT passa a ter o Pi
como destino. Ele enxerga tudo capturando a própria interface, sem espelhamento de
porta, sem configuração especial de switch.

```
   ESP32  ──── Wi-Fi ────▶  Raspberry Pi 3
 (sensor)                  ├── Mosquitto (broker MQTT, porta 1883)
                           └── Docker
                               └── detect.py
                                   ├── PyShark → tshark (captura em wlan0)
                                   ├── FlowMeter (pacotes → fluxos)
                                   └── RandomForest (classifica)

   Máquina de teste ──── mesma rede isolada ────▶ gera tráfego de ataque
```

Sobre o Docker: o container precisa de `--net=host` e das capacidades `NET_RAW` e
`NET_ADMIN`. Sem elas, ele só enxerga a rede virtual interna do Docker e a captura
sai vazia. Vale saber explicar isso, porque é a pergunta técnica mais provável.

## 3.5 Rotulagem por construção

Tráfego capturado ao vivo não vem com rótulo. Sem rótulo, não há como calcular F1.

A solução é separar a coleta em janelas temporais limpas e declarar o rótulo pela
fase:

- **Janela benigna**: só o ESP32 publicando. Rode `detect.py --phase benign` por
  uns 30 minutos. Tudo que aparecer é, por construção, normal.
- **Janela de ataque**: de outra máquina da bancada, gere varredura e inundação
  contra os seus próprios dispositivos. Rode `--phase attack`.

Ferramentas padrão de teste dão conta: `nmap` produz varredura (categoria
*scanning* ou *reconnaissance* nas bases), `hping3` produz inundação SYN ou UDP
(categoria *DoS* / *DDoS*).

No CSV final, a coluna `phase` é a verdade de campo e a coluna `pred` é a previsão
do modelo. Cruzando as duas você obtém F1, taxa de falso positivo e taxa de falso
negativo sobre tráfego real.

**Rede isolada é obrigatório.** Use roteador dedicado ou VLAN separada, com os seus
equipamentos apenas. Nunca na rede da universidade. Além da questão legal e ética
óbvia, tráfego de terceiros entrando na janela contamina o rótulo por construção e
invalida toda a medição.

---

# Parte 4 — O que esperar dos resultados

## 4.1 Previsões

Faça essas previsões antes de rodar. Acertar ou errar, as duas coisas são
apresentáveis, e prever antes demonstra entendimento.

**O F1 macro vai ficar muito abaixo do F1 ponderado no BoT-IoT.** Causa: 429
registros benignos. Confiança alta.

**A avaliação cruzada entre bases vai despencar.** Treinar no BoT-IoT e testar no
ToN-IoT Network deve derrubar bastante o desempenho, porque são testbeds
diferentes, com topologias e ferramentas de geração diferentes. Isso mostra que os
modelos aprendem o testbed, não o ataque.

**O falso positivo no tráfego real vai ser o problema.** Reconexão do ESP32 depois
de oscilação de Wi-Fi, keepalive do MQTT, mDNS e ARP produzem fluxos curtos,
unidirecionais, sem resposta. Isso é `ATTEMPT` com `bytes_ratio` perto de 1,0 —
exatamente a forma de uma varredura. O modelo vai marcar tráfego legítimo como
ataque.

**O Random Forest deve ficar próximo do MLP em qualidade e bem à frente em custo.**
Em dados tabulares, ensembles de árvores costumam empatar ou vencer redes neurais
rasas.

## 4.2 Por que o falso positivo é a melhor conclusão possível

Imagine um IDS com 1% de falso positivo numa rede que abre 10.000 fluxos por hora.
São 100 alarmes falsos por hora, 2.400 por dia. Nenhum operador humano acompanha
isso. O sistema é desligado na primeira semana.

Por isso um F1 de 0,999 em CSV e um sistema inutilizável na prática não são
contraditórios. São a mesma coisa vista de dois ângulos, e mostrar isso com medição
própria é uma contribuição real.

O enunciado do trabalho é explícito: *"Um resultado ruim é um resultado. Portanto,
se seu trabalho não obteve um bom resultado, você não terá desconto algum. Contudo,
você deverá justificar na sua apresentação porque o resultado foi ruim."*

Resultado ruim bem explicado vale mais que 99,9% sem explicação.

---

# Parte 5 — Perguntas que a banca pode fazer

**Por que Random Forest e não uma rede neural mais profunda, ou um transformer?**
Porque o objetivo é a borda. Um Pi 3 de 1 GB não roda arquitetura profunda em tempo
útil, e a base é tabular, terreno onde ensembles de árvores são historicamente
competitivos. Além disso, o Random Forest tapa um buraco concreto: a árvore do
Orange falhou no BoT-IoT no artigo original.

**Você não está apenas repetindo o artigo com outro algoritmo?**
Não. São três diferenças. Primeira, o algoritmo novo, que nenhum trabalho comparou
nessas bases junto com esses cinco. Segunda, o modelo sai do CSV e classifica
tráfego real capturado por mim. Terceira, meço custo computacional — latência,
memória, vazão — que o artigo não reporta em nenhum lugar.

**Por que o F1 caiu tanto em relação ao artigo?**
Porque reporto F1 macro, e o artigo reporta ponderado. No BoT-IoT a classe benigna
tem 429 registros num total de 3,3 milhões, então na média ponderada ela
praticamente não existe. Os dois números estão na minha tabela, lado a lado.

**Como você sabe que o tráfego capturado era realmente ataque?**
Rotulagem por construção. Coletei em janelas separadas: numa só o ESP32 publicava,
noutra gerei varredura e inundação de uma máquina conhecida, em rede isolada. A
fase é gravada em cada linha do log.

**O modelo foi treinado com dados de 2019 e você testou em 2026. Isso é válido?**
É uma limitação real, e o desempenho ruim no tráfego atual é em parte evidência
disso. Os padrões de ataque mudaram e as bases envelheceram. É justamente um dos
motivos pelos quais a validação em tráfego real importa: ela expõe o
envelhecimento que a avaliação em CSV esconde.

**Por que colocar o broker MQTT no Raspberry Pi?**
Por visibilidade de rede. Num switch, o Pi só recebe os quadros endereçados a ele.
Sendo o broker, todo o tráfego MQTT termina nele e a captura enxerga tudo, sem
depender de espelhamento de porta.

**Qual a maior limitação do seu trabalho?**
O volume e a diversidade do tráfego real. Um ESP32 publicando telemetria não
reproduz a heterogeneidade de uma rede IoT de produção, com dezenas de dispositivos
de fabricantes diferentes. Minhas conclusões sobre falso positivo valem para o meu
testbed e precisariam de validação em escala maior.

**Por que não usou aprendizado profundo?**
Restrição de hardware e de tempo, e porque a comparação de referência era com
algoritmos clássicos. Acrescentar uma arquitetura profunda mudaria o eixo da
comparação e não caberia no Pi 3.

**O que exatamente o flowmeter faz?**
Recebe pacotes individuais do PyShark e reconstrói conversas, agrupando pela
5-tupla. Acumula bytes e contagem de pacotes em cada direção, observa os flags TCP
para inferir o estado da conexão, e emite o fluxo quando ele fica ocioso por 15
segundos. A saída tem exatamente as mesmas 11 colunas usadas no treino.

**Por que descartou o endereço IP se ele ajuda a classificar?**
Porque ele ajuda pelo motivo errado. No testbed o atacante era sempre a mesma
máquina, então o modelo aprenderia o endereço em vez do comportamento. Funcionaria
perfeitamente no teste e falharia em qualquer outra rede. Inclusive medi isso: há
um experimento rodando com e sem os identificadores.

---

# Parte 6 — Ordem de trabalho

1. Baixar BoT-IoT (versão "10 best features") e ToN-IoT.
2. Rodar `prepare.py --inspect` e conferir os nomes reais das colunas.
3. Trilha A: `replicate.py` nas duas bases. Comparar com as Tabelas 3 e 4.
4. Trilha A: repetir com `--keep-identifiers`. Medir o vazamento.
5. Trilha B: `prepare.py` e `train.py`. Exportar o modelo.
6. Montar o Pi: Mosquitto, Docker, ESP32 publicando.
7. Coletar janela benigna. Coletar janela de ataque.
8. Cruzar `phase` com `pred`. Gerar gráficos.
9. Montar os slides, ensaiar com cronômetro.

Reserve as duas últimas semanas inteiras para as etapas 8 e 9. Algo vai dar errado
na 6 ou na 7, e é melhor que sobre tempo.

---

# Parte 7 — Verificação de referências

O enunciado prevê perda de 0 a 6 pontos se **uma única** citação for fictícia ou
não condizente com o texto citado.

A referência principal, conferida por você no PDF:

> INUWA, M. M.; DAS, R. A comparative analysis of various machine learning methods
> for anomaly detection in cyber attacks on IoT networks. *Internet of Things*,
> v. 26, p. 101162, 2024. DOI: 10.1016/j.iot.2024.101162.

Duas armadilhas:

Não repita a afirmação da Seção 4.1 de que o BoT-IoT é subconjunto do ToN-IoT. São
bases distintas. Confira nas fontes primárias, que estão na própria bibliografia do
artigo: Koroniotis et al. (ref. 7) para o BoT-IoT, Alsaedi et al. e Moustafa
(refs. 31 e 32) para o ToN-IoT.

Qualquer outra referência que você acrescentar precisa ser aberta e lida. Se veio
de sugestão de IA sem verificação, o risco é o trabalho inteiro.
