# Status do projeto (atualizado em 16/10/2026)

Arquivo para retomar o trabalho numa sessão nova. Leia este primeiro e depois,
nesta ordem: `ROTEIRO_IMPLEMENTACAO.md` (calendário e portões), `VERIFICACAO.md`
(o que o artigo realmente fez), `GUIA_DE_DOMINIO.md` (conceitos) e `README.md`.

## Contexto em três linhas

Trabalho da disciplina de IA (UFS) da Beatriz Oliveira Eduão. Extensão do artigo
Inuwa & Das (2024), *Internet of Things* 26:101162: acrescentar Random Forest aos
5 classificadores, aplicar o método a uma base recente (CICIoT2023) e validar a
inferência num Raspberry Pi 3 com tráfego MQTT real de um ESP32. Apresentação de
resultados perto de 05/11/2026.

## Ambiente

- PC: Windows 11, 7,8 GB de RAM, **Python 3.14**. Comandos sempre a partir de
  `Desktop\iot`.
- **Use `py`, não `python`.** Desde 09/10, `python` responde "Python was not
  found" (o atalho da Microsoft Store passou a vir antes do Python no PATH);
  `py` chama o mesmo Python 3.14.6. Para voltar a usar `python`: Configurações
  → Aplicativos → Configurações avançadas → Aliases de execução de aplicativo →
  desligar "python.exe" e "python3.exe".
- Bibliotecas instaladas em 07/10 pelo `requirements-pc.txt`: **scikit-learn
  1.8.0, numpy 2.4.4, pandas 3.0.2** (o numpy 2.5.1 e o pandas 3.0.5 que estavam
  instalados foram trocados por essas versões).
- Há um segundo PC com 24 GB de RAM, não usado. Trocar de máquina exigiria
  reinstalar as mesmas versões; só vale se a RAM travar o `prepare.py`.
- Raspberry Pi 3 com Raspberry Pi OS 64 bits: pronto.
- HD com Ubuntu bootável (máquina de ataque): `nmap` e `hping3` testados.
- Roteador antigo dedicado para a rede isolada.

## Onde paramos

**Semana B do roteiro (13 a 19/10).** Lado do PC do Portão B concluído em 16/10
(`models/rf_edge.joblib` existe). Falta o lado do Pi: `teste.pcap` com tráfego
MQTT real do ESP32.

Feito:
- **Pasta do projeto corrigida (07/10).** O pacote de 07/10 tinha sido
  descompactado em `Desktop\iot\iot\`. O conteúdo foi copiado por cima da raiz
  e a subpasta removida. Os scripts em `src/` são os corrigidos.
- **BoT-IoT "10 best features"** em `data/raw/botiot/` (3.668.522 linhas).
- **Replicação no BoT-IoT: Portão A aprovado (07/10).** F1 ponderado entre
  0,9996 e 0,9999 nos 6 modelos.
- **CICIoT2023** baixado: `MERGED_CSV.zip`, 63 arquivos `Merged01..63.csv`,
  8,7 GB, em `data/raw/ciciot/MERGED_CSV/`.
- **Replicação no CICIoT2023 (08/10)** sobre o `Merged01.csv`, com e sem `IAT`.
- `replicate.py` ganhou a opção `--drop-cols` (remove colunas escolhidas; nome
  inexistente é erro). Registre a opção no `--name`, porque o CSV não a guarda.
- **ToN-IoT Windows baixado (até 14/10)** do OneDrive oficial da UNSW, nas duas
  versões: `data/raw/toniot_win_processed/` (`windows10_dataset.csv`,
  `windows7_dataset.csv`) e `data/raw/toniot_win_traintest/`
  (`Train_Test_Windows_10.csv`, `Train_Test_Windows_7.csv`). O
  `src/identify_toniot.py` mostrou que o artigo usou o
  **`Train_Test_Windows_10.csv`** (descoberta 6).
- **`replicate.py` com alvo multiclasse (14/10)** e as três rodadas
  multiclasse: ToN-W10, BoT-IoT e BoT-IoT com identificadores (descoberta 7 e
  tabela abaixo).
- **Trilha B no PC (16/10).** BoT-IoT "All features" em `data/raw/botiot_all/`
  (4 arquivos, 3.668.522 fluxos; todas as colunas do `COLMAP_BOTIOT` presentes
  e todos os 11 estados do Argus mapeados). Comandos rodados:
  ```
  py src/prepare.py --dataset botiot --input data/raw/botiot_all/ --output data/botiot.parquet --sample 300000
  py src/train.py --train data/botiot.parquet
  ```
  Resultado: `data/botiot.parquet` (300.000 fluxos: 477 benignos inteiros +
  299.523 ataques sorteados), `models/rf_edge.joblib` (**119,6 KB**),
  `models/metadata.json` e `results/metrics.csv`. Versões gravadas no
  metadata (scikit-learn 1.8.0, numpy 2.4.4, pandas 3.0.2) **iguais** às do
  `requirements-pi.txt`. Ver descoberta 9.

Resultados em `results/replication.csv`, que agora tem a coluna `target`
(`binary` ou `multiclass`). Cópia do arquivo antes dessa mudança:
`results/replication_backup_2026-10-14.csv`. O arquivo
`results/replication_script_antigo.csv` é uma rodada feita com o script antigo
(identificadores errados, `proto` perdido): **não usar**.

**Rodadas binárias (benigno × ataque).** Não são comparáveis com as Tabelas 3 e
4 do artigo, que classificam o tipo de ataque. Continuam válidas como
experimento complementar.

| Base | Modelo | F1 pond. | F1 macro | F1 benigno |
|---|---|---|---|---|
| BoT-IoT | Tree | 0,9999 | 0,9778 | 0,9556 |
| BoT-IoT | NeuralNetwork | 0,9998 | 0,9631 | 0,9263 |
| BoT-IoT | SVM | 0,9996 | 0,9403 | 0,8809 |
| BoT-IoT | kNN | 0,9997 | 0,9599 | 0,9199 |
| BoT-IoT | LogisticRegression | 0,9996 | 0,9353 | 0,8708 |
| BoT-IoT | RandomForest | 0,9999 | 0,9773 | 0,9547 |
| CICIoT2023 | Tree | 0,9851 | 0,9288 | 0,8655 |
| CICIoT2023 | NeuralNetwork | 0,9857 | 0,9329 | 0,8736 |
| CICIoT2023 | SVM | 0,9825 | 0,9191 | 0,8478 |
| CICIoT2023 | kNN | 0,9848 | 0,9286 | 0,8655 |
| CICIoT2023 | LogisticRegression | 0,9829 | 0,9205 | 0,8504 |
| CICIoT2023 | RandomForest | 0,9889 | 0,9478 | 0,9016 |

Leitura rápida: no CICIoT2023 o Random Forest é o melhor com folga no F1 do
benigno (0,90 contra 0,87 do segundo). É uma única divisão treino/teste; a
repetição em outros arquivos (abaixo) diz se a vantagem se sustenta.

**Rodadas multiclasse (tipo de ataque, como no artigo).** F1 ponderado
comparado com as Tabelas 3 e 4. "F1 benigno" aqui é o F1 da classe `normal`.

| Modelo | ToN-W10 artigo (Tab. 4) | ToN-W10 nosso | BoT-IoT artigo (Tab. 3) | BoT-IoT sem ids | BoT-IoT com ids |
|---|---|---|---|---|---|
| kNN | 0,992 | 0,9979 | 0,999 | 0,9936 | 0,9998 |
| Tree | 0,998 | 0,9997 | error | 0,9936 | 1,0000 |
| SVM | 0,997 | 1,0000 | 0,999 | 0,8617 | 0,9992 |
| NeuralNetwork | 0,999 | 0,9987 | 0,999 | 0,9527 | 0,9998 |
| LogisticRegression | 0,774 | 0,9998 | 0,775 | 0,8888 | 0,9998 |
| RandomForest | — | 1,0000 | — | 0,9939 | 0,9999 |

F1 macro e F1 benigno das mesmas rodadas:

| Modelo | ToN-W10 macro | ToN-W10 benigno | BoT sem ids macro | BoT sem ids benigno | BoT com ids macro | BoT com ids benigno |
|---|---|---|---|---|---|---|
| Tree | 0,9816 | 1,0000 | 0,9602 | 0,9534 | 1,0000 | 1,0000 |
| NeuralNetwork | 0,8743 | 0,9998 | 0,9123 | 0,9362 | 0,9584 | 0,9689 |
| SVM | 1,0000 | 1,0000 | 0,5227 | 0,2604 | 0,9124 | 0,9619 |
| kNN | 0,8720 | 0,9998 | 0,9478 | 0,9544 | 0,9632 | 0,9550 |
| LogisticRegression | 0,9821 | 1,0000 | 0,7891 | 0,9124 | 0,9434 | 0,9655 |
| RandomForest | 1,0000 | 1,0000 | 0,9601 | 0,9758 | 0,9802 | 0,9931 |

Leitura rápida:
- **ToN-W10:** os quatro modelos que o artigo reporta bem ficam a menos de
  0,006 da Tabela 4. A exceção é a regressão logística: 0,9998 aqui contra
  0,774 no artigo.
- **BoT-IoT:** os 0,999 da Tabela 3 só aparecem **com** identificadores. Sem
  eles, o SVM cai para 0,862 e a rede neural para 0,953. É um indício de que o
  artigo deixou identificadores entre as features (descoberta 8).
- **Regressão logística:** ~0,775 no artigo nas duas bases, bem acima disso
  aqui em todas as rodadas. Diferença sistemática de configuração. Hipótese
  ainda não testada: o Orange não normalizou as features; o nosso pipeline
  normaliza (`StandardScaler`).
- **F1 macro baixo no ToN-W10 (rede neural e kNN, 0,87)** vem da classe `mitm`,
  com 15 registros no arquivo e 4 no teste: os dois modelos erram os 4 (F1 da
  classe = 0). Sem `mitm`, o macro seria 0,999 (rede neural) e 0,997 (kNN).
  Com tão poucos casos, o número oscila muito. (Conferido em 16/10.)
- O SVM deu `ConvergenceWarning` (não convergiu em 3.000 iterações) no ToN-W10 e
  no BoT-IoT com identificadores.

Próximo passo imediato:

1. No Pi: Mosquitto aceitando o ESP32 (Mosquitto 2 só aceita conexões locais
   por padrão; criar `/etc/mosquitto/conf.d/lab.conf` com `listener 1883` e
   `allow_anonymous true`, aceitável só porque a rede é isolada), ESP32
   publicando e `teste.pcap` gravado com `tshark -f "tcp port 1883"`.
2. Copiar `src/`, `models/` e `requirements-pi.txt` para o Pi; criar um ambiente
   virtual (`python3 -m venv ~/iot-venv`) e instalar o `requirements-pi.txt`.
   Conferido em 14/10: há pacotes prontos para ARM 64 bits em Python 3.11 a
   3.13 para as três bibliotecas fixadas.
3. (Opcional, barato) Repetir o CICIoT2023 em outros arquivos:
   ```
   py src/replicate.py --input data/raw/ciciot/MERGED_CSV/Merged20.csv --name CICIoT2023-Merged20
   py src/replicate.py --input data/raw/ciciot/MERGED_CSV/Merged42.csv --name CICIoT2023-Merged42
   ```
4. (Opcional) Testar a hipótese da regressão logística: rodar sem o
   `StandardScaler` e ver se o F1 cai para perto de 0,775. Exige uma opção
   nova no `replicate.py`.

Pendente:
- Trilha de hardware: Mosquitto no Pi e ESP32 publicando.

## Descobertas que ainda não estão nos outros documentos

**1. A versão "10 best" não serve para a trilha B.** Colunas reais: `pkSeqID`,
`proto`, `saddr`, `sport`, `daddr`, `dport`, `seq`, `stddev`, `N_IN_Conn_P_SrcIP`,
`min`, `state_number`, `mean`, `N_IN_Conn_P_DstIP`, `drate`, `srate`, `max`,
`attack`, `category`, `subcategory`. Não há `dur`, `sbytes`, `dbytes`, `spkts`,
`dpkts` nem `state`, que são o que o `flowmeter.py` mede no Pi. Divisão das
versões:
- "10 best" → `replicate.py` (trilha A, a que o artigo usou).
- "All features" → `prepare.py` e `train.py` (trilha B, esquema canônico e Pi).

**2. Correções já feitas no `replicate.py`:**
- Remove `category` **e** `subcategory`. Antes só removia a primeira, o que
  vazaria o rótulo.
- Identificadores casados pelo nome inteiro da coluna. Assim saem `pkSeqID`,
  `saddr`, `sport`, `daddr`, `dport` e `seq`, e as features `N_IN_Conn_P_*`
  ficam.
- Texto detectado com `pd.api.types.is_numeric_dtype`. No pandas 3 o texto tem
  tipo `str` e o teste antigo (`dtype == object`) falhava em silêncio,
  descartando `proto` e zerando rótulos em texto. Corrigido também no
  `prepare.py`.
- Amostragem: mantém todos os benignos e sorteia os ataques. A proporção de
  benignos na amostra fica maior que na base original (BoT-IoT: 0,159% contra
  0,013%; CICIoT2023: 5,5% contra 2,3%). Isso precisa ser declarado na
  apresentação.

**3. Ponto para a banca (`seq` e identificadores no BoT-IoT).** Com
`--keep-identifiers`, todos os modelos melhoram e o Random Forest chega a
F1 = 1,0000. Atenção ao que essa rodada mantém de fato: `pkSeqID`, `seq` e
`saddr` (21 valores, vira one-hot). `daddr` (84 valores), `sport` e `dport` são
texto de alta cardinalidade e o script os descarta mesmo nessa rodada.

**4. CICIoT2023: qual versão e por que não entra na trilha B.**
- O site oferece `CSV/CSV.zip` e `CSV/MERGED_CSV.zip`. O `CSV.zip` tem 309
  arquivos separados por ataque, 39 colunas e **nenhuma coluna de rótulo** (a
  classe está só no nome da pasta). O README que vem nele descreve outra versão.
  O certo é o `MERGED_CSV.zip`: 39 colunas + `Label`.
- Nenhuma das duas tem `flow_duration`. As linhas são janelas de 10 a 100
  pacotes (coluna `Number`), não fluxos, e não há separação origem/destino.
  `Tot size` é igual a `AVG`. Por isso o `COLMAP_CICIOT2023` do `prepare.py` não
  tem como ser preenchido honestamente e a avaliação cruzada foi descartada
  (ver o quadro na Semana B do roteiro).
- Os 63 arquivos são equivalentes (base embaralhada). Proporção de benignos:
  Merged01 2,33%, Merged20 2,34%, Merged42 2,35%, Merged63 2,38%. Todos têm as
  34 classes. Um arquivo basta: o `replicate.py` sorteia 300 mil linhas e um
  arquivo tem mais de 700 mil.
- Não rodar o `prepare.py --inspect` nem o `replicate.py` sobre a pasta inteira
  do CICIoT2023: os dois carregam tudo na memória (cerca de 45 milhões de linhas).

**5. `IAT` no CICIoT2023 não muda o resultado.** A hipótese era que ela
funcionasse como carimbo de tempo, como o `seq` no BoT-IoT. Sem ela, o F1 do
benigno mudou no máximo 0,005 (Tree: 0,8655 → 0,8700; Random Forest: 0,9016 →
0,9017). Na tarefa benigno × ataque, a feature está limpa.

**6. Qual versão do ToN-IoT o artigo usou.** O artigo não diz. O
`src/identify_toniot.py` compara a proporção de cada classe de um arquivo com a
Tabela 5 (Normal 34.000, DDoS 15.670, Password 12.340, XSS 4.310, Injection
2.080, DoS 1.790, Scanning 1.520, MITM 50; total 71.760).
- **`Train_Test_Windows_10.csv` é o do artigo:** todas as classes batem com
  diferença máxima de 0,01 ponto percentual. 21.104 linhas e 126 colunas (o
  artigo fala em 125 propriedades).
- As outras três ficam a 15 pontos ou mais: `windows10_dataset.csv` (35.975
  linhas, 127 colunas, 69% normal contra 47% no artigo), `windows7_dataset.csv`
  (28.367 linhas, 135 colunas) e `Train_Test_Windows_7.csv` (15.980 linhas, 134
  colunas).
- **Ponto para a apresentação:** o texto diz que o Windows 7 foi usado, mas
  nenhuma tabela traz resultado dele. O Windows 7 tem classes diferentes
  (Backdoor e Ransomware, sem DoS nem MITM), e a Tabela 5 tem exatamente as 8
  classes do Windows 10.
- **Os dados do BoT-IoT também são os do artigo:** os totais da Tabela 10 são
  90% das nossas contagens (Normal 429 de 477, Theft 72 de 79, DDoS 1.733.961
  de 1.926.624, Reconnaissance 81.975 de 91.082).

**7. O artigo classifica o tipo de ataque, não benigno × ataque.** As matrizes
das Tabelas 5 a 13 têm 8 classes no ToN-IoT e 5 no BoT-IoT (DDoS, DoS, Normal,
Reconnaissance, Theft). Até 08/10 todas as rodadas eram binárias. Mudanças no
`replicate.py` em 14/10:
- `--multiclass`: o alvo é a coluna de tipo (`type` no ToN-IoT, `category` no
  BoT-IoT), em minúsculas. Sem a opção, nada muda.
- Amostragem para várias classes: classes com até `sample // nº de classes`
  registros entram inteiras; as maiores dividem o restante na proporção
  original. O script imprime quantos registros de cada classe ficaram.
- No multiclasse, os nomes das classes viram números (`LabelEncoder`) antes da
  divisão treino/teste. Com texto, o `MLPClassifier` com `early_stopping` quebra.
- "F1 benigno" no multiclasse é o F1 da classe `normal` (ou `benign` /
  `benigntraffic`).
- Coluna `target` no CSV. O script agora lê o CSV existente, marca as linhas
  antigas como `binary`, junta e reescreve tudo (via arquivo temporário).
- **Não estava no plano:** no ToN-W10, 69 contadores numéricos têm algumas
  células com um espaço em branco (" "), e o pandas lia a coluna inteira como
  texto. A regra de cardinalidade descartaria todas elas. Agora uma coluna de
  texto vira número se **todo** valor não vazio for número; o branco vira
  ausente (mediana). Portas em hexadecimal do BoT-IoT continuam texto.
- **Verificação:** a versão antiga e a nova rodaram nos mesmos dados no modo
  binário (BoT-IoT, BoT-IoT com identificadores, CICIoT2023 sem `IAT`). F1
  ponderado, macro, benigno e status ficaram idênticos nos 18 resultados.

**8. Indício de que o artigo usou identificadores no BoT-IoT.** Duas pistas
independentes:
- Os 0,999 da Tabela 3 (SVM, rede neural, kNN) só se reproduzem com
  identificadores; sem eles, SVM 0,862 e rede neural 0,953.
- A árvore do Orange falhou com "atributos com mais de 16 valores". Entre as
  colunas de texto do "10 best", só `saddr` (21 valores), `daddr` (84), `sport` e
  `dport` passam de 16. Alguma delas estava entre as features.

É indício, não prova: o artigo não lista as colunas usadas. Na apresentação,
diga "os números do artigo são reproduzidos quando os identificadores são
mantidos", não "o artigo usou identificadores".

**9. Trilha B: amostragem e o primeiro modelo do Pi (16/10).**
- O `--sample` do `prepare.py` era proporcional: em 300 mil fluxos sobrariam uns
  39 benignos. Agora segue a regra do `replicate.py` (classe rara inteira,
  ataques completam). Sem `--sample`, nada muda. Custo a declarar: benignos são
  0,159% da amostra contra 0,013% na base.
- Resultado no teste do PC (90.000 fluxos, 143 benignos):

  | Modelo | F1 macro | Taxa de falso positivo |
  |---|---|---|
  | DecisionTree | 0,9842 | 0,0350 |
  | MLP | 0,9718 | 0,0629 |
  | kNN | 0,9701 | 0,0629 |
  | LinearSVM | 0,7509 | 0,6364 |
  | **RandomForest** | 0,7505 | **0,0000** |
  | NaiveBayes | 0,6474 | 0,3147 |

- **O Random Forest troca alarme falso por ataque perdido.** Por causa do
  `class_weight="balanced_subsample"`, nenhum dos 143 benignos foi marcado como
  ataque, mas cerca de 280 dos 89.857 ataques (0,31%) foram classificados como
  benignos. Por isso a precisão da classe benigna é 0,34 e o F1 macro cai para
  0,75. Para o teste com o ESP32, onde o risco previsto é alarme falso, isso
  favorece o Random Forest. Mas a taxa de 0% vem de só 143 benignos.
- Dos 477 benignos da base, só 47 são TCP (a maioria é UDP com estado CON). O
  MQTT do ESP32 é TCP: espere alarmes falsos no tráfego real.
- O `train.py` diz "os cinco do artigo", mas usa Naive Bayes no lugar da
  regressão logística e um SVM diferente (SGD) do usado no `replicate.py`. Não
  afeta o modelo do Pi; importa se a tabela do `train.py` for para os slides.

## Atenção

- Python 3.14 é mais novo que o recomendado (3.11 ou 3.12). Até agora todas as
  bibliotecas instalaram sem problema.
- O `requirements-pi.txt` precisa das mesmas versões de scikit-learn e numpy que
  o `train.py` imprimir no PC.
- Toda referência bibliográfica nos slides precisa ser aberta e conferida:
  o enunciado prevê perda de 0 a 6 pontos por uma citação falsa ou não condizente.
- A conclusão do artigo (Seção 6) cita como trabalho futuro métodos de ensemble
  e o uso de outras bases públicas de redes IoT: é a justificativa do Random
  Forest e do CICIoT2023 na extensão.
