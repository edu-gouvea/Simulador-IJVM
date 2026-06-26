"""
=============================================================
  Simulador da Mic-1 Modificada  —  UFPB / Arq. Comp. II
  Profª. Sarah Pontes Madruga
=============================================================
Uso:
  python mic1.py etapa1 programa_etapa1.txt saida_etapa1.txt
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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python3 mic1.py etapa1 <programa.txt> <saida.txt>")
        sys.exit(1)

    modo = sys.argv[1]

    if modo == "etapa1":
        etapa1(sys.argv[2], sys.argv[3])
    else:
        print(f"Modo '{modo}' não reconhecido.")