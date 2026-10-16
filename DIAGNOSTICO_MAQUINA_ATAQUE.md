# Diagnóstico da máquina de ataque (HD Ubuntu)

Siga na ordem. Cada bloco tem um comando, o resultado esperado, e o que fazer em
cada desfecho. Você não precisa decidir nada no improviso: tudo que pode acontecer
está previsto abaixo.

O papel desta máquina é UM só: gerar tráfego de ataque (varredura e inundação)
contra os seus próprios dispositivos, na rede isolada. Ela não roda Python, não
roda o modelo, não faz parte do treino. Mantenha-a mínima.

---

## Antes do boot

- Desconecte o HD de qualquer outra função e ligue o PC por ele.
- Se possível, conecte o PC ao **roteador isolado por cabo de rede**. Com um Ubuntu
  de 4 anos, o driver de Wi-Fi é a parte com maior chance de dar trabalho; o cabo
  elimina essa variável. Deixe a internet fora — nada na porta WAN do roteador.
- Se você precisar de internet para instalar as ferramentas (provável), veja a
  nota sobre isso no Passo 3.

---

## Passo 1 — Identificar a versão

```bash
lsb_release -a
```

Anote a linha `Release`. Desfechos:

- **24.04, 22.04** → sistema atual, siga direto para o Passo 3. Ignore o Passo 2.
- **20.04** → fim do suporte padrão em abr/2025. Pode funcionar, pode não. Siga
  para o Passo 2.
- **18.04 ou anterior** → repositórios provavelmente desativados. Leia o Passo 2,
  mas já considere seriamente a reinstalação (Passo 5).

Aproveite e descubra o nome da sua interface de rede, você vai precisar dele:

```bash
ip -brief address
```

Isso lista as interfaces. A cabeada costuma aparecer como `eth0` ou algo como
`enp3s0`; a Wi-Fi como `wlan0` ou `wlp2s0`. Anote a que recebeu um IP do roteador
(vai ser um endereço tipo `192.168.x.x`).

---

## Passo 2 — Só se a versão for antiga: decidir consertar ou reinstalar

O teste real é o Passo 3 (`apt update`). Não tente adivinhar aqui — rode o Passo 3
e volte se ele falhar. Esta seção existe só para você já saber o que significa a
falha quando ela vier.

Um Ubuntu fora de suporte tem os repositórios normais desativados. O `apt update`
falha com mensagens como `404 Not Found` ou `does not have a Release file`. Duas
saídas, na ordem de preferência:

**Preferível: reinstalar (Passo 5).** Menos de uma hora, e você ganha anos de
suporte e drivers novos. Como o HD é dedicado a esta função, não há nada a perder.

**Alternativa: apontar para o arquivo morto.** O Ubuntu mantém as versões antigas
em `old-releases.ubuntu.com`. Reescrever o `sources.list` para lá costuma reviver o
`apt`. É um remendo — só vale se a reinstalação for inviável por algum motivo.

---

## Passo 3 — Testar os repositórios

```bash
sudo apt update
```

Este comando é o divisor de águas. Desfechos:

- **Terminou sem erro** (linhas `Hit`, `Get`, `Reading package lists... Done`) →
  os repositórios respondem. Siga para o Passo 4.
- **Erros `404` ou `Release file` ausente** → repositórios desativados. Vá para o
  Passo 5 (reinstalar) ou aplique o remendo do arquivo morto do Passo 2.
- **`Temporary failure resolving` ou nada acontece** → é falta de internet, não de
  repositório. Veja a nota abaixo.

> **Nota sobre internet para instalar.** Você precisa de internet uma única vez,
> para baixar `nmap` e `hping3`. Mas a rede de testes é isolada, sem internet. Três
> saídas: (a) conecte o Ubuntu à internet normal só para instalar, depois mova para
> a rede isolada; (b) se o roteador isolado puder ter internet temporariamente na
> WAN durante a semana 1, use isso e desconecte a WAN depois; (c) baixe os pacotes
> `.deb` em outra máquina e instale offline com `sudo dpkg -i`. A opção (a) é a mais
> simples. A rede só precisa ser isolada nas janelas de COLETA (semanas 6-7), não
> agora na instalação.

---

## Passo 4 — Instalar as ferramentas

```bash
sudo apt install -y nmap hping3
```

Confirme que instalaram:

```bash
nmap --version
sudo hping3 --version
```

- **Ambos respondem com versão** → ferramentas prontas. Siga para o Passo 6.
- **`hping3: command not found`** → em algumas versões o pacote tem outro nome ou
  está num repositório extra (`universe`). Rode
  `sudo add-apt-repository universe && sudo apt update` e tente instalar de novo.
- **`nmap` falha** → raro; quase sempre é o mesmo problema de repositório do
  Passo 3.

---

## Passo 5 — Reinstalar o Ubuntu (só se decidiu por isso)

Faça isto em outra máquina ou antes de mover o HD:

1. Baixe o **Ubuntu 24.04 LTS Desktop** do site oficial (ubuntu.com).
2. Grave num pendrive com o Rufus (no Windows) ou o balenaEtcher.
3. Dê boot pelo pendrive, escolha "Instalar Ubuntu", e instale **no HD dedicado**.
   Atenção redobrada na tela de particionamento: selecione o HD certo, não o disco
   do Windows.
4. Depois de instalar, volte ao Passo 1.

Não instale nada além do sistema base. Esta máquina não precisa de mais nada.

---

## Passo 6 — Teste de sanidade: os pacotes alcançam a rede?

Este é o teste que confirma a peça mais arriscada do projeto. Com o Ubuntu
conectado ao roteador isolado (idealmente por cabo):

Descubra o IP do roteador:

```bash
ip route | grep default
```

O endereço após `default via` é o roteador (algo como `192.168.0.1`). Rode uma
varredura simples contra ele:

```bash
nmap 192.168.0.1
```

(troque pelo IP real do seu roteador)

- **Listou portas abertas** (ex.: `80/tcp open`, `53/tcp open`) → o caminho de
  saída está livre. O `hping3` vai alcançar seus dispositivos. **Peça crítica
  confirmada.** Máquina de ataque pronta.
- **`Note: Host seems down` ou tudo `filtered`** → pode ser firewall do roteador
  (normal e ok — o teste real será contra o ESP32 e o Pi, não o roteador) OU
  problema de conexão. Faça o teste alternativo abaixo.

Teste alternativo, mais direto: descubra o IP de qualquer dispositivo já conectado
à rede-ilha (o Pi, por exemplo) e faça um ping:

```bash
ping -c 4 <ip-do-pi>
```

- **Respondeu** → a máquina enxerga a rede e conversa com os dispositivos. Pronto.
- **`Destination Host Unreachable` ou 100% packet loss** → problema de rede.
  Verifique: o cabo está no roteador certo? A interface pegou IP
  (`ip -brief address`)? O Pi está na mesma rede? Se estiver por Wi-Fi, tente
  cabo.

---

## Passo 7 — Guardar as informações para as semanas 6 e 7

Quando tudo passar, anote num lugar que você vá reencontrar em outubro:

```
Máquina de ataque (HD Ubuntu)
  Versão do Ubuntu : ______________________
  Interface de rede: ______________________  (eth0 / wlan0 / etc.)
  IP nesta máquina : ______________________
  IP do roteador   : ______________________
  nmap  instalado  : sim / não
  hping3 instalado : sim / não
  Teste de alcance : passou / falhou
```

Você vai precisar do IP do ESP32 e do Pi também, mas esses só existirão depois de
montá-los (semanas 4 e 5). Anote-os lá.

---

## O que você vai rodar de verdade nas semanas 6 e 7

Só para você ver onde isto tudo desemboca — **não rode agora**, é referência para
depois, e sempre contra os SEUS dispositivos na rede isolada.

Varredura de portas (gera tráfego de categoria *scanning* / *reconnaissance*):

```bash
sudo nmap -sS <ip-do-esp32-ou-pi>
```

Inundação SYN (gera tráfego de categoria *DoS* / *DDoS*):

```bash
sudo hping3 -S --flood -p 1883 <ip-do-alvo>
```

O `--flood` manda o mais rápido possível; use com parcimônia e por poucos segundos,
o suficiente para gerar os fluxos de ataque na janela de coleta. O `detect.py`
rodando no Pi com `--phase attack` grava tudo com o rótulo correto.

---

## Resumo de uma linha

Dê boot → `lsb_release -a` → `sudo apt update`. Se passar, instale nmap e hping3 e
faça o `nmap` no roteador. Se `apt update` falhar, reinstale o 24.04. Ou funciona,
ou você reinstala; não há caminho em que você fica preso.
