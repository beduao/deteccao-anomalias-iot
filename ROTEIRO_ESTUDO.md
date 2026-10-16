# Roteiro de estudo

O mínimo para você rodar o projeto com segurança e defender na banca. Não é um
curso de ciência de dados — é exatamente o que este trabalho exige, e nada além.

Baseado na sua autoavaliação: "básico em tudo" (pandas e scikit-learn). Então
começamos pela base e subimos só até onde o projeto precisa.

Tempo total estimado: **10 a 12 horas**, que cabem na semana 1 em paralelo com o
desbloqueio de hardware. Nada aqui depende das bases terem chegado.

---

## Como usar este roteiro

Três blocos, em ordem de prioridade. Se o tempo apertar, o Bloco 1 é inegociável
(é o que a banca vai perguntar), o Bloco 2 é necessário para rodar o código, e o
Bloco 3 é o que amarra os dois.

Para cada tópico há: o que estudar, por que importa no SEU projeto, onde ele
aparece no seu código, e um teste de "você entendeu" — uma pergunta que você deve
conseguir responder em voz alta, sem consultar. Se não conseguir, volte ao tópico.

Estude com o código aberto ao lado. O melhor material do projeto são os próprios
arquivos: ler o `GUIA_DE_DOMINIO.md` e depois olhar onde cada conceito aparece no
`.py` ensina mais rápido que tutorial genérico.

---

# BLOCO 1 — Métricas de classificação (4 horas) — O MAIS IMPORTANTE

Este bloco é o coração intelectual do seu trabalho. A sua extensão inteira gira
em torno de uma métrica enganosa. Se você dominar isto, defende o trabalho.

## 1.1 Matriz de confusão (1 hora)

**O que é:** uma tabela 2x2 que cruza o que era verdade com o que o modelo previu.
Quatro caixas: verdadeiro positivo (era ataque, previu ataque), verdadeiro negativo
(era normal, previu normal), falso positivo (era normal, previu ataque) e falso
negativo (era ataque, previu normal).

**Por que importa no seu projeto:** tudo o mais deriva daqui. As duas caixas de
erro têm nomes e consequências diferentes, e a banca vai querer que você saiba
distinguir. Falso positivo é alarme falso; falso negativo é ataque que passou.

**Onde aparece no seu código:** `train.py`, linha 93, `confusion_matrix(...).ravel()`
desmembra a matriz exatamente nessas quatro caixas: `tn, fp, fn, tp`.

**Teste de "você entendeu":** explique, sem olhar, a diferença entre um falso
positivo e um falso negativo num IDS, e diga qual dos dois é mais perigoso e por quê.
(Resposta curta: depende do contexto, mas falso negativo deixa o ataque entrar;
falso positivo demais faz o operador desligar o sistema. Você tem que saber
argumentar os dois lados.)

## 1.2 Precisão e revocação (1,5 hora) — O CONCEITO-CHAVE DA BANCA

**O que é:**
- **Precisão** = dos que o modelo marcou como ataque, quantos eram mesmo ataque.
  Fórmula: tp / (tp + fp). Precisão baixa = muito alarme falso.
- **Revocação (recall)** = dos ataques que existiam de verdade, quantos o modelo
  pegou. Fórmula: tp / (tp + fn). Revocação baixa = ataque passando batido.

**A tensão entre as duas:** melhorar uma costuma piorar a outra. Um modelo
paranoico que marca tudo como ataque tem revocação perfeita (não deixa nada passar)
mas precisão péssima (alarme o tempo todo). Um modelo tímido é o oposto.

**Por que importa no seu projeto:** esta é a pergunta mais provável da banca, nas
palavras do seu próprio guia. E é a base para entender o F1.

**Onde aparece no seu código:** `train.py`, linhas 100-101, calcula `false_positive_rate`
e `false_negative_rate` — as taxas de erro que se relacionam diretamente com precisão
e revocação.

**Teste de "você entendeu":** um modelo tem precisão 0,99 e revocação 0,40. Descreva,
em uma frase, que tipo de modelo é esse. (Resposta: quando ele dá o alarme, quase
sempre acerta, mas deixa passar 60% dos ataques — tímido demais para um IDS.)

## 1.3 F1, e por que ponderado vs. macro é o seu trabalho (1,5 hora)

**O que é o F1:** a média harmônica de precisão e revocação. Harmônica, não
aritmética, porque pune o desequilíbrio: se uma das duas é zero, o F1 é zero, não
0,5. É um número único que resume as duas.

**F1 ponderado vs. macro — o cerne da sua extensão:**
- **F1 macro:** calcula o F1 de cada classe e tira a média SIMPLES. A classe
  benigna vale tanto quanto a de ataque, mesmo tendo mil vezes menos exemplos.
- **F1 ponderado:** a média é PONDERADA pelo número de exemplos de cada classe.
  Com 429 benignos contra 3,3 milhões de ataque, a classe benigna contribui com
  0,013% do resultado. Ela some.

O artigo reporta o ponderado (o Orange chama de "average over classes") e chega a
0,999. Você reporta os dois lado a lado, e a distância entre eles é a sua
contribuição científica.

**Por que importa no seu projeto:** é literalmente o resultado principal que a sua
apresentação final vai mostrar. Um F1 de 0,999 que desaba quando calculado de forma
justa.

**Onde aparece no seu código:** `replicate.py`, linhas 193-195, calcula os três F1
(ponderado, macro, e da classe benigna) lado a lado. Rode este arquivo e leia a
saída: você vê o fenômeno acontecer.

**Teste de "você entendeu":** explique, sem olhar, por que um modelo pode ter F1
ponderado de 0,999 e F1 macro de 0,60 na mesma base. (Resposta: a base é
desbalanceada; o ponderado é dominado pela classe gigante que o modelo acerta, e o
macro expõe que ele vai mal na classe rara.)

---

# BLOCO 2 — Pandas mínimo (4 horas) — PARA RODAR O CÓDIGO

Você não vai escrever pandas do zero. Precisa ler, rodar e ajustar. O foco é
entender o que os scripts fazem, não virar especialista.

## 2.1 DataFrame e leitura de CSV (1,5 hora)

**O que é:** um DataFrame é uma tabela na memória — linhas e colunas, como uma
planilha. É a estrutura central do pandas. `pd.read_csv("arquivo.csv")` carrega um
CSV num DataFrame.

**O que praticar:** abrir um CSV qualquer, ver as primeiras linhas com `.head()`,
ver os nomes das colunas com `.columns`, ver o tamanho com `.shape`, e ver um resumo
com `.describe()` e `.info()`. Só isso já cobre 80% do que você precisa.

**Por que importa no seu projeto:** é exatamente o que o `--inspect` faz por baixo.
Você vai usar isso para conferir os nomes reais das colunas de cada base antes de
preencher os mapeamentos.

**Onde aparece no seu código:** `prepare.py`, linha 163, `pd.read_csv(...)`; e a
função `main` inteira do `--inspect` (linhas 217-221) só lista `df.columns`.

**Teste de "você entendeu":** dado um CSV, quais comandos você roda para descobrir
quantas linhas ele tem e como as colunas se chamam? (Resposta: `.shape` e `.columns`,
ou `.info()` que mostra os dois.)

## 2.2 Selecionar colunas e filtrar linhas (1,5 hora)

**O que é:**
- Selecionar coluna: `df["duration"]` pega uma coluna; `df[["a", "b"]]` pega várias.
- Filtrar linha: `df[df["duration"] >= 0]` mantém só as linhas onde a condição é
  verdadeira.

**O que praticar:** separar features do rótulo (`X = df[lista]`, `y = df["label"]`),
e filtrar linhas por uma condição.

**Por que importa no seu projeto:** é como o código separa o que entra no modelo do
que ele deve prever, e como remove linhas ruins.

**Onde aparece no seu código:** `train.py`, linha 120, `X, y = df[ALL_FEATURES], df[LABEL]`
é seleção de colunas; `prepare.py`, linha 197, `out[out["duration"] >= 0]` é filtro
de linha.

**Teste de "você entendeu":** o que a linha `X, y = df[ALL_FEATURES], df[LABEL]`
faz, em palavras? (Resposta: separa a tabela em duas partes — as onze colunas de
entrada do modelo, e a coluna de resposta que ele deve aprender.)

## 2.3 Agrupar e o essencial sobre tipos (1 hora)

**O que é:** `df.groupby("label")` agrupa linhas pelo valor de uma coluna, para
aplicar algo a cada grupo. E `pd.to_numeric(..., errors="coerce")` converte texto em
número, transformando o que falhar em vazio (NaN) em vez de quebrar.

**Por que importa no seu projeto:** o agrupamento é o que faz a amostragem
estratificada (preservar a proporção de classes). A conversão numérica é a limpeza
de dados sujos que aparece em todo o pré-processamento.

**Onde aparece no seu código:** `prepare.py`, linhas 229-233, o `groupby(LABEL)`
faz a amostragem estratificada; e `pd.to_numeric(..., errors="coerce")` aparece em
vários lugares como linha 121.

**Teste de "você entendeu":** por que a amostragem usa `groupby(LABEL)` em vez de
sortear linhas aleatoriamente? (Resposta: para preservar a proporção entre benigno
e ataque; com 429 benignos, um sorteio simples poderia não pegar nenhum.)

---

# BLOCO 3 — scikit-learn conceitual (3 horas) — PARA AMARRAR TUDO

Você quase não escreve scikit-learn diretamente — os scripts encapsulam. O que
precisa é entender os conceitos, para explicar o que o código faz.

## 3.1 Treino e teste, e por que se separa (1 hora)

**O que é:** você divide os dados em duas partes. Treina o modelo numa (treino) e
mede o desempenho na outra (teste), que ele nunca viu. Isso mede se ele **generaliza**
ou só **decorou**.

**O conceito de sobreajuste (overfitting):** um modelo que decora o treino tem nota
perfeita nele e nota ruim em dados novos. A separação treino/teste é o que revela
isso. É por isso que a nota que importa é sempre no teste.

**Por que importa no seu projeto:** é a base de toda a avaliação. E conecta com a
avaliação cruzada entre bases (treinar no BoT-IoT, testar no CICIoT2023), que é uma
versão extrema disto: teste em dados de um mundo totalmente diferente.

**Onde aparece no seu código:** `train.py`, linhas 121-122, `train_test_split` com
`test_size=0.30` (30% para teste) e `stratify=y` (mantém a proporção de classes).

**Teste de "você entendeu":** por que não se mede o desempenho do modelo nos mesmos
dados em que ele treinou? (Resposta: porque ele pode ter decorado; a nota no treino
não diz se ele funciona em dados novos.)

## 3.2 Pré-processamento: normalizar e codificar (1 hora)

**O que é:**
- **Normalizar** (StandardScaler): colocar todos os números na mesma escala. Sem
  isso, `src_bytes` (valores na casa dos milhares) dominaria `duration` (valores
  abaixo de 10) só pela magnitude.
- **One-hot** (OneHotEncoder): transformar categorias em texto (tcp, udp) em colunas
  numéricas de 0 e 1, porque o modelo não entende texto.

**Por que importa no seu projeto:** explica por que o código separa features
numéricas de categóricas, e por que modelos como k-NN e MLP precisam disso para
funcionar.

**Onde aparece no seu código:** `train.py`, `build_preprocessor` (linhas 46-54),
aplica StandardScaler nas numéricas e OneHotEncoder nas categóricas.

**Teste de "você entendeu":** por que `duration` e `src_bytes` precisam ser
normalizados antes de entrar num k-NN? (Resposta: o k-NN mede distância; sem
normalizar, a feature com números maiores dominaria a distância e a outra seria
ignorada.)

## 3.3 O que é cada classificador, em uma frase (1 hora)

Você não precisa da matemática. Precisa saber explicar cada um em uma frase, porque
seu trabalho compara seis deles.

- **Decision Tree:** uma sequência de perguntas sim/não sobre as features até chegar
  a uma decisão.
- **Random Forest (a sua extensão):** muitas árvores treinadas com aleatoriedade,
  e a resposta é o voto da maioria. Mais robusto que uma árvore só.
- **k-NN:** classifica um ponto olhando os k exemplos mais parecidos e vendo qual
  classe domina entre eles.
- **SVM:** traça a fronteira que melhor separa as duas classes no espaço das features.
- **Naive Bayes:** usa probabilidade, assumindo (ingenuamente) que as features são
  independentes.
- **MLP (rede neural, a vencedora do artigo):** camadas de neurônios que aprendem
  padrões complexos e não-lineares, à custa de mais processamento.

**Por que importa no seu projeto:** a banca pode apontar para qualquer um e pedir
"o que é esse?". E a comparação Random Forest vs. MLP (árvores vs. rede neural) é o
eixo da sua extensão.

**Onde aparece no seu código:** `train.py`, `make_models` (linhas 57-79), e
`replicate.py`, `models` (linhas 118-145).

**Teste de "você entendeu":** por que você escolheu Random Forest para embarcar no
Pi, e não a rede neural que venceu no artigo? (Resposta: na inferência o Random
Forest faz comparações numéricas simples, mais leves que a multiplicação de matrizes
da rede; é mais adequado a hardware fraco, e ainda preenche a lacuna da árvore que
falhou no Orange. Está no `GUIA_DE_DOMINIO.md`, seção 2.7.)

---

# Ordem sugerida e ritmo

Se você tem a semana 1 inteira:

- **Dia 1-2:** Bloco 1 completo (métricas). É o mais importante e o mais conceitual.
  Leia a seção 2.4 do `GUIA_DE_DOMINIO.md` junto.
- **Dia 3-4:** Bloco 2 (pandas), com um CSV qualquer aberto para praticar os comandos.
- **Dia 5:** Bloco 3 (scikit-learn conceitual), lendo o código ao lado.
- **Dia 6-7:** desbloqueio de hardware (boot do Ubuntu, gravar o Pi OS), que não
  depende deste estudo.

Se o tempo for curto, faça só o Bloco 1 completo e a seção 3.1 do Bloco 3. Com isso
você já roda o projeto e defende o essencial.

# O teste final: a pergunta que resume tudo

Quando terminar, você deve conseguir responder esta, em voz alta, em dois minutos,
sem consultar nada:

> "O artigo relatou F1 de 0,999. Por que esse número é enganoso, como o seu trabalho
> mostra isso, e por que o Random Forest que você adicionou é uma boa escolha para
> rodar num Raspberry Pi?"

Se você responde isso com clareza, dominou o núcleo do trabalho. Todo o resto é
detalhe que você preenche a partir daqui.
