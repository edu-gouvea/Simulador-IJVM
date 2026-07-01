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
- [Como Executar](#como-executar)
- [Formato dos Arquivos de Entrada](#formato-dos-arquivos-de-entrada)
- [Formato da Saída](#formato-da-saída)
- [Exemplo Completo — Etapa 1](#exemplo-completo--etapa-1)
- [Exemplo Completo — Etapa 2, Tarefa 1](#exemplo-completo--etapa-2-tarefa-1)
- [Exemplo Completo — Etapa 2, Tarefa 2](#exemplo-completo--etapa-2-tarefa-2)
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
```

### Parâmetros

| Parâmetro              | Descrição |
|-------------------------|-----------|
| `etapa1`                 | Modo de execução da Etapa 1 (ULA de 6 bits) |
| `etapa2_tarefa1`          | Modo de execução da Etapa 2 / Tarefa 1 (ULA de 8 bits) |
| `etapa2_tarefa2`          | Modo de execução da Etapa 2 / Tarefa 2 (caminho de dados completo) |
| `<arquivo_registradores>` | (Somente `etapa2_tarefa2`) Arquivo `.txt` com o estado inicial dos registradores |
| `<arquivo_programa>`      | Caminho para o arquivo `.txt` com as instruções a serem executadas |
| `<arquivo_saida>`         | Caminho para o arquivo `.txt` onde a saída será gravada |

### Exemplos

```bash
python3 mic1.py etapa1 programa_etapa1.txt saida_etapa1.txt

python3 mic1.py etapa2_tarefa1 programa_etapa2_tarefa1.txt saida_etapa2_tarefa1.txt

python3 mic1.py etapa2_tarefa2 registradores_etapa2_tarefa2.txt programa_etapa2_tarefa2.txt saida_etapa2_tarefa2.txt
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
- O simulador foi projetado para ser expandido em etapas futuras com novos componentes da Mic-1 (memória de dados/instruções, pilha, tradução de instruções da ISA da IJVM etc.).
