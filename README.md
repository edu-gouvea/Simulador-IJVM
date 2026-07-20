# Simulador da Mic-1 Modificada

> Projeto acadêmico desenvolvido para a disciplina de **Arquitetura de Computadores II**  
> Universidade Federal da Paraíba (UFPB) — Profª. Sarah Pontes Madruga

---

## Sumário

- [Descrição](#descrição)
- [Arquitetura Simulada](#arquitetura-simulada)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Etapa 1 — ULA de 6 Bits de Controle](#etapa-1--ula-de-6-bits-de-controle)
- [Etapa 2 — Caminho de Dados da Mic-1](#etapa-2--caminho-de-dados-da-mic-1)
  - [Tarefa 1 — ULA de 8 Bits de Controle (SLL8 / SRA1 / N / Z)](#tarefa-1--ula-de-8-bits-de-controle-sll8--sra1--n--z)
  - [Tarefa 2 — Registradores, Decodificador e Seletor](#tarefa-2--registradores-decodificador-e-seletor)
- [Etapa 3 — Acesso à Memória](#etapa-3--acesso-à-memória)
  - [Tarefa 1 — Leitura e Escrita na Memória de Dados](#tarefa-1--leitura-e-escrita-na-memória-de-dados)
- [Entregável — ILOAD, DUP e BIPUSH](#entregável--iload-dup-e-bipush)
- [Como Executar](#como-executar)
- [Formato dos Arquivos de Entrada](#formato-dos-arquivos-de-entrada)
- [Formato da Saída](#formato-da-saída)
- [Exemplo Completo — Etapa 1](#exemplo-completo--etapa-1)
- [Exemplo Completo — Etapa 2, Tarefa 1](#exemplo-completo--etapa-2-tarefa-1)
- [Exemplo Completo — Etapa 2, Tarefa 2](#exemplo-completo--etapa-2-tarefa-2)
- [Exemplo Completo — Etapa 3, Tarefa 1](#exemplo-completo--etapa-3-tarefa-1)
- [Exemplo Completo — Entregável](#exemplo-completo--entregável)
- [Requisitos](#requisitos)
- [Observações](#observações)

---

## Descrição

Este projeto implementa um **simulador da microarquitetura Mic-1 modificada**, baseada na máquina descrita por Tanenbaum em *Organização Estruturada de Computadores*. O simulador é desenvolvido em Python e executa programas de microinstruções, reproduzindo o comportamento interno da ULA (Unidade Lógica e Aritmética) e do caminho de dados da Mic-1.

O projeto é dividido em etapas incrementais, cada uma adicionando componentes e funcionalidades ao simulador.

---

## Arquitetura Simulada

A Mic-1 modificada opera com:

- Palavras de **32 bits** (sem sinal, complemento a dois)
- **ULA** controlada, na Etapa 1, por **6 bits de controle**: `F0 F1 ENA ENB INVA INC`
- **ULA** controlada, a partir da Etapa 2, por **8 bits de controle**: `SLL8 SRA1 F0 F1 ENA ENB INVA INC`
- Registradores internos `A` e `B` para operandos
- Registrador `S` (e, a partir da Etapa 2, sua versão deslocada `Sd`) para o resultado
- Bit de carry-out (`co`) e, a partir da Etapa 2, as flags `N` (negativo) e `Z` (zero)
- A partir da Etapa 2, um conjunto de **10 registradores** (`H`, `OPC`, `TOS`, `CPP`, `LV`, `SP`, `PC`, `MDR`, `MAR` de 32 bits, e `MBR` de 8 bits), um **decodificador de 4 bits** para o barramento B e um **seletor de 9 bits** para o barramento C
- A partir da Etapa 3, uma **memória de dados** de 8 endereços (32 bits cada), acessada por `MAR` (endereço) e `MDR` (dado lido/escrito), com **2 bits de controle** (`WRITE`, `READ`)

### Bits de Controle da ULA (Etapa 1 — 6 bits)

| Bit  | Nome | Função |
|------|------|--------|
| 0    | F0   | Seletor de função (LSB) |
| 1    | F1   | Seletor de função (MSB) |
| 2    | ENA  | Habilita entrada A |
| 3    | ENB  | Habilita entrada B |
| 4    | INVA | Inverte A antes da operação |
| 5    | INC  | Força carry-in = 1 (incremento) |

### Bits de Controle da ULA (Etapa 2 — 8 bits)

| Bit  | Nome | Função |
|------|------|--------|
| 0    | SLL8 | Desloca a saída `S` 8 bits para a esquerda (lógico) |
| 1    | SRA1 | Desloca a saída `S` 1 bit para a direita (aritmético, preserva o sinal) |
| 2    | F0   | Seletor de função (LSB) |
| 3    | F1   | Seletor de função (MSB) |
| 4    | ENA  | Habilita entrada A |
| 5    | ENB  | Habilita entrada B |
| 6    | INVA | Inverte A antes da operação |
| 7    | INC  | Força carry-in = 1 (incremento) |

> `SLL8` e `SRA1` nunca ficam ativos ao mesmo tempo. O deslocamento é aplicado **depois** do cálculo de `S` pelo núcleo da ULA, gerando a saída deslocada `Sd`.

### Funções da ULA (F1 F0)

| F1 | F0 | Operação |
|----|----|----------|
| 0  | 0  | AND (A & B) |
| 0  | 1  | OR  (A \| B) |
| 1  | 0  | NOT A |
| 1  | 1  | Soma (A + B + carry_in) |

> A combinação de `INVA` e `INC` com a soma permite derivar operações como subtração e passagem de `B`.

### Flags de Saída (a partir da Etapa 2)

| Flag | Significado |
|------|-------------|
| `co` (Vai-um) | 1 se houve estouro (carry-out) na soma |
| `N`  | 1 se a saída deslocada `Sd`, interpretada com sinal, é negativa (bit mais significativo = 1) |
| `Z`  | 1 se a saída deslocada `Sd` é igual a zero |

---

## Estrutura do Projeto

```
mic1/
├── mic1.py                            # Simulador principal (etapa1, etapa2_tarefa1, etapa2_tarefa2)
├── programa_etapa1.txt                # Programa de entrada da Etapa 1
├── saida_etapa1.txt                   # Saída gerada pelo simulador (Etapa 1)
├── programa_etapa2_tarefa1.txt        # Programa de entrada da Etapa 2 / Tarefa 1 (ULA 8 bits)
├── saida_etapa2_tarefa1.txt           # Saída gerada pelo simulador (Etapa 2 / Tarefa 1)
├── registradores_etapa2_tarefa2.txt   # Estado inicial dos registradores (Etapa 2 / Tarefa 2)
├── programa_etapa2_tarefa2.txt        # Programa de entrada da Etapa 2 / Tarefa 2 (caminho de dados)
├── saida_etapa2_tarefa2.txt           # Saída gerada pelo simulador (Etapa 2 / Tarefa 2)
├── registradores_etapa3_tarefa1.txt   # Estado inicial dos registradores (Etapa 3 / Tarefa 1)
├── dados_etapa3_tarefa1.txt           # Estado inicial da memória de dados (Etapa 3 / Tarefa 1)
├── programa_etapa3_tarefa1.txt        # Programa de entrada da Etapa 3 / Tarefa 1 (acesso à memória)
├── saida_etapa3_tarefa1.txt           # Saída gerada pelo simulador (Etapa 3 / Tarefa 1)
├── registradores_entregavel.txt       # Estado inicial dos registradores (Entregável)
├── dados_entregavel.txt               # Estado inicial da memória de dados (Entregável)
├── instrucoes_entregavel.txt          # Instruções ISA da IJVM: ILOAD / DUP / BIPUSH (Entregável)
├── saida_entregavel.txt               # Saída gerada pelo simulador (Entregável)
└── README.md
```

---

## Etapa 1 — ULA de 6 Bits de Controle

Na Etapa 1, o simulador lê uma sequência de palavras de **6 bits** (os sinais de controle da ULA) e executa cada microinstrução com os operandos fixos:

- `A` inicializado como `0xFFFFFFFF` (all-ones, 32 bits)
- `B` inicializado como `0x00000001`

A cada ciclo:
1. Os 6 bits de controle são decodificados.
2. A ULA calcula `S` e `carry_out`.
3. `A` é atualizado com o valor de `S` (realimentação).
4. `B` permanece fixo.

O programa termina quando não há mais instruções (EOP — End of Program).

---

## Etapa 2 — Caminho de Dados da Mic-1

A Etapa 2 evolui a ULA da Etapa 1 e introduz o caminho de dados da Mic-1, com registradores, barramentos e a lógica de decodificação/seleção que conecta tudo à ULA. Ela é dividida em duas tarefas.

### Tarefa 1 — ULA de 8 Bits de Controle (SLL8 / SRA1 / N / Z)

A ULA da Etapa 1 é estendida para receber uma palavra de controle de **8 bits**:

```
SLL8 SRA1 F0 F1 ENA ENB INVA INC
```

O núcleo de 6 bits (`F0 F1 ENA ENB INVA INC`) funciona exatamente como na Etapa 1, calculando `S` e `co`. Em seguida:

1. Se `SLL8 = 1`, `S` é deslocado **logicamente 8 bits à esquerda** (zeros entram pela direita, os 8 bits mais significativos são descartados), gerando `Sd`.
2. Se `SRA1 = 1`, `S` é deslocado **aritmeticamente 1 bit à direita** (o bit de sinal é preservado), gerando `Sd`.
3. Se nenhum dos dois estiver ativo, `Sd = S`.
4. As flags `N` e `Z` são calculadas sobre `Sd`.

O teste desta tarefa segue a mesma estrutura da Etapa 1: `A` inicia em `0xFFFFFFFF`, `B` é fixo em `1`, e `A` é realimentado com `Sd` a cada ciclo.

### Tarefa 2 — Registradores, Decodificador e Seletor

Nesta tarefa é implementado o restante do caminho de dados da Mic-1, sem envolver ainda acesso à memória (isso fica para a Etapa 3):

- **10 registradores**: `H`, `OPC`, `TOS`, `CPP`, `LV`, `SP`, `PC`, `MDR` e `MAR` (32 bits cada) e `MBR` (8 bits).
- Um **decodificador de 4 bits**, que escolhe qual dos 9 registradores comanda o barramento B (entrada B da ULA).
- Um **seletor de 9 bits**, que habilita um ou mais dos 9 registradores de 32 bits a serem escritos com a saída da ULA (barramento C).
- A entrada **A** da ULA é sempre o valor armazenado em `H`.

**Mapeamento do decodificador de 4 bits (barramento B):**

| Registrador | OPC | TOS | CPP | LV | SP | MBRU | MBR | PC | MDR |
|-------------|-----|-----|-----|----|----|------|-----|----|----|
| Saída habilitada | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |

> `MBR` é estendido com o **bit de sinal** até 32 bits; `MBRU` é a mesma informação, mas estendida com **zeros**.

**Mapeamento do seletor de 9 bits (barramento C):**

| Registrador | H | OPC | TOS | CPP | LV | SP | PC | MDR | MAR |
|-------------|---|-----|-----|-----|----|----|----|-----|-----|
| Bit | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |

A partir desta tarefa, cada linha do programa é uma instrução de **21 bits**, organizada como:

```
Controle da ULA (8 bits) | Controle do barramento C (9 bits) | Controle do barramento B (4 bits)
```

A cada ciclo:
1. `A = H` e `B` = valor do registrador indicado pelo decodificador de 4 bits (ambos lidos **antes** de qualquer escrita do ciclo).
2. A ULA calcula `Sd`, `co`, `N` e `Z`.
3. `Sd` é escrito em **todos** os registradores habilitados pelo seletor de 9 bits.

> **Observação:** um exemplo do enunciado indica o registrador `LV` para os bits `0100`, mas, pela tabela oficial de mapeamento do decodificador, `0100 = 4` corresponde a `SP` (o valor `5` é que corresponde a `LV`). O simulador segue a tabela de mapeamento, que é a fonte mais confiável (é a mesma usada no exemplo do `MBR`, que bate exatamente com o enunciado).

---

## Etapa 3 — Acesso à Memória

A Etapa 3 adiciona à Mic-1 o acesso à **memória de dados**, permitindo que os registradores `MAR` (endereço) e `MDR` (dado) leiam e escrevam valores persistidos fora dos registradores.

### Tarefa 1 — Leitura e Escrita na Memória de Dados

A microinstrução cresce de 21 para **23 bits**, com o novo campo de memória inserido entre o controle do barramento C e o controle do barramento B:

```
Controle da ULA (8) | Controle do barramento C (9) | Memória (2) | Controle do barramento B (4)
```

Os 2 bits de memória são organizados como:

```
WRITE READ
X1    X0
```

| WRITE | READ | Operação |
|-------|------|----------|
| 1 | 0 | O valor de `MDR` é **escrito** na posição de `dados.txt` apontada por `MAR` |
| 0 | 1 | O valor da posição de `dados.txt` apontada por `MAR` é **lido** e copiado para `MDR` |
| 0 | 0 | Nenhuma operação de memória |
| 1 | 1 | Caso especial (**fetch**), usado apenas na tarefa **Entregável** (para carregar o argumento de `BIPUSH` em `MBR`/`H`); nesta tarefa (Tarefa 1) o simulador apenas registra a ocorrência no log, sem acessar `dados.txt` |

A memória de dados possui **8 endereços** (linhas), cada um armazenando uma palavra de **32 bits**. O endereço efetivo usado é o valor de `MAR` (se `MAR` estiver fora da faixa `[0, 7]`, o simulador usa `MAR mod 8` e sinaliza um aviso no log, para manter a execução robusta mesmo diante de um endereço inesperado).

**Ordem de execução dentro do ciclo** (conforme o enunciado):

1. A ULA calcula `Sd`, `co`, `N`, `Z` (igual à Tarefa 2 da Etapa 2).
2. Os registradores habilitados pelo seletor de 9 bits são escritos com `Sd` (barramento C).
3. **Somente depois disso**, a operação de memória (`WRITE`/`READ`) é realizada, usando os valores já atualizados de `MAR` e/ou `MDR`.

Esse detalhe de ordenação é importante: em uma mesma microinstrução, um registrador pode ser atualizado pela ULA e, no mesmo ciclo, ser usado imediatamente como endereço (`MAR`) ou dado (`MDR`) da operação de memória — como no exemplo do enunciado em que `SP` e `MAR` são escritos com `SP+1` e, na sequência, esse novo `MAR` já é usado para uma leitura.

---

## Entregável — ILOAD, DUP e BIPUSH

O entregável final reconhece instruções de alto nível da ISA da IJVM em um arquivo `.txt`, **traduz cada uma dinamicamente** em sua sequência de microinstruções de 23 bits e as executa sobre o mesmo caminho de dados e memória implementados nas etapas anteriores.

### Instruções suportadas

**`ILOAD x`** — carrega no topo da pilha a variável local de índice `x` (offset a partir de `LV`):

```
H = LV
H = H+1        ← repetida x vezes
MAR = H; rd
MAR = SP = SP+1; wr
TOS = MDR
```

O número de microinstruções `H = H+1` é gerado **dinamicamente** de acordo com o argumento `x` (para `x = 0`, nenhuma é gerada).

**`DUP`** — duplica o valor no topo da pilha:

```
MAR = SP = SP+1
MDR = TOS; wr
```

**`BIPUSH byte`** — empilha um byte arbitrário fornecido como argumento:

```
SP = MAR = SP+1
fetch
MDR = TOS = H; wr
```

A microinstrução `fetch` é o caso especial de memória descrito na Tarefa 1 da Etapa 3 (`WRITE = READ = 1`): os 8 bits que normalmente controlam a ULA passam a carregar o **argumento literal de `BIPUSH`**. Quando esse padrão ocorre, o simulador:

1. Copia o byte diretamente para `MBR`.
2. Copia `MBR` para `H`, com **extensão de zeros** até 32 bits — **sem passar pela ULA**.
3. Não realiza nenhuma leitura/escrita em `dados.txt` neste ciclo.

### Formato do arquivo de instruções

Uma instrução por linha:

```
ILOAD <x>
DUP
BIPUSH <byte>
```

`<x>` é um inteiro (índice da variável local). `<byte>` pode ser uma palavra binária de 8 bits (ex.: `00010100`) ou um inteiro decimal/hexadecimal, que é truncado para 8 bits.

### O que o log do entregável mostra

Para cada instrução de alto nível, e para cada microinstrução gerada dentro dela, o log traz:

- O valor de todos os registradores no início e no fim da microinstrução.
- O registrador que comanda o barramento B (quando aplicável).
- Os registradores habilitados no barramento C.
- O valor de `Sd`, `co`, `N`, `Z` (ou, no caso do fetch, o byte carregado em `MBR`/`H`).
- O estado da memória de dados ao final de cada instrução de alto nível.

Além disso, o log mostra o estado da memória de dados **antes** da execução do programa e o estado final de registradores e memória ao término de todas as instruções.

---

## Como Executar

### Pré-requisitos

- Python 3.7 ou superior
- Nenhuma dependência externa

### Sintaxe

```bash
# Etapa 1 — ULA de 6 bits
python3 mic1.py etapa1 <arquivo_programa> <arquivo_saida>

# Etapa 2, Tarefa 1 — ULA de 8 bits (SLL8 / SRA1 / N / Z)
python3 mic1.py etapa2_tarefa1 <arquivo_programa> <arquivo_saida>

# Etapa 2, Tarefa 2 — Caminho de dados completo
python3 mic1.py etapa2_tarefa2 <arquivo_registradores> <arquivo_programa> <arquivo_saida>

# Etapa 3, Tarefa 1 — Acesso à memória de dados
python3 mic1.py etapa3_tarefa1 <arquivo_registradores> <arquivo_dados> <arquivo_programa> <arquivo_saida>

# Entregável — ILOAD x, DUP, BIPUSH byte
python3 mic1.py entregavel <arquivo_registradores> <arquivo_dados> <arquivo_instrucoes> <arquivo_saida>
```

### Parâmetros

| Parâmetro              | Descrição |
|-------------------------|-----------|
| `etapa1`                 | Modo de execução da Etapa 1 (ULA de 6 bits) |
| `etapa2_tarefa1`          | Modo de execução da Etapa 2 / Tarefa 1 (ULA de 8 bits) |
| `etapa2_tarefa2`          | Modo de execução da Etapa 2 / Tarefa 2 (caminho de dados completo) |
| `etapa3_tarefa1`          | Modo de execução da Etapa 3 / Tarefa 1 (acesso à memória de dados) |
| `entregavel`              | Modo de execução do Entregável (tradução e execução de `ILOAD x`, `DUP`, `BIPUSH byte`) |
| `<arquivo_registradores>` | (Em `etapa2_tarefa2`, `etapa3_tarefa1` e `entregavel`) Arquivo `.txt` com o estado inicial dos registradores |
| `<arquivo_dados>`         | (Em `etapa3_tarefa1` e `entregavel`) Arquivo `.txt` com o estado inicial da memória de dados (8 endereços) |
| `<arquivo_programa>`      | (Em `etapa1`, `etapa2_tarefa1`, `etapa2_tarefa2`, `etapa3_tarefa1`) Arquivo `.txt` com as microinstruções a serem executadas |
| `<arquivo_instrucoes>`    | (Somente `entregavel`) Arquivo `.txt` com instruções da ISA da IJVM (`ILOAD x` / `DUP` / `BIPUSH byte`) |
| `<arquivo_saida>`         | Caminho para o arquivo `.txt` onde a saída será gravada |

### Exemplos

```bash
python3 mic1.py etapa1 programa_etapa1.txt saida_etapa1.txt

python3 mic1.py etapa2_tarefa1 programa_etapa2_tarefa1.txt saida_etapa2_tarefa1.txt

python3 mic1.py etapa2_tarefa2 registradores_etapa2_tarefa2.txt programa_etapa2_tarefa2.txt saida_etapa2_tarefa2.txt

python3 mic1.py etapa3_tarefa1 registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt programa_etapa3_tarefa1.txt saida_etapa3_tarefa1.txt

python3 mic1.py entregavel registradores_entregavel.txt dados_entregavel.txt instrucoes_entregavel.txt saida_entregavel.txt
```

---

## Formato dos Arquivos de Entrada

Em todos os modos, linhas em branco e linhas iniciadas com `#` são ignoradas (comentários).

### Etapa 1

O arquivo de programa contém **uma instrução por linha**, onde cada instrução é uma palavra de **6 bits** (apenas `0` e `1`).

**Exemplo — `programa_etapa1.txt`:**

```
# Exemplo de programa para a Etapa 1
111100
110101
110100
011100
```

### Etapa 2 — Tarefa 1

O arquivo de programa contém **uma instrução por linha**, onde cada instrução é uma palavra de **8 bits** (`SLL8 SRA1 F0 F1 ENA ENB INVA INC`).

**Exemplo — `programa_etapa2_tarefa1.txt`:**

```
# SLL8 SRA1 F0 F1 ENA ENB INVA INC
00111100
10111100
01111100
00011100
```

### Etapa 2 — Tarefa 2

Dois arquivos são necessários:

**1. Arquivo de registradores** (`registradores_etapa2_tarefa2.txt`) — define o estado inicial de cada registrador, uma atribuição `REGISTRADOR=valor` por linha. Os valores podem ser decimais ou usar os prefixos `0x` (hexadecimal) / `0b` (binário).

```
# Estado inicial dos registradores
H=0
OPC=0
TOS=0
CPP=0
LV=0
SP=10
PC=0
MDR=5
MAR=0
MBR=0
```

**2. Arquivo de programa** (`programa_etapa2_tarefa2.txt`) — uma instrução de **21 bits** por linha, no formato `ULA(8) | Barramento C(9) | Barramento B(4)`.

```
# ULA(8) | Barramento C(9) | Barramento B(4)
001101001010000000000
001111000000000100100
```

> Qualquer linha com formato inválido (número de bits incorreto, ou caracteres diferentes de `0`/`1`) é reportada como erro no log de saída, e o simulador avança para o próximo ciclo.

### Etapa 3 — Tarefa 1

Três arquivos são necessários:

**1. Arquivo de registradores** — mesmo formato usado na Etapa 2 / Tarefa 2.

**2. Arquivo de memória de dados** (`dados_etapa3_tarefa1.txt`) — até 8 linhas, uma por endereço (0 a 7). Cada linha pode ser uma palavra binária de 32 bits ou um inteiro (decimal, `0x...` ou `0b...`). Endereços não informados são inicializados com zero.

```
# Memória de dados — endereços 0..7
0
0
0
0
0
0
0
0
```

**3. Arquivo de programa** (`programa_etapa3_tarefa1.txt`) — uma instrução de **23 bits** por linha, no formato `ULA(8) | Barramento C(9) | Memória(2) | Barramento B(4)`.

```
# ULA(8) | Barramento C(9) | Memória(2) | Barramento B(4)
00111100000000010100100
00110101000001001010100
```

---

## Formato da Saída

A saída é gerada tanto no **terminal** quanto no **arquivo de saída** especificado.

### Etapa 1

```
b = <valor de B em 32 bits binários>
a = <valor de A em 32 bits binários>

Start of Program
============================================================
Cycle <N>

PC = <N>
IR = <instrução de 6 bits>
b = <B em binário>
a = <A em binário>
s = <S em binário>
co = <carry-out: 0 ou 1>
============================================================
Cycle <N+1>
...
============================================================
Cycle <último+1>

PC = <último+1>
> Line is empty, EOP.
```

### Etapa 2 — Tarefa 1

Estrutura idêntica à da Etapa 1, mas com `IR` de 8 bits, a saída deslocada `sd` no lugar de `s`, e as flags `n` e `z` adicionadas:

```
b  = <B em binário>
a  = <A em binário>
sd = <Sd em binário>
co = <carry-out: 0 ou 1>
n  = <flag N: 0 ou 1>
z  = <flag Z: 0 ou 1>
```

### Etapa 2 — Tarefa 2

Para cada ciclo, o log traz o estado de **todos** os registradores no início e no fim do ciclo, o registrador que comanda o barramento B, os registradores habilitados no barramento C, e os valores de `Sd`, `co`, `N` e `Z`:

```
Cycle <N>

IR = <instrução de 21 bits>

--- Registradores no início do ciclo ---
  H    = ...
  OPC  = ...
  ...

Barramento B comandado por: <nome do registrador>
A (= H)        = ...
B (<registrador>) = ...
Controle ULA (SLL8 SRA1 F0 F1 ENA ENB INVA INC) = <8 bits>
Sd = ...
Vai-um = <0 ou 1>   N = <0 ou 1>   Z = <0 ou 1>
Registradores habilitados no barramento C: <lista, ou "(nenhum)">

--- Registradores no fim do ciclo ---
  H    = ...
  OPC  = ...
  ...
```

### Etapa 3 — Tarefa 1

Estrutura idêntica à da Etapa 2 / Tarefa 2, acrescida do controle de memória e do estado da memória de dados no início e no fim de cada ciclo:

```
Cycle <N>

IR = <instrução de 23 bits>

--- Registradores no início do ciclo ---
  ...

Barramento B comandado por: <nome do registrador>
A (= H)        = ...
B (<registrador>) = ...
Controle ULA (SLL8 SRA1 F0 F1 ENA ENB INVA INC) = <8 bits>
Sd = ...
Vai-um = <0 ou 1>   N = <0 ou 1>   Z = <0 ou 1>
Registradores habilitados no barramento C: <lista, ou "(nenhum)">

Controle de memória (WRITE READ) = <2 bits>
Operação de memória: WRITE  →  dados[<endereço>] = MDR = ...
   (ou: READ  →  MDR = dados[<endereço>] = ...)
   (ou: nenhuma, se WRITE=0 e READ=0)

--- Registradores no fim do ciclo ---
  ...

--- Memória de dados no fim do ciclo ---
  [0] = ...
  [1] = ...
  ...
  [7] = ...
```

---

## Exemplo Completo — Etapa 1

### Entrada (`programa_etapa1.txt`)

```
111100
110101
110100
011100
```

### Saída esperada

```
b = 00000000000000000000000000000001
a = 11111111111111111111111111111111

Start of Program
============================================================
Cycle 1

PC = 1
IR = 111100
b = 00000000000000000000000000000001
a = 11111111111111111111111111111111
s = 00000000000000000000000000000000
co = 1
============================================================
Cycle 2

PC = 2
IR = 110101
b = 00000000000000000000000000000001
a = 00000000000000000000000000000000
s = 00000000000000000000000000000010
co = 0
============================================================
Cycle 3

PC = 3
IR = 110100
b = 00000000000000000000000000000001
a = 00000000000000000000000000000000
s = 00000000000000000000000000000001
co = 0
============================================================
Cycle 4

PC = 4
IR = 011100
b = 00000000000000000000000000000001
a = 11111111111111111111111111111111
s = 11111111111111111111111111111111
co = 0
============================================================
Cycle 5

PC = 5
> Line is empty, EOP.
```

### Decodificação das instruções

| Ciclo | IR     | F1F0 | ENA | ENB | INVA | INC | Operação realizada |
|-------|--------|------|-----|-----|------|-----|--------------------|
| 1     | 111100 | 11   | 1   | 1   | 0    | 0   | A + B (0xFFFFFFFF + 1 = 0, co=1) |
| 2     | 110101 | 11   | 0   | 1   | 0    | 1   | B + 1 (0 + 1 + 1 = 2) |
| 3     | 110100 | 11   | 0   | 1   | 0    | 0   | B (passa B: 1) |
| 4     | 011100 | 01   | 1   | 1   | 1    | 0   | OR(NOT A, B) → NOT(1) \| 1 = 0xFFFFFFFE \| 1 = 0xFFFFFFFF |

---

## Exemplo Completo — Etapa 2, Tarefa 1

### Entrada (`programa_etapa2_tarefa1.txt`)

```
00111100
10111100
01111100
00011100
```

### Saída esperada

```
b = 00000000000000000000000000000001
a = 11111111111111111111111111111111

Start of Program
============================================================
Cycle 1

PC = 1
IR = 00111100
b  = 00000000000000000000000000000001
a  = 11111111111111111111111111111111
sd = 00000000000000000000000000000000
co = 1
n  = 0
z  = 1
============================================================
Cycle 2

PC = 2
IR = 10111100
b  = 00000000000000000000000000000001
a  = 00000000000000000000000000000000
sd = 00000000000000000000000100000000
co = 0
n  = 0
z  = 0
============================================================
Cycle 3

PC = 3
IR = 01111100
b  = 00000000000000000000000000000001
a  = 00000000000000000000000100000000
sd = 00000000000000000000000010000000
co = 0
n  = 0
z  = 0
============================================================
Cycle 4

PC = 4
IR = 00011100
b  = 00000000000000000000000000000001
a  = 00000000000000000000000010000000
sd = 11111111111111111111111101111111
co = 0
n  = 1
z  = 0
============================================================
Cycle 5

PC = 5
> Line is empty, EOP.
```

### Decodificação das instruções

| Ciclo | IR (8 bits) | SLL8 | SRA1 | F1F0 | Operação | `Sd` | Flags |
|-------|-------------|------|------|------|----------|------|-------|
| 1 | `00111100` | 0 | 0 | 11 (soma) | `A + B` = `0xFFFFFFFF + 1` | `0x00000000` | `co=1`, `z=1` |
| 2 | `10111100` | 1 | 0 | 11 (soma) | `(A + B) << 8` = `1 << 8` | `0x00000100` | — |
| 3 | `01111100` | 0 | 1 | 11 (soma) | `(A + B) >>> 1` (aritmético) = `257 >> 1` | `0x00000080` | — |
| 4 | `00011100` | 0 | 0 | 10 (NOT A) | `NOT A` = `~0x00000080` | `0xFFFFFF7F` | `n=1` |

---

## Exemplo Completo — Etapa 2, Tarefa 2

### Entrada (`registradores_etapa2_tarefa2.txt`)

```
H=0
OPC=0
TOS=0
CPP=0
LV=0
SP=10
PC=0
MDR=5
MAR=0
MBR=0
```

### Entrada (`programa_etapa2_tarefa2.txt`)

```
001101001010000000000
001111000000000100100
```

### Decodificação das instruções

| Ciclo | IR (21 bits) | ULA (8) | C (9) | B (4) | Barramento B | Operação | Registradores escritos |
|-------|---------------|---------|-------|-------|--------------|----------|-------------------------|
| 1 | `001101001010000000000` | `00110100` | `101000000` | `0000` | `MDR` (=5) | `Sd = B = MDR` | `H`, `TOS` → `5` |
| 2 | `001111000000000100100` | `00111100` | `000000010` | `0100` | `SP` (=10) | `Sd = A + B = H + SP` | `MDR` → `15` |

### Saída esperada (resumo)

Ao final da execução:

```
H   = 5
OPC = 0
TOS = 5
CPP = 0
LV  = 0
SP  = 10
PC  = 0
MDR = 15
MAR = 0
MBR = 0
```

> O log completo, com o estado de todos os registradores no início e no fim de cada ciclo, é gravado em `saida_etapa2_tarefa2.txt`.

---

## Exemplo Completo — Etapa 3, Tarefa 1

### Entrada (`registradores_etapa3_tarefa1.txt`)

```
H=0
OPC=0
TOS=0
CPP=0
LV=8
SP=3
PC=0
MDR=0
MAR=0
MBR=0
```

### Entrada (`dados_etapa3_tarefa1.txt`)

```
0
0
0
0
0
0
0
0
```

### Entrada (`programa_etapa3_tarefa1.txt`)

```
00111100000000010100100
00110101000001001010100
```

### Decodificação das instruções

| Ciclo | IR (23 bits) | ULA (8) | C (9) | MEM (2) | B (4) | Barramento B | Operação | Registradores escritos | Operação de memória |
|-------|---------------|---------|-------|---------|-------|--------------|----------|--------------------------|----------------------|
| 1 | `00111100000000010100100` | `00111100` | `000000010` | `10` | `0100` | `SP` (=3) | `Sd = A + B = H + SP = 0 + 3` | `MDR` → `3` | `WRITE`: `dados[MAR=0] = MDR = 3` |
| 2 | `00110101000001001010100` | `00110101` | `000001001` | `01` | `0100` | `SP` (=3) | `Sd = B + 1 = SP + 1 = 4` | `SP` → `4`, `MAR` → `4` | `READ`: `MDR = dados[MAR=4] = 0` |

> Repare que, no ciclo 2, a operação de memória usa o valor de `MAR` **já atualizado** pela ULA/barramento C no mesmo ciclo (`MAR = 4`), conforme a ordem de execução especificada no enunciado.

### Saída esperada (resumo)

Ao final da execução:

```
Registradores:
  H   = 0
  OPC = 0
  TOS = 0
  CPP = 0
  LV  = 8
  SP  = 4
  PC  = 0
  MDR = 0
  MAR = 4
  MBR = 0

Memória de dados:
  [0] = 3
  [1..7] = 0
```

> O log completo, com o estado de todos os registradores e da memória no início e no fim de cada ciclo, é gravado em `saida_etapa3_tarefa1.txt`.

---

## Exemplo Completo — Entregável

### Entrada (`registradores_entregavel.txt`)

```
H=0
OPC=0
TOS=0
CPP=0
LV=2
SP=4
PC=0
MDR=0
MAR=0
MBR=0
```

### Entrada (`dados_entregavel.txt`)

```
0
0
0
42
0
0
0
0
```

> `LV = 2` (base do quadro de variáveis locais) e `dados[3] = dados[LV+1] = 42` simula a variável local de índice 1 já armazenada na memória.

### Entrada (`instrucoes_entregavel.txt`)

```
ILOAD 1
DUP
BIPUSH 00010100
```

### Rastreamento da execução

**`ILOAD 1`** — carrega a variável local 1 (offset `LV+1`) no topo da pilha:

| Microinstrução | Efeito | Estado após |
|---|---|---|
| `H = LV` | `H = 2` | `H=2` |
| `H = H+1` | `H = 3` (repetida 1 vez, pois `x=1`) | `H=3` |
| `MAR = H; rd` | `MAR = 3`; lê `dados[3] = 42` para `MDR` | `MAR=3, MDR=42` |
| `MAR = SP = SP+1; wr` | `SP = 5`, `MAR = 5`; escreve `MDR=42` em `dados[5]` | `SP=5, MAR=5, dados[5]=42` |
| `TOS = MDR` | `TOS = 42` | `TOS=42` |

**`DUP`** — duplica o topo da pilha:

| Microinstrução | Efeito | Estado após |
|---|---|---|
| `MAR = SP = SP+1` | `SP = 6`, `MAR = 6` | `SP=6, MAR=6` |
| `MDR = TOS; wr` | `MDR = 42`; escreve em `dados[6]` | `MDR=42, dados[6]=42` |

**`BIPUSH 00010100`** (byte = 20) — empilha o byte literal:

| Microinstrução | Efeito | Estado após |
|---|---|---|
| `SP = MAR = SP+1` | `SP = 7`, `MAR = 7` | `SP=7, MAR=7` |
| `fetch` | `MBR = 00010100`; `H = MBR` (zero-extended, sem ULA) | `MBR=20, H=20` |
| `MDR = TOS = H; wr` | `MDR = 20`, `TOS = 20`; escreve em `dados[7]` | `MDR=20, TOS=20, dados[7]=20` |

### Saída esperada (resumo)

Ao final da execução das três instruções:

```
Registradores:
  H   = 20
  TOS = 20
  LV  = 2
  SP  = 7
  MDR = 20
  MAR = 7
  MBR = 20

Memória de dados:
  [3] = 42   (variável local, inalterada)
  [5] = 42   (ILOAD 1 empilhado)
  [6] = 42   (DUP do topo)
  [7] = 20   (BIPUSH 20 empilhado)
```

> O log completo — com cada microinstrução, seus 23 bits, e o estado de registradores/memória antes e depois de cada uma — é gravado em `saida_entregavel.txt`.

---

## Requisitos

- **Python** ≥ 3.7
- Sistema operacional: Linux, macOS ou Windows
- Sem dependências externas (biblioteca padrão apenas)

---

## Observações

- Todos os valores de 32 bits são tratados internamente como inteiros **sem sinal**; a interpretação com sinal (complemento de 2) é usada apenas para exibição em decimal e para o cálculo da flag `N`.
- O carry-out (`co`) só é relevante na operação de soma (`F1F0 = 11`).
- A partir da Etapa 2, `SLL8` e `SRA1` nunca ficam ativos ao mesmo tempo, e o deslocamento ocorre **depois** do cálculo de `S` pela ULA.
- Na Tarefa 2 da Etapa 2, a entrada `A` da ULA é **sempre** o valor de `H`; portanto, para operar sobre outro registrador é necessário primeiro copiá-lo para `H` em um ciclo anterior.
- Os registradores no início de um ciclo (a partir do segundo) são sempre iguais ao estado final do ciclo anterior — não há mais um `PC` contando linhas do programa como na Etapa 1.
- Na Etapa 3, a operação de memória (`WRITE`/`READ`) sempre ocorre **depois** da escrita no barramento C — ou seja, se a mesma microinstrução escrever `MAR` e também acessar a memória, o acesso já usa o novo valor de `MAR`.
- A memória de dados tem apenas **8 endereços** nesta tarefa; endereços fora da faixa `[0, 7]` são tratados via `MAR mod 8` e sinalizados no log, para que a execução não seja interrompida.
- A combinação `WRITE=1, READ=1` é reservada para o caso especial de *fetch* usado na tradução de `BIPUSH byte`; nesta etapa (Tarefa 1) ela é apenas reportada no log, sem efeito sobre `dados.txt`. No **Entregável**, esse mesmo caso especial é usado de fato: os 8 bits do campo da ULA carregam o byte literal do `BIPUSH`, que é copiado para `MBR` e depois para `H` (extensão de zeros, sem passar pela ULA).
- No Entregável, cada instrução de alto nível (`ILOAD x`, `DUP`, `BIPUSH byte`) é **traduzida dinamicamente** para uma lista de microinstruções de 23 bits (usando os mesmos campos ULA/C/Memória/B das etapas anteriores) e executada com a mesma rotina que processa microinstruções na Etapa 3. Isso garante que o comportamento seja idêntico ao que já foi validado nas etapas anteriores — não há um caminho de execução separado.
- A memória de dados usada nos testes tem apenas 8 endereços; nos exemplos de `ILOAD`/`DUP`/`BIPUSH`, `LV` e `SP` foram escolhidos de propósito para que os endereços acessados (`LV+1`, e os sucessivos `SP+1`) fiquem dentro da faixa `[0, 7]`.
- O projeto está completo em relação ao que foi pedido no enunciado: Etapa 1, Etapa 2 (Tarefas 1 e 2), Etapa 3 (Tarefa 1) e o Entregável (`ILOAD x`, `DUP`, `BIPUSH byte`).
