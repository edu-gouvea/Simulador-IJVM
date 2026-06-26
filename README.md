# Simulador da Mic-1 Modificada

> Projeto acadêmico desenvolvido para a disciplina de **Arquitetura de Computadores II**  
> Universidade Federal da Paraíba (UFPB) — Profª. Sarah Pontes Madruga

---

## Sumário

- [Descrição](#descrição)
- [Arquitetura Simulada](#arquitetura-simulada)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Etapa 1 — ULA de 6 Bits de Controle](#etapa-1--ula-de-6-bits-de-controle)
- [Como Executar](#como-executar)
- [Formato dos Arquivos de Entrada](#formato-dos-arquivos-de-entrada)
- [Formato da Saída](#formato-da-saída)
- [Exemplo Completo — Etapa 1](#exemplo-completo--etapa-1)
- [Requisitos](#requisitos)

---

## Descrição

Este projeto implementa um **simulador da microarquitetura Mic-1 modificada**, baseada na máquina descrita por Tanenbaum em *Organização Estruturada de Computadores*. O simulador é desenvolvido em Python e executa programas de microinstruções, reproduzindo o comportamento interno da ULA (Unidade Lógica e Aritmética) e do caminho de dados da Mic-1.

O projeto é dividido em etapas incrementais, cada uma adicionando componentes e funcionalidades ao simulador.

---

## Arquitetura Simulada

A Mic-1 modificada opera com:

- Palavras de **32 bits** (sem sinal, complemento a dois)
- **ULA** controlada por **6 bits de controle**: `F0 F1 ENA ENB INVA INC`
- Registradores internos `A` e `B` para operandos
- Registrador `S` para o resultado
- Bit de carry-out (`co`)

### Bits de Controle da ULA

| Bit  | Nome | Função |
|------|------|--------|
| 0    | F0   | Seletor de função (LSB) |
| 1    | F1   | Seletor de função (MSB) |
| 2    | ENA  | Habilita entrada A |
| 3    | ENB  | Habilita entrada B |
| 4    | INVA | Inverte A antes da operação |
| 5    | INC  | Força carry-in = 1 (incremento) |

### Funções da ULA (F1 F0)

| F1 | F0 | Operação |
|----|----|----------|
| 0  | 0  | AND (A & B) |
| 0  | 1  | OR  (A \| B) |
| 1  | 0  | NOT A |
| 1  | 1  | Soma (A + B + carry_in) |

> A combinação de `INVA` e `INC` com a soma permite derivar operações como subtração e passagem de `B`.

---

## Estrutura do Projeto

```
mic1/
├── mic1.py                  # Simulador principal
├── programa_etapa1.txt      # Programa de entrada da Etapa 1
├── saida_etapa1.txt         # Saída gerada pelo simulador
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

## Como Executar

### Pré-requisitos

- Python 3.7 ou superior
- Nenhuma dependência externa

### Sintaxe

```bash
python3 mic1.py etapa1 <arquivo_programa> <arquivo_saida>
```

### Parâmetros

| Parâmetro         | Descrição |
|-------------------|-----------|
| `etapa1`          | Modo de execução (identifica a etapa) |
| `<arquivo_programa>` | Caminho para o arquivo `.txt` com os sinais de controle |
| `<arquivo_saida>`    | Caminho para o arquivo `.txt` onde a saída será gravada |

### Exemplo

```bash
python3 mic1.py etapa1 programa_etapa1.txt saida_etapa1.txt
```

---

## Formato dos Arquivos de Entrada

O arquivo de programa contém **uma instrução por linha**, onde cada instrução é uma palavra de **6 bits** (apenas `0` e `1`).

Linhas em branco e linhas iniciadas com `#` são ignoradas (comentários).

**Exemplo — `programa_etapa1.txt`:**

```
# Exemplo de programa para a Etapa 1
111100
110101
110100
011100
```

> Qualquer linha com formato inválido (diferente de 6 bits binários) é reportada como erro no log de saída e o simulador avança para o próximo ciclo.

---

## Formato da Saída

A saída é gerada tanto no **terminal** quanto no **arquivo de saída** especificado.

**Estrutura geral:**

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

## Requisitos

- **Python** ≥ 3.7
- Sistema operacional: Linux, macOS ou Windows
- Sem dependências externas (biblioteca padrão apenas)

---

## Observações

- Todos os valores são tratados como inteiros de **32 bits sem sinal** internamente.
- O carry-out só é relevante na operação de soma (`F1F0 = 11`).
- A realimentação de `S → A` a cada ciclo permite encadear operações progressivas.
- O simulador foi projetado para ser expandido em etapas futuras com novos componentes da Mic-1 (barramento, memória, registradores adicionais etc.).
