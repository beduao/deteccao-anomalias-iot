# Verificação do artigo-base e ajustes no plano

## Referência correta (verificada no PDF)

> INUWA, Muhammad Muhammad; DAS, Resul. A comparative analysis of various machine
> learning methods for anomaly detection in cyber attacks on IoT networks.
> **Internet of Things**, v. 26, p. 101162, 2024. DOI: 10.1016/j.iot.2024.101162.

Recebido em 6 jan. 2024, aceito em 10 mar. 2024, disponível online em 12 mar. 2024.
Filiação: Federal University Dutse (Nigéria) e Fırat University (Türkiye). O artigo
é derivado da tese de doutorado de Inuwa, orientada por Das.

Cite o periódico, não o ScienceDirect nem o repositório de download.

---

## O que o seu roteiro acertou

| Afirmação do roteiro | Situação |
|---|---|
| Periódico *Internet of Things*, Elsevier, 2024 | Confere |
| Autores Inuwa e Das | Confere |
| Análise comparativa de métodos de ML para ataques em IoT | Confere |
| Implementação em Orange-3, não em código | Confere (Seção 4.2 e Fig. 3) |
| Cinco classificadores | Confere: SVM, k-NN, Rede Neural, Tree, Regressão Logística |
| Bases ToN-IoT e BoT-IoT | Confere, com ressalva importante abaixo |
| Rede neural melhor, F1 perto de 99,9% | Confere: 0,999 nas Tabelas 3 e 4 |

Uma observação sobre o número: as Tabelas 3 e 4 trazem F1 = 0,999, mas a linha
"Our paper" da Tabela 1 diz 99,99%. O próprio artigo é inconsistente. Prefira
citar 0,999 e a tabela de origem.

---

## Correção obrigatória: qual ToN-IoT eles usaram

Seção 4.3.1, textualmente: *"The comparison method used data sets from ToN-IoT
Windows 7 and 10 operating system datasets. Windows 7 has 133 properties... The
Windows 10.csv file has 125 properties"*.

**Eles não usaram o ToN-IoT Network.** Usaram os arquivos de telemetria do sistema
operacional Windows: contadores de processo, memória e registro. Isso é dado de
**host**, não de rede. As matrizes de confusão (Tabelas 5 a 9) confirmam, com
71.760 registros e classes DDoS, DoS, Injection, MITM, Normal, Password, Scanning
e XSS.

Consequência direta para o seu projeto: **a parte ToN-IoT do artigo não pode
alimentar a captura ao vivo no Raspberry Pi.** Não existe tradução entre um
contador de processo do Windows e um pacote MQTT. Só o BoT-IoT, que é tráfego de
rede derivado do Argus, serve para embarcar.

**O plano fica em duas trilhas:**

- **Trilha A — replicação** (`src/replicate.py`): roda os 5 classificadores mais o
  Random Forest nas features nativas de cada base, incluindo o ToN-IoT Windows.
  Reproduz fielmente a comparação do artigo.
- **Trilha B — borda** (`src/prepare.py` → `train.py` → `detect.py`): usa apenas
  bases de rede sob o esquema canônico. BoT-IoT como base principal; o ToN-IoT
  **Network** (versão diferente da que o artigo usou) entra como sua segunda base.

Isso não foge do objetivo apresentado. Você prometeu acrescentar o Random Forest e
validar em hardware com tráfego real, e é exatamente o que as duas trilhas fazem.
A separação vira um slide de metodologia, não um problema.

---

## Três achados que sustentam a apresentação final

### 1. O modelo de árvore falhou por completo no BoT-IoT

Tabela 3, linha `Tree`: `error` em todas as colunas. O texto explica: *"Tree failed
with error: Exhaustive binarization does not handle attributes with more than 16
values"*. Em seguida o artigo afirma que o F1 ainda vale comparação, mas não existe
F1 de árvore para o BoT-IoT em lugar nenhum.

Ou seja: a comparação no BoT-IoT tem quatro modelos, não cinco, e a família de
árvores ficou sem representante. Isso dá ao Random Forest uma justificativa muito
mais forte do que a computacional que você usou na primeira apresentação: ele não é
só mais leve, ele **preenche uma lacuna documentada no artigo original**. É uma
limitação da ferramenta (o widget do Orange), não do algoritmo, e o scikit-learn
não tem essa restrição.

### 2. A classe benigna do BoT-IoT é praticamente inexistente

Tabela 10: Normal = **429** registros num total de 3.301.671. São 0,013%. A classe
Theft tem 72.

Um classificador que responda "ataque" para tudo acerta 99,987%. O F1 de 0,999
reportado é média ponderada sobre as classes, então a classe benigna quase não
influencia o número. Para um IDS, cuja função é justamente separar o tráfego normal
do malicioso, isso inverte o problema.

O `replicate.py` reporta F1 ponderado e F1 macro lado a lado. A distância entre os
dois é o seu resultado mais forte, e é reprodutível com poucas linhas.

### 3. Os valores de AUC são matematicamente impossíveis

Tabela 3: AUC de −8,114, −8,110, −8,100 e −7,981. Tabela 4: AUC de 1,006 e 1,055.
AUC é uma área sob curva normalizada, sempre entre 0 e 1.

Apresente isso de forma factual e sóbria — como evidência de que replicar e
verificar tem valor, não como crítica pessoal aos autores. É defensável e mostra
leitura cuidadosa.

---

## Um erro do artigo que você não deve repetir

Seção 4.1: *"The Bot-IoT dataset is a specific subset of the ToN-IoT dataset"*.

São bases distintas, de testbeds distintos, publicadas em momentos distintos pelo
mesmo grupo da UNSW Canberra. Confira nas fontes primárias, que estão na própria
lista de referências do artigo: Koroniotis et al. para o BoT-IoT (ref. [7]) e
Alsaedi et al. / Moustafa para o ToN-IoT (refs. [31] e [32]).

Se você repetir essa afirmação num slide, ela conta como citação não condizente com
o texto citado.

---

## Ajustes já aplicados no código

- `prepare.py`: `--dataset toniot` virou `toniot_net`, com nota explicando que o
  artigo usou a versão Windows.
- `train.py` e `replicate.py`: `class_weight` balanceado, sem o qual o modelo
  aprende a responder "ataque" sempre.
- `replicate.py` (novo): replica os 5 classificadores do artigo com os
  hiperparâmetros declarados na Seção 4.3.2 (Tree profundidade 100; MLP 100
  neurônios, ReLU, Adam, alpha 1e-4, 200 iterações; SVM C=1; k-NN k=5 euclidiano
  uniforme; LR ridge C=1), acrescenta o Random Forest, e reporta F1 ponderado,
  macro e da classe benigna.
- Flag `--keep-identifiers`: o artigo não diz quais colunas foram descartadas no
  widget Select Columns. Os arquivos do BoT-IoT trazem `saddr`, `daddr`, `sport`,
  `dport` e agregados por IP de origem. Rodar com e sem esses campos mede quanto do
  desempenho vem de memorizar endereço em vez de aprender comportamento.

---

## Para o tráfego ao vivo

Treine no BoT-IoT com `class_weight`, senão o modelo embarcado vai marcar quase
todo o tráfego do seu ESP32 como ataque — não por estar errado sobre a rede, mas
por ter aprendido numa base onde tráfego benigno quase não existe. Essa previsão,
confirmada ou refutada pela medição, já é um resultado apresentável.
