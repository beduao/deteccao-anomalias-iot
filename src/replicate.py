"""
Replicacao da comparacao de Inuwa & Das (2024), acrescida do Random Forest.

Roda sobre as features NATIVAS de cada base, sem esquema canonico, porque o
objetivo aqui e reproduzir o que o artigo fez e ver se os numeros batem.
Funciona tanto no BoT-IoT "10 best features" quanto nos arquivos ToN-IoT
Windows 7 / Windows 10, que sao os que o artigo realmente usou. Na extensao,
roda tambem no CICIoT2023 (MERGED_CSV), uma base de 2023 que o artigo nao usou.

Uso:
    python src/replicate.py --input data/raw/botiot/ --name BoT-IoT
    python src/replicate.py --input data/raw/botiot/ --name BoT-IoT-vazamento \\
        --keep-identifiers        # demonstra o efeito do vazamento
    python src/replicate.py --input data/raw/ciciot/MERGED_CSV/Merged01.csv \\
        --name CICIoT2023-sem-IAT --drop-cols IAT   # testa uma feature suspeita
    python src/replicate.py \\
        --input data/raw/toniot_win_traintest/Train_Test_Windows_10.csv \\
        --name ToN-W10 --multiclass   # alvo = tipo de ataque, como no artigo

Alvo:
  - binario (padrao): benigno x ataque, pela coluna de rotulo ("label"/"attack").
  - --multiclass: o TIPO de ataque, pela coluna de tipo ("type" no ToN-IoT,
    "category" no BoT-IoT). E o que o artigo fez: as matrizes de confusao das
    Tabelas 5 a 13 tem 8 classes no ToN-IoT e 5 no BoT-IoT. Para comparar com
    as Tabelas 3 e 4, use --multiclass.

Reporta as metricas lado a lado:
  - F1 ponderado  : o que o artigo reportou ("average over classes" do Orange)
  - F1 macro      : trata cada classe igualmente
  - F1 benigno    : F1 so da classe benigna ("normal" no modo multiclasse)

A diferenca entre o ponderado e o macro e o resultado mais importante do
trabalho. No BoT-IoT a classe benigna tem 429 registros contra 3,3 milhoes de
ataque (Tabela 10 do artigo). O F1 ponderado ignora a classe rara; o macro nao.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

RANDOM_STATE = 42

# Colunas que causam vazamento: o modelo memoriza o endereco do atacante
# em vez de aprender o comportamento do ataque.
IDENTIFIER_PATTERNS = re.compile(
    r"^(saddr|daddr|src_ip|dst_ip|srcip|dstip|sport|dport|src_port|dst_port|"
    r"smac|dmac|mac|stime|ltime|ts|timestamp|time|date|seq|pkseqid|uid|id|"
    r"soui|doui|sco|dco)$", re.IGNORECASE)
# O casamento e pelo nome INTEIRO da coluna. Assim "saddr" e removida, mas
# "N_IN_Conn_P_SrcIP" (contagem de conexoes por IP de origem, uma feature de
# comportamento) e mantida, mesmo contendo "SrcIP" no nome.

LABEL_CANDIDATES = ["label", "attack"]
TYPE_CANDIDATES = ["type", "category", "subcategory", "attack_cat"]
# Nome da classe benigna no modo multiclasse, conforme a base.
BENIGN_NAMES = ["normal", "benign", "benigntraffic"]

# Ordem das colunas no CSV de resultados.
RESULT_COLS = ["dataset", "model", "target", "f1_weighted", "f1_macro",
               "f1_benign", "train_s", "identifiers_kept", "status"]


def load(path: str) -> pd.DataFrame:
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.csv")))
        if not files:
            raise FileNotFoundError(f"Nenhum CSV em {path}")
        print(f"[rep] Lendo {len(files)} arquivo(s)")
        return pd.concat((pd.read_csv(f, low_memory=False) for f in files),
                         ignore_index=True)
    return pd.read_csv(path, low_memory=False)


def find_col(df, candidates):
    lower = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def numeric_with_blanks(X: pd.DataFrame) -> list[str]:
    """Colunas de texto que sao numericas a menos de celulas em branco.

    No ToN-IoT Windows, dezenas de contadores (processador, rede, memoria,
    disco) tem algumas celulas com " ". O pandas le a coluna inteira como
    texto, e a regra de cardinalidade abaixo a descartaria. A conversao so
    acontece se TODO valor nao vazio for numero; qualquer outro texto (ex.:
    portas em hexadecimal no BoT-IoT) mantem a coluna como esta.
    """
    out = []
    for c in X.columns:
        if pd.api.types.is_numeric_dtype(X[c]):
            continue
        s = X[c].astype(str).str.strip()
        vazio = X[c].isna() | (s == "") | (s.str.lower() == "nan")
        conv = pd.to_numeric(s.where(~vazio), errors="coerce")
        if conv.notna().any() and not (conv.isna() & ~vazio).any():
            out.append(c)
    return out


def prepare(df: pd.DataFrame, keep_ids: bool, drop_cols: list[str] | None = None,
            multiclass: bool = False):
    label_col = find_col(df, LABEL_CANDIDATES)
    type_col = find_col(df, TYPE_CANDIDATES)
    if multiclass:
        if type_col is None:
            raise KeyError("--multiclass: coluna de tipo de ataque nao encontrada "
                           f"({TYPE_CANDIDATES}). Colunas: {list(df.columns)}")
        y = df[type_col].astype(str).str.lower().str.strip()
    else:
        if label_col is None:
            raise KeyError(f"Coluna de rotulo nao encontrada. Colunas: {list(df.columns)}")
        y_raw = df[label_col]
        if not pd.api.types.is_numeric_dtype(y_raw):
            y = (~y_raw.astype(str).str.lower().str.strip()
                 .isin({"0", "normal", "benign", "false"})).astype(int)
        else:
            y = pd.to_numeric(y_raw, errors="coerce").fillna(0).astype(int)

    # Remove TODAS as colunas de rotulo ou tipo de ataque presentes. No BoT-IoT
    # existem "category" e "subcategory"; se uma delas ficasse como feature, o
    # modelo receberia a resposta pronta.
    lower = {c.lower().strip(): c for c in df.columns}
    type_cols = {lower[t] for t in TYPE_CANDIDATES if t in lower}
    drop = ({label_col} if label_col else set()) | type_cols
    X = df.drop(columns=[c for c in drop if c in df.columns])

    if not keep_ids:
        ident = [c for c in X.columns if IDENTIFIER_PATTERNS.search(c)]
        if ident:
            print(f"[rep] Descartando {len(ident)} coluna(s) identificadora(s): "
                  f"{ident[:8]}{' ...' if len(ident) > 8 else ''}")
            X = X.drop(columns=ident)
    else:
        print("[rep] ATENCAO: identificadores MANTIDOS (experimento de vazamento)")

    # Colunas escolhidas na linha de comando (ex.: --drop-cols IAT), para medir
    # quanto do resultado depende de uma feature suspeita. Nome errado e erro,
    # nao aviso: um typo nao pode passar como "rodada sem a feature".
    if drop_cols:
        lower_x = {c.lower().strip(): c for c in X.columns}
        faltando = [c for c in drop_cols if c.lower().strip() not in lower_x]
        if faltando:
            raise KeyError(f"--drop-cols: coluna(s) inexistente(s): {faltando}. "
                           f"Colunas: {list(X.columns)}")
        escolhidas = [lower_x[c.lower().strip()] for c in drop_cols]
        print(f"[rep] Descartando por --drop-cols: {escolhidas}")
        X = X.drop(columns=escolhidas)

    # Numeros lidos como texto por causa de celulas em branco: viram numero, e
    # o branco vira ausente (preenchido pela mediana no pipeline).
    conv = numeric_with_blanks(X)
    if conv:
        print(f"[rep] {len(conv)} coluna(s) numerica(s) com celulas em branco "
              "convertida(s) para numero (branco = ausente)")
        for c in conv:
            s = X[c].astype(str).str.strip()
            X[c] = pd.to_numeric(s.where(s != ""), errors="coerce")

    # Categoricas de baixa cardinalidade viram one-hot; o resto vira numerico.
    # is_numeric_dtype funciona no pandas 2 e no 3. No pandas 3 o texto tem
    # tipo "str", nao "object", e o teste antigo (dtype == object) falhava.
    texto = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
    cat = [c for c in texto if X[c].nunique() <= 32]
    high = [c for c in texto if c not in cat]
    if high:
        print(f"[rep] Descartando {len(high)} coluna(s) texto de alta cardinalidade")
        X = X.drop(columns=high)
    if cat:
        X = pd.get_dummies(X, columns=cat, dummy_na=False)

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.loc[:, X.notna().any()]
    return X, y, type_col


def sample_classes(y: pd.Series, n_total: int) -> pd.Index:
    """Indices de uma amostra de n_total linhas que preserva as classes raras.

    Classes com ate n_total // (numero de classes) registros entram inteiras.
    As maiores dividem o restante na proporcao original entre elas (sorteio).
    No caso binario isso reproduz a regra antiga: a classe benigna, rara,
    entra inteira e os ataques completam a amostra.
    Consequencia que voce precisa declarar na apresentacao: as classes raras
    ficam com proporcao MAIOR na amostra do que na base original.
    """
    counts = y.value_counts()
    limite = n_total // len(counts)
    pequenas = [c for c in counts.index if counts[c] <= limite]
    grandes = [c for c in counts.index if counts[c] > limite]

    resto = n_total - int(sum(counts[c] for c in pequenas))
    total_grandes = int(sum(counts[c] for c in grandes))
    exato = {c: resto * int(counts[c]) / total_grandes for c in grandes}
    cotas = {c: int(exato[c]) for c in grandes}
    # Distribui as linhas que sobraram do arredondamento pelas maiores fracoes.
    sobra = resto - sum(cotas.values())
    for c in sorted(grandes, key=lambda c: exato[c] - cotas[c], reverse=True)[:sobra]:
        cotas[c] += 1

    partes = [y.index[y == c] for c in pequenas]
    for c in grandes:
        sorteio = pd.Series(y.index[y == c]).sample(n=min(cotas[c], int(counts[c])),
                                                    random_state=RANDOM_STATE)
        partes.append(pd.Index(sorteio))
    keep = partes[0].append(partes[1:]) if len(partes) > 1 else partes[0]

    print(f"[rep] Amostra: {len(keep):,} linhas")
    for c in counts.index:
        n = int(cotas[c]) if c in cotas else int(counts[c])
        modo = "inteira" if c in pequenas else f"sorteada de {int(counts[c]):,}"
        print(f"[rep]    {str(c):<20} {n:>9,} ({100 * n / len(keep):6.3f}%)  {modo}")
    return keep


def models(balanced: bool):
    cw = "balanced" if balanced else None
    return {
        # Os cinco do artigo
        "Tree": DecisionTreeClassifier(max_depth=100, min_samples_leaf=1,
                                       min_samples_split=5, class_weight=cw,
                                       random_state=RANDOM_STATE),
        "NeuralNetwork": MLPClassifier(hidden_layer_sizes=(100,), activation="relu",
                                       solver="adam", alpha=1e-4, max_iter=200,
                                       early_stopping=True, random_state=RANDOM_STATE),
        "SVM": LinearSVC(C=1.0, class_weight=cw, max_iter=3000,
                         random_state=RANDOM_STATE),
        "kNN": KNeighborsClassifier(n_neighbors=5, metric="euclidean",
                                    weights="uniform", n_jobs=-1),
        # regularizacao ridge (L2), C=1, como na Secao 4.3.2 do artigo
        "LogisticRegression": LogisticRegression(C=1.0, max_iter=1000,
                                                 class_weight=cw,
                                                 random_state=RANDOM_STATE),
        # --- A EXTENSAO ---
        # Justificativa dupla: (1) nunca foi comparado nestas bases pelos autores;
        # (2) na Tabela 3 o widget Tree do Orange falhou por completo no BoT-IoT
        # ("Exhaustive binarization does not handle attributes with more than 16
        # values"), deixando a familia de arvores sem representante naquela base.
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=20, min_samples_leaf=2,
            class_weight="balanced_subsample" if balanced else None,
            n_jobs=-1, random_state=RANDOM_STATE),
    }


def save_results(res: pd.DataFrame, out: str) -> None:
    """Junta as linhas novas as existentes e reescreve o CSV inteiro.

    Linhas gravadas antes da coluna "target" existir sao todas binarias. A
    escrita passa por um arquivo temporario, para que uma falha no meio nao
    corrompa os resultados anteriores.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if os.path.exists(out):
        old = pd.read_csv(out)
        if "target" not in old.columns:
            old["target"] = "binary"
            print(f"[rep] {out}: coluna 'target' criada; as {len(old)} linhas "
                  "anteriores foram marcadas como 'binary'")
        res = pd.concat([old, res], ignore_index=True)
    cols = RESULT_COLS + [c for c in res.columns if c not in RESULT_COLS]
    tmp = out + ".tmp"
    res[cols].to_csv(tmp, index=False)
    os.replace(tmp, out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--name", default="dataset")
    ap.add_argument("--keep-identifiers", action="store_true")
    ap.add_argument("--multiclass", action="store_true",
                    help="alvo = tipo de ataque (como no artigo), em vez de "
                         "benigno x ataque")
    ap.add_argument("--balanced", action="store_true",
                    help="aplica class_weight (recomendado para BoT-IoT)")
    ap.add_argument("--sample", type=int, default=300000)
    ap.add_argument("--drop-cols", default="",
                    help="colunas a remover, separadas por virgula (ex.: IAT). "
                         "Indique isso tambem no --name, pois o CSV de "
                         "resultados nao guarda esta opcao")
    ap.add_argument("--out", default="results/replication.csv")
    args = ap.parse_args()
    target = "multiclass" if args.multiclass else "binary"

    df = load(args.input)
    print(f"[rep] {len(df):,} linhas, {len(df.columns)} colunas")

    drop_cols = [c for c in args.drop_cols.split(",") if c.strip()]
    X, y, type_col = prepare(df, args.keep_identifiers, drop_cols, args.multiclass)

    if args.multiclass:
        print(f"[rep] Alvo multiclasse: coluna '{type_col}', {y.nunique()} classes")
        for c, n in y.value_counts().items():
            print(f"[rep]    {c:<20} {n:>10,} ({100 * n / len(y):7.4f}%)")
    else:
        n_atk = int(y.sum())
        n_ben = len(y) - n_atk
        print(f"[rep] benigno={n_ben:,} ataque={n_atk:,} "
              f"| benigno representa {100 * n_ben / len(y):.4f}% da base")
        if n_ben / len(y) < 0.01:
            print("[rep] >>> A classe benigna e residual. Acuracia e F1 ponderado")
            print("[rep] >>> nao significam nada aqui. Olhe o F1 macro.")

    if args.sample and args.sample < len(X):
        keep = sample_classes(y, args.sample)
        X, y = X.loc[keep], y.loc[keep]

    benign_code = 0
    if args.multiclass:
        # Rotulos em texto quebram o MLPClassifier com early_stopping
        # (TypeError no np.isnan dentro do scikit-learn): vira codigo numerico.
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y), index=y.index)
        classes = list(le.classes_)
        nome_benigno = next((b for b in BENIGN_NAMES if b in classes), None)
        if nome_benigno is None:
            print(f"[rep] AVISO: nenhuma classe benigna ({BENIGN_NAMES}) entre "
                  f"{classes}; F1 benigno fica vazio")
            benign_code = None
        else:
            benign_code = classes.index(nome_benigno)
            print(f"[rep] F1 benigno = F1 da classe '{nome_benigno}'")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE)

    rows = []
    for name, clf in models(args.balanced).items():
        pipe = Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", clf),
        ])
        t0 = time.perf_counter()
        try:
            pipe.fit(X_tr, y_tr)
            pred = pipe.predict(X_te)
            f1w = f1_score(y_te, pred, average="weighted")
            f1m = f1_score(y_te, pred, average="macro")
            if not args.multiclass:
                f1b = f1_score(y_te, pred, pos_label=0, zero_division=0)
            elif benign_code is None:
                f1b = float("nan")
            else:
                f1b = f1_score(y_te, pred, labels=[benign_code], average=None,
                               zero_division=0)[0]
            status = "ok"
        except Exception as exc:
            f1w = f1m = f1b = float("nan")
            status = f"FALHOU: {type(exc).__name__}"
        dt = time.perf_counter() - t0

        rows.append({"dataset": args.name, "model": name, "target": target,
                     "f1_weighted": f1w, "f1_macro": f1m, "f1_benign": f1b,
                     "train_s": dt, "identifiers_kept": args.keep_identifiers,
                     "status": status})
        print(f"[rep] {name:<20} F1-pond={f1w:.4f}  F1-macro={f1m:.4f}  "
              f"F1-benigno={f1b:.4f}  ({dt:.1f}s) {status}")

    save_results(pd.DataFrame(rows), args.out)
    print(f"\n[rep] Resultados gravados em {args.out}")
    print("[rep] Compare a coluna f1_weighted com as Tabelas 3 e 4 do artigo")
    print("[rep] (rodadas --multiclass). A distancia ate f1_macro e o seu resultado.")


if __name__ == "__main__":
    main()
