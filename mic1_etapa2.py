"""
=============================================================
  Simulador da Mic-1 Modificada  —  UFPB / Arq. Comp. II
  Profª. Sarah Pontes Madruga
=============================================================
Uso:
  python3 mic1.py etapa1          programa_etapa1.txt saida_etapa1.txt
  python3 mic1.py etapa2_tarefa1  programa_etapa2_tarefa1.txt saida_etapa2_tarefa1.txt
  python3 mic1.py etapa2_tarefa2  registradores_etapa2_tarefa2.txt programa_etapa2_tarefa2.txt saida_etapa2_tarefa2.txt
=============================================================
"""

import sys
import os

# ───────────────────────────────────────────────────────────
# CONSTANTES E HELPERS
# ───────────────────────────────────────────────────────────

MASK32 = 0xFFFFFFFF
SEP60  = "=" * 60
SEP53  = "=" * 53
STAR   = "*" * 31


def u32(v: int) -> int:
    """Garante inteiro sem sinal de 32 bits."""
    return v & MASK32


def b32(v: int) -> str:
    """Formata inteiro como string de 32 bits."""
    return format(u32(v), "032b")


def b8(v: int) -> str:
    """Formata inteiro como string de 8 bits."""
    return format(v & 0xFF, "08b")


def sign_ext8(v: int) -> int:
    """Extensão de SINAL de 8 para 32 bits."""
    v &= 0xFF
    if v & 0x80:
        return u32(v | 0xFFFFFF00)
    return v


def zero_ext8(v: int) -> int:
    """Extensão com ZEROS de 8 para 32 bits."""
    return v & 0xFF


def to_signed32(v: int) -> int:
    """Interpreta um inteiro de 32 bits sem sinal como inteiro com sinal (complemento de 2)."""
    v = u32(v)
    return v - 0x100000000 if (v & 0x80000000) else v


def load_lines(path: str) -> list:
    """Lê arquivo e devolve linhas não-vazias e sem comentários."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]


# ───────────────────────────────────────────────────────────
# ULA  (núcleo compartilhado, 6 bits de controle)
# ───────────────────────────────────────────────────────────

def ula_core(ctrl6: str, A: int, B: int) -> tuple:
    """
    Executa a ULA com 6 bits de controle: F0 F1 ENA ENB INVA INC
    Retorna (S, carry_out) — S é inteiro de 32 bits sem sinal.
    """
    F0, F1, ENA, ENB, INVA, INC = (int(b) for b in ctrl6)

    a_in = u32(A) if ENA else 0
    if INVA:
        a_in = u32(~a_in)

    b_in = u32(B) if ENB else 0

    carry_in = INC  # INC força carry; vem-um não é usado nestas etapas

    f = (F1 << 1) | F0

    if f == 0b11:           # soma
        res  = a_in + b_in + carry_in
        S    = u32(res)
        co   = 1 if res > MASK32 else 0
    elif f == 0b10:         # NOT a_in
        S    = u32(~a_in)
        co   = 0
    elif f == 0b01:         # OR
        S    = u32(a_in | b_in)
        co   = 0
    else:                   # AND
        S    = u32(a_in & b_in)
        co   = 0

    return S, co


# ───────────────────────────────────────────────────────────
# ULA  (etapa 2 — 8 bits de controle: SLL8 SRA1 F0 F1 ENA ENB INVA INC)
# ───────────────────────────────────────────────────────────

def shift_sll8(v: int) -> int:
    """Deslocamento LÓGICO para a esquerda em 8 bits (zeros entram pela direita)."""
    return u32(u32(v) << 8)


def shift_sra1(v: int) -> int:
    """Deslocamento ARITMÉTICO para a direita em 1 bit (preserva o bit de sinal)."""
    v = u32(v)
    sinal = v & 0x80000000
    res = v >> 1
    if sinal:
        res |= 0x80000000
    return u32(res)


def ula8(ctrl8: str, A: int, B: int) -> tuple:
    """
    Executa a ULA com 8 bits de controle: SLL8 SRA1 F0 F1 ENA ENB INVA INC
    O núcleo de 6 bits (F0..INC) é o mesmo da etapa 1. Depois de calculado
    o valor S, o deslocador (SLL8 / SRA1) é aplicado para gerar a saída
    deslocada Sd. As flags N (negativo) e Z (zero) são calculadas sobre Sd.
    SLL8 e SRA1 nunca estão ativos ao mesmo tempo (conforme o enunciado).

    Retorna (Sd, co, N, Z).
    """
    SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC = (int(b) for b in ctrl8)

    ctrl6 = f"{F0}{F1}{ENA}{ENB}{INVA}{INC}"
    S, co = ula_core(ctrl6, A, B)

    if SLL8:
        Sd = shift_sll8(S)
    elif SRA1:
        Sd = shift_sra1(S)
    else:
        Sd = S

    N = 1 if (Sd & 0x80000000) else 0
    Z = 1 if Sd == 0 else 0

    return Sd, co, N, Z


# ───────────────────────────────────────────────────────────
# ETAPA 1  —  ULA 6 bits
# ───────────────────────────────────────────────────────────

def etapa1(prog_path: str, out_path: str):
    """
    Cada linha do programa: <ctrl_6bits>  (A e B são constantes de 32 bits
    inicializados como all-1 e 1 respectivamente, conforme saída de exemplo).
    """
    instrucoes = load_lines(prog_path)

    # A e B fixos; a saída de exemplo usa A=0xFFFFFFFF, B=1
    A = MASK32      # = 11111111...1
    B = 1

    log = []
    log.append(f"b = {b32(B)}")
    log.append(f"a = {b32(A)}")
    log.append("")
    log.append("Start of Program")

    PC = 1
    for ctrl in instrucoes:
        log.append(SEP60)
        log.append(f"Cycle {PC}")
        log.append("")
        log.append(f"PC = {PC}")

        if len(ctrl) != 6 or not all(c in "01" for c in ctrl):
            log.append(f"> Error, invalid control signals.")
            PC += 1
            continue

        log.append(f"IR = {ctrl}")

        S, co = ula_core(ctrl, A, B)

        log.append(f"b = {b32(B)}")
        log.append(f"a = {b32(A)}")
        log.append(f"s = {b32(S)}")
        log.append(f"co = {co}")

        # A é atualizado com S; B permanece fixo (conforme exemplos)
        A = S
        PC += 1

    log.append(SEP60)
    log.append(f"Cycle {PC}")
    log.append("")
    log.append(f"PC = {PC}")
    log.append("> Line is empty, EOP.")
    log.append("")

    resultado = "\n".join(log)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resultado)
    print(resultado)
    print(f"\nLog salvo em: {out_path}")


# ───────────────────────────────────────────────────────────
# ETAPA 2 — TAREFA 1  —  ULA 8 bits (SLL8 / SRA1 / N / Z)
# ───────────────────────────────────────────────────────────

def etapa2_tarefa1(prog_path: str, out_path: str):
    """
    Mesma estrutura de teste da etapa 1, mas agora cada linha do programa
    contém uma palavra de controle de 8 bits:
        SLL8 SRA1 F0 F1 ENA ENB INVA INC
    A e B seguem o mesmo padrão da etapa 1 (A = todos 1s, B = 1), e A é
    realimentado com a saída deslocada Sd a cada ciclo.
    """
    instrucoes = load_lines(prog_path)

    A = MASK32
    B = 1

    log = []
    log.append(f"b = {b32(B)}")
    log.append(f"a = {b32(A)}")
    log.append("")
    log.append("Start of Program")

    PC = 1
    for ctrl in instrucoes:
        log.append(SEP60)
        log.append(f"Cycle {PC}")
        log.append("")
        log.append(f"PC = {PC}")

        if len(ctrl) != 8 or not all(c in "01" for c in ctrl):
            log.append("> Error, invalid control signals.")
            PC += 1
            continue

        log.append(f"IR = {ctrl}")

        Sd, co, N, Z = ula8(ctrl, A, B)

        log.append(f"b  = {b32(B)}")
        log.append(f"a  = {b32(A)}")
        log.append(f"sd = {b32(Sd)}")
        log.append(f"co = {co}")
        log.append(f"n  = {N}")
        log.append(f"z  = {Z}")

        A = Sd
        PC += 1

    log.append(SEP60)
    log.append(f"Cycle {PC}")
    log.append("")
    log.append(f"PC = {PC}")
    log.append("> Line is empty, EOP.")
    log.append("")

    resultado = "\n".join(log)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resultado)
    print(resultado)
    print(f"\nLog salvo em: {out_path}")


# ───────────────────────────────────────────────────────────
# ETAPA 2 — TAREFA 2  —  Caminho de dados (registradores, decoder, seletor)
# ───────────────────────────────────────────────────────────

REGS32 = ["H", "OPC", "TOS", "CPP", "LV", "SP", "PC", "MDR", "MAR"]

# Decodificador de 4 bits -> registrador que comanda o barramento B
# (Registrador  OPC TOS CPP LV SP MBRU MBR PC MDR / Saída  8 7 6 5 4 3 2 1 0)
DECODER_B = {
    8: "OPC", 7: "TOS", 6: "CPP", 5: "LV", 4: "SP",
    3: "MBRU", 2: "MBR", 1: "PC", 0: "MDR",
}

# Seletor de 9 bits -> registradores habilitados a serem escritos pelo barramento C
# (Registrador  H OPC TOS CPP LV SP PC MDR MAR / Bit  8 7 6 5 4 3 2 1 0)
SELETOR_C_BIT = {
    8: "H", 7: "OPC", 6: "TOS", 5: "CPP", 4: "LV",
    3: "SP", 2: "PC", 1: "MDR", 0: "MAR",
}


def registradores_iniciais() -> dict:
    regs = {r: 0 for r in REGS32}
    regs["MBR"] = 0
    return regs


def load_registradores(path: str) -> dict:
    """
    Lê o estado inicial dos registradores a partir de um arquivo texto.
    Formato esperado, uma atribuição por linha:
        H=0
        OPC=0
        TOS=0
        CPP=0
        LV=0
        SP=0
        PC=0
        MDR=0
        MAR=0
        MBR=0
    Os valores podem ser decimais, ou em hexadecimal/binário usando os
    prefixos 0x / 0b (são interpretados por int(valor, 0)).
    """
    regs = registradores_iniciais()
    for linha in load_lines(path):
        if "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip().upper()
        valor = valor.strip()
        val = int(valor, 0)
        if chave == "MBR":
            regs["MBR"] = val & 0xFF
        elif chave in REGS32:
            regs[chave] = u32(val)
    return regs


def decode_bus_b(bits4: str, regs: dict) -> tuple:
    """Decodifica os 4 bits de controle do barramento B. Retorna (valor_32bits, nome)."""
    idx = int(bits4, 2)
    nome = DECODER_B.get(idx)
    if nome is None:
        return 0, f"Indefinido({idx})"
    if nome == "MBR":
        # bit de sinal do MBR estende a palavra até 32 bits
        return sign_ext8(regs["MBR"]), "MBR"
    if nome == "MBRU":
        # extensão com zeros até 32 bits
        return zero_ext8(regs["MBR"]), "MBRU"
    return regs[nome], nome


def decode_bus_c(bits9: str) -> list:
    """Decodifica os 9 bits do seletor de escrita do barramento C."""
    habilitados = []
    for i, bit in enumerate(bits9):
        if bit == "1":
            habilitados.append(SELETOR_C_BIT[8 - i])
    return habilitados


def snapshot(regs: dict) -> list:
    """Gera linhas formatadas com o estado atual de todos os registradores."""
    ordem = ["H", "OPC", "TOS", "CPP", "LV", "SP", "PC", "MDR", "MAR", "MBR"]
    linhas = []
    for r in ordem:
        if r == "MBR":
            linhas.append(f"{r:4s} = {b8(regs[r])}  (dec = {regs[r]})")
        else:
            linhas.append(
                f"{r:4s} = {b32(regs[r])}  (dec = {to_signed32(regs[r])})"
            )
    return linhas


def etapa2_tarefa2(reg_path: str, prog_path: str, out_path: str):
    """
    Executa o caminho de dados da Mic-1 (sem memória/pilha, que vêm na etapa 3).
    Cada linha do programa é uma palavra de 21 bits:
        Controle da ULA (8) | Controle do barramento C (9) | Controle do barramento B (4)
    A entrada A da ULA é sempre o valor de H. A entrada B é o valor do
    registrador habilitado pelo decodificador de 4 bits. A saída deslocada
    Sd é escrita, ao final do ciclo, em todos os registradores habilitados
    pelo seletor de 9 bits.
    """
    regs = load_registradores(reg_path)
    instrucoes = load_lines(prog_path)

    log = []
    log.append("Estado inicial dos registradores:")
    for linha in snapshot(regs):
        log.append("  " + linha)
    log.append("")
    log.append("Start of Program")

    ciclo = 1
    for instr in instrucoes:
        instr = instr.replace(" ", "")
        log.append(SEP60)
        log.append(f"Cycle {ciclo}")
        log.append("")

        if len(instr) != 21 or not all(c in "01" for c in instr):
            log.append("> Error, invalid instruction (esperado palavra de 21 bits).")
            ciclo += 1
            continue

        ctrl_ula = instr[0:8]
        ctrl_c = instr[8:17]
        ctrl_b = instr[17:21]

        log.append(f"IR = {instr}")
        log.append("")
        log.append("--- Registradores no início do ciclo ---")
        for linha in snapshot(regs):
            log.append("  " + linha)

        B_val, B_nome = decode_bus_b(ctrl_b, regs)
        A_val = regs["H"]
        habilitados_c = decode_bus_c(ctrl_c)

        log.append("")
        log.append(f"Barramento B comandado por: {B_nome}")
        log.append(f"A (= H)        = {b32(A_val)}")
        log.append(f"B ({B_nome:5s}) = {b32(B_val)}")
        log.append(
            f"Controle ULA (SLL8 SRA1 F0 F1 ENA ENB INVA INC) = {ctrl_ula}"
        )

        Sd, co, N, Z = ula8(ctrl_ula, A_val, B_val)

        log.append(f"Sd = {b32(Sd)}")
        log.append(f"Vai-um = {co}   N = {N}   Z = {Z}")
        log.append(
            "Registradores habilitados no barramento C: "
            + (", ".join(habilitados_c) if habilitados_c else "(nenhum)")
        )

        for r in habilitados_c:
            regs[r] = u32(Sd)

        log.append("")
        log.append("--- Registradores no fim do ciclo ---")
        for linha in snapshot(regs):
            log.append("  " + linha)
        log.append("")

        ciclo += 1

    log.append(SEP60)
    log.append(f"Cycle {ciclo}")
    log.append("")
    log.append("> Line is empty, EOP.")
    log.append("")

    resultado = "\n".join(log)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resultado)
    print(resultado)
    print(f"\nLog salvo em: {out_path}")


# ───────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────

def _uso_e_sai():
    print("Uso:")
    print("  python3 mic1.py etapa1          <programa.txt> <saida.txt>")
    print("  python3 mic1.py etapa2_tarefa1  <programa.txt> <saida.txt>")
    print("  python3 mic1.py etapa2_tarefa2  <registradores.txt> <programa.txt> <saida.txt>")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        _uso_e_sai()

    modo = sys.argv[1]

    if modo == "etapa1":
        if len(sys.argv) != 4:
            _uso_e_sai()
        etapa1(sys.argv[2], sys.argv[3])

    elif modo == "etapa2_tarefa1":
        if len(sys.argv) != 4:
            _uso_e_sai()
        etapa2_tarefa1(sys.argv[2], sys.argv[3])

    elif modo == "etapa2_tarefa2":
        if len(sys.argv) != 5:
            _uso_e_sai()
        etapa2_tarefa2(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        print(f"Modo '{modo}' não reconhecido.")
        _uso_e_sai()
