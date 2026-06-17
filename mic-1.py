"""
=======================================================
  Simulador da Mic-1 Modificada - UFPB / Arq. Comp. II
  Profª. Sarah Pontes Madruga
=======================================================

Estrutura:
  - Etapa 1  : ULA 6 bits  (F0 F1 ENA ENB INVA INC)
  - Etapa 2  : ULA 8 bits + registradores + microinstruções de 21 bits
  - Etapa 3  : Memória de dados + microinstruções de 23 bits
  - Entregável: Instruções IJVM  (ILOAD x, DUP, BIPUSH byte)
"""

import sys
import os

# ═══════════════════════════════════════════════════
#  UTILITÁRIOS
# ═══════════════════════════════════════════════════

WORD_BITS = 32
WORD_MASK = (1 << WORD_BITS) - 1   # 0xFFFFFFFF


def to_signed32(v: int) -> int:
    """Converte inteiro sem sinal de 32 bits para com sinal."""
    v &= WORD_MASK
    if v >= (1 << 31):
        v -= (1 << WORD_BITS)
    return v


def to_unsigned32(v: int) -> int:
    return v & WORD_MASK


def int_to_bin(v: int, bits: int) -> str:
    """Representa inteiro como string binária de largura fixa (sem sinal)."""
    return format(to_unsigned32(v) & ((1 << bits) - 1), f'0{bits}b')


def sign_extend_8_to_32(byte_val: int) -> int:
    """Extensão de sinal: 8 bits → 32 bits."""
    byte_val &= 0xFF
    if byte_val & 0x80:
        return byte_val | 0xFFFFFF00
    return byte_val


def zero_extend_8_to_32(byte_val: int) -> int:
    """Extensão com zeros: 8 bits → 32 bits."""
    return byte_val & 0xFF


# ═══════════════════════════════════════════════════
#  ETAPA 1 — ULA de 6 bits
# ═══════════════════════════════════════════════════

class ULA6:
    """
    ULA da Mic-1 controlada por 6 bits:
      F0 F1 ENA ENB INVA INC
      X0 X1 X2  X3  X4   X5
    """

    def executar(self, ctrl: str, A: int, B: int, vem_um: int = 0):
        """
        Executa a ULA dado o vetor de controle de 6 bits (string '000000'),
        os valores A e B (inteiros de 32 bits) e o bit vem-um.
        Retorna (S, vai_um) ambos inteiros.
        """
        if len(ctrl) != 6 or not all(c in '01' for c in ctrl):
            raise ValueError(f"Palavra de controle inválida: '{ctrl}' (esperado 6 bits)")

        F0, F1, ENA, ENB, INVA, INC = (int(b) for b in ctrl)

        A = to_unsigned32(A)
        B = to_unsigned32(B)

        # Entrada A efetiva
        a_in = A if ENA else 0
        if INVA:
            a_in = (~a_in) & WORD_MASK

        # Entrada B efetiva
        b_in = B if ENB else 0

        # Bit vem-um
        carry_in = INC if INC else vem_um

        # Operação selecionada por F1:F0
        f = (F1 << 1) | F0
        if f == 0b00:       # AND
            S = (a_in & b_in) & WORD_MASK
            vai_um = 0
        elif f == 0b01:     # OR
            S = (a_in | b_in) & WORD_MASK
            vai_um = 0
        elif f == 0b10:     # NOT a_in  (passa ~A)
            S = (~a_in) & WORD_MASK
            vai_um = 0
        elif f == 0b11:     # soma completa com carry
            resultado = a_in + b_in + carry_in
            S = resultado & WORD_MASK
            vai_um = 1 if resultado > WORD_MASK else 0
        else:
            S, vai_um = 0, 0

        return S, vai_um


# ═══════════════════════════════════════════════════
#  ETAPA 2 — ULA de 8 bits (com SLL8 e SRA1)
# ═══════════════════════════════════════════════════

class ULA8:
    """
    ULA da Mic-1 modificada — palavra de controle de 8 bits:
      SLL8 SRA1 F0 F1 ENA ENB INVA INC
      X0   X1   X2 X3 X4  X5  X6   X7

    Saídas: Sd (saída deslocada), vai_um, N, Z
    """

    def __init__(self):
        self._ula6 = ULA6()

    def executar(self, ctrl: str, A: int, B: int, vem_um: int = 0):
        """
        ctrl: string de 8 bits.
        Retorna (Sd, vai_um, N, Z).
        """
        if len(ctrl) != 8 or not all(c in '01' for c in ctrl):
            raise ValueError(f"Palavra de controle inválida: '{ctrl}' (esperado 8 bits)")

        SLL8, SRA1 = int(ctrl[0]), int(ctrl[1])
        ctrl6 = ctrl[2:]   # F0 F1 ENA ENB INVA INC

        S, vai_um = self._ula6.executar(ctrl6, A, B, vem_um)

        # Deslocador (pós-ULA)
        if SLL8 and not SRA1:
            # Deslocamento lógico para a esquerda em 8 bits
            Sd = (S << 8) & WORD_MASK
        elif SRA1 and not SLL8:
            # Deslocamento aritmético para a direita em 1 bit (preserva sinal)
            S_signed = to_signed32(S)
            Sd = to_unsigned32(S_signed >> 1)
        else:
            Sd = S

        # Flags
        Z = 1 if (Sd == 0) else 0
        N = 1 if (Sd & (1 << 31)) else 0

        return Sd, vai_um, N, Z


# ═══════════════════════════════════════════════════
#  ETAPA 2 — Registradores e barramentos
# ═══════════════════════════════════════════════════

# Mapeamento decodificador barramento B (4 bits → registrador)
# Saída habilitada: MDR=0, PC=1, MBR=2, MBRU=3, SP=4, LV=5, CPP=6, TOS=7, OPC=8
BARRAMENTO_B = {
    0: 'MDR',
    1: 'PC',
    2: 'MBR',
    3: 'MBRU',
    4: 'SP',
    5: 'LV',
    6: 'CPP',
    7: 'TOS',
    8: 'OPC',
}

# Mapeamento seletor barramento C (9 bits, bit 0 = MAR, bit 8 = H)
# Registrador : bit
BARRAMENTO_C_BITS = {
    'MAR': 0,
    'MDR': 1,
    'PC':  2,
    'SP':  3,
    'LV':  4,
    'CPP': 5,
    'TOS': 6,
    'OPC': 7,
    'H':   8,
}


class Registradores:
    """Conjunto de registradores da Mic-1."""

    NOMES_32 = ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'PC', 'MDR', 'MAR']
    NOMES_8  = ['MBR']

    def __init__(self):
        self.H   = 0
        self.OPC = 0
        self.TOS = 0
        self.CPP = 0
        self.LV  = 0
        self.SP  = 0
        self.PC  = 0
        self.MDR = 0
        self.MAR = 0
        self.MBR = 0   # 8 bits

    def get(self, nome: str) -> int:
        return getattr(self, nome)

    def set(self, nome: str, valor: int):
        if nome == 'MBR':
            setattr(self, nome, valor & 0xFF)
        else:
            setattr(self, nome, to_unsigned32(valor))

    def carregar_de_dict(self, d: dict):
        for nome, val in d.items():
            self.set(nome, val)

    def copiar(self) -> 'Registradores':
        r = Registradores()
        for n in self.NOMES_32 + self.NOMES_8:
            r.set(n, self.get(n))
        return r

    def dump(self) -> dict:
        return {n: self.get(n) for n in self.NOMES_32 + self.NOMES_8}

    def linha_str(self) -> str:
        partes = []
        for n in ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'MBR', 'PC', 'MDR', 'MAR']:
            partes.append(f"{n}={self.get(n)}")
        return "  ".join(partes)

    def __str__(self):
        return self.linha_str()


# ═══════════════════════════════════════════════════
#  ETAPA 3 — Memória de dados (8 palavras de 32 bits)
# ═══════════════════════════════════════════════════

class MemoriaDados:
    TAMANHO = 8

    def __init__(self):
        self.dados = [0] * self.TAMANHO

    def ler(self, endereco: int) -> int:
        if 0 <= endereco < self.TAMANHO:
            return self.dados[endereco]
        raise IndexError(f"Endereço de memória inválido: {endereco}")

    def escrever(self, endereco: int, valor: int):
        if 0 <= endereco < self.TAMANHO:
            self.dados[endereco] = to_unsigned32(valor)
        else:
            raise IndexError(f"Endereço de memória inválido: {endereco}")

    def carregar_de_arquivo(self, caminho: str):
        with open(caminho, 'r') as f:
            for i, linha in enumerate(f):
                linha = linha.strip()
                if not linha:
                    continue
                if i >= self.TAMANHO:
                    break
                self.dados[i] = int(linha, 2) if set(linha) <= {'0','1'} else int(linha)

    def dump(self) -> str:
        linhas = []
        for i, v in enumerate(self.dados):
            linhas.append(f"  mem[{i}] = {v:10d}  ({int_to_bin(v, 32)})")
        return "\n".join(linhas)


# ═══════════════════════════════════════════════════
#  MÁQUINA MIC-1 COMPLETA
# ═══════════════════════════════════════════════════

class Mic1:
    """
    Simulador completo da Mic-1 modificada.
    Suporta microinstruções de 23 bits:
      ULA(8) | Barr.C(9) | Memória(2) | Barr.B(4)
    """

    def __init__(self):
        self.ula       = ULA8()
        self.regs      = Registradores()
        self.memoria   = MemoriaDados()
        self.log_linhas: list[str] = []

    # ── carregadores de arquivos ─────────────────────

    def carregar_registradores(self, caminho: str):
        """Arquivo com linhas  NOME=VALOR  (decimal ou binário)."""
        with open(caminho, 'r') as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith('#'):
                    continue
                nome, _, val_str = linha.partition('=')
                nome = nome.strip().upper()
                val_str = val_str.strip()
                val = int(val_str, 2) if set(val_str) <= {'0','1'} else int(val_str)
                self.regs.set(nome, val)

    def carregar_memoria(self, caminho: str):
        self.memoria.carregar_de_arquivo(caminho)

    # ── execução de microinstrução de 23 bits ────────

    def executar_microinstrucao(self, palavra: str, log: list = None) -> dict:
        """
        palavra: string de 23 bits
          bits [22:15] → controle ULA (8 bits)
          bits [14:6]  → controle barramento C (9 bits)
          bits [5:4]   → memória (WRITE READ)
          bits [3:0]   → controle barramento B (4 bits)
        Retorna dicionário com informações da execução.
        """
        if len(palavra) != 23:
            raise ValueError(f"Microinstrução deve ter 23 bits, recebeu {len(palavra)}: '{palavra}'")

        ctrl_ula  = palavra[0:8]
        ctrl_c    = palavra[8:17]
        ctrl_mem  = palavra[17:19]
        ctrl_b    = palavra[19:23]

        WRITE = int(ctrl_mem[0])
        READ  = int(ctrl_mem[1])

        # Caso especial: WRITE=1 e READ=1 → fetch (H = MBR com zero-extend)
        especial_fetch = (WRITE == 1 and READ == 1)

        b_idx = int(ctrl_b, 2)

        info = {
            'IR'         : palavra,
            'ctrl_ula'   : ctrl_ula,
            'ctrl_c'     : ctrl_c,
            'WRITE'      : WRITE,
            'READ'       : READ,
            'especial'   : especial_fetch,
            'regs_antes' : self.regs.copiar(),
            'mem_antes'  : list(self.memoria.dados),
        }

        if especial_fetch:
            # H = MBR (8 bits do início da palavra → MBR, depois H = MBR)
            byte_val = int(ctrl_ula, 2) & 0xFF
            self.regs.set('MBR', byte_val)
            self.regs.set('H',   zero_extend_8_to_32(byte_val))
            info['operacao']  = 'FETCH especial: H = MBR (zero-extend)'
            info['barr_b']    = 'N/A'
            info['barr_c']    = ['H', 'MBR']
            info['Sd'] = self.regs.get('H')
            info['vai_um'] = 0
            info['N'] = 0
            info['Z'] = 1 if self.regs.get('H') == 0 else 0
        else:
            # 1) Entrada B
            if b_idx not in BARRAMENTO_B:
                raise ValueError(f"Índice do barramento B inválido: {b_idx}")
            nome_b = BARRAMENTO_B[b_idx]

            if nome_b == 'MBRU':
                B_val = zero_extend_8_to_32(self.regs.get('MBR'))
            elif nome_b == 'MBR':
                B_val = sign_extend_8_to_32(self.regs.get('MBR'))
            else:
                B_val = self.regs.get(nome_b)

            # 2) Entrada A = H
            A_val = self.regs.get('H')

            # 3) ULA
            Sd, vai_um, N, Z = self.ula.executar(ctrl_ula, A_val, B_val)

            # 4) Escreve nos registradores habilitados (barramento C)
            regs_escritos = []
            for nome_reg, bit_pos in BARRAMENTO_C_BITS.items():
                if ctrl_c[8 - bit_pos] == '1':
                    self.regs.set(nome_reg, Sd)
                    regs_escritos.append(nome_reg)

            # 5) Operação de memória (após escrita nos regs)
            if WRITE and not READ:
                endereco = self.regs.get('MAR') % self.memoria.TAMANHO
                self.memoria.escrever(endereco, self.regs.get('MDR'))
            elif READ and not WRITE:
                endereco = self.regs.get('MAR') % self.memoria.TAMANHO
                self.regs.set('MDR', self.memoria.ler(endereco))

            info['barr_b']   = nome_b
            info['B_val']    = B_val
            info['A_val']    = A_val
            info['Sd']       = Sd
            info['vai_um']   = vai_um
            info['N']        = N
            info['Z']        = Z
            info['barr_c']   = regs_escritos

        info['regs_depois'] = self.regs.copiar()
        info['mem_depois']  = list(self.memoria.dados)
        return info

    # ── formatação de log ────────────────────────────

    @staticmethod
    def _formatar_info(info: dict, mostrar_mem: bool = True) -> str:
        linhas = []
        linhas.append(f"  IR = {info['IR']}")

        ra = info['regs_antes']
        rd = info['regs_depois']
        linhas.append("  REGISTRADORES (antes → depois):")
        for n in ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'MBR', 'PC', 'MDR', 'MAR']:
            av = ra.get(n)
            dv = rd.get(n)
            mudou = " ◄" if av != dv else ""
            linhas.append(f"    {n:4s}: {av:12d}  →  {dv:12d}{mudou}")

        if not info['especial']:
            linhas.append(f"  Barramento B : {info['barr_b']}  (B={info.get('B_val',0)})")
            linhas.append(f"  Barramento C : {info['barr_c']}")
            linhas.append(f"  ULA saída Sd : {info['Sd']}  vai_um={info['vai_um']}  N={info['N']}  Z={info['Z']}")
        else:
            linhas.append(f"  {info['operacao']}")

        if mostrar_mem:
            ma = info['mem_antes']
            md = info['mem_depois']
            linhas.append("  MEMÓRIA (antes → depois):")
            for i in range(len(ma)):
                mudou = " ◄" if ma[i] != md[i] else ""
                linhas.append(f"    mem[{i}]: {ma[i]:12d}  →  {md[i]:12d}{mudou}")

        return "\n".join(linhas)

    # ── execução em modo de arquivo de microinstruções ─

    def executar_arquivo_microinstrucoes(self,
                                          caminho_prog: str,
                                          mostrar_mem: bool = True) -> str:
        """
        Lê arquivo de microinstruções (1 por linha, 21 ou 23 bits) e executa.
        Retorna o log como string.
        """
        log = []
        with open(caminho_prog, 'r') as f:
            instrucoes = [l.strip() for l in f if l.strip() and not l.startswith('#')]

        for i, palavra in enumerate(instrucoes):
            # Normaliza para 23 bits (padding de zeros à esquerda se 21 bits)
            if len(palavra) == 21:
                ctrl_ula = palavra[:8]
                ctrl_c = palavra[8:17]
                ctrl_b = palavra[17:21]

                palavra = ctrl_ula + ctrl_c + "00" + ctrl_b

            elif len(palavra) != 23:
                raise ValueError("Microinstrução inválida")
            log.append(f"\n{'='*60}")
            log.append(f"  Microinstrução #{i+1}  (PC={i})")
            log.append(f"{'='*60}")
            info = self.executar_microinstrucao(palavra, log)
            log.append(self._formatar_info(info, mostrar_mem))

        return "\n".join(log)


# ═══════════════════════════════════════════════════
#  ENTREGÁVEL — Instruções IJVM
# ═══════════════════════════════════════════════════

# Microinstruções pré-definidas (strings de 23 bits)
# Notação: [ctrl_ula(8)] [ctrl_c(9)] [mem(2)] [ctrl_b(4)]

def _microinstr(ctrl_ula, ctrl_c, mem, ctrl_b) -> str:
    return ctrl_ula + ctrl_c + mem + ctrl_b

# Auxiliar: monta ctrl_c a partir de lista de nomes de registradores
def _ctrl_c_de_lista(nomes: list) -> str:
    bits = ['0'] * 9
    for n in nomes:
        if n in BARRAMENTO_C_BITS:
            bits[8 - BARRAMENTO_C_BITS[n]] = '1'
    return ''.join(bits)

# Auxiliar: monta ctrl_b a partir do nome do registrador
def _ctrl_b_de_nome(nome: str) -> str:
    for k, v in BARRAMENTO_B.items():
        if v == nome:
            return format(k, '04b')
    raise ValueError(f"Registrador não encontrado no barramento B: {nome}")

# Operações ULA comuns (8 bits: SLL8 SRA1 F0 F1 ENA ENB INVA INC)
ULA_B       = '00001100'   # Sd = B           (F=11, ENA=0, ENB=1, INVA=0, INC=0)
ULA_A_MAIS_B= '00111100'   # Sd = A + B       (F=11, ENA=1, ENB=1, INVA=0, INC=0)
ULA_B_MAIS_1= '00110101'   # Sd = B + 1       (F=11, ENA=0, ENB=1, INVA=0, INC=1)
                            #   → ENA=0 → a_in=0, INC=1 → carry_in=1, logo Sd = B+1
ULA_A       = '00111000'   # Sd = A           (F=11, ENA=1, ENB=0, INVA=0, INC=0)
                            #   → B_in=0, logo Sd=A+0=A


def traduzir_iload(x: int, estado_regs: Registradores, memoria: MemoriaDados) -> list:
    """
    Traduz ILOAD x para lista de microinstruções de 23 bits.
    Sequência:
      H = LV
      (H = H+1) × x   ← x incrementos
      MAR = H; rd
      MAR = SP = SP+1; wr
      TOS = MDR
    """
    micro = []

    # H = LV  →  Sd = B(LV), escreve H
    micro.append(_microinstr(
        ULA_B,
        _ctrl_c_de_lista(['H']),
        '00',
        _ctrl_b_de_nome('LV')
    ))

    # H = H+1  (repetido x vezes)
    for _ in range(x):
        # Sd = A + 1  →  ENA=1, ENB=0, INC=1 →  Sd = H + 0 + 1 = H+1
        micro.append(_microinstr(
            '00111001',          # F=11, ENA=1, ENB=0, INVA=0, INC=1
            _ctrl_c_de_lista(['H']),
            '00',
            _ctrl_b_de_nome('MDR')  # B não importa (ENB=0)
        ))

    # MAR = H; rd
    micro.append(_microinstr(
        ULA_A,
        _ctrl_c_de_lista(['MAR']),
        '01',                    # READ=1
        _ctrl_b_de_nome('MDR')   # B irrelevante (ENB=0)
    ))

    # MAR = SP = SP+1; wr
    micro.append(_microinstr(
        ULA_B_MAIS_1,
        _ctrl_c_de_lista(['MAR', 'SP']),
        '10',                    # WRITE=1
        _ctrl_b_de_nome('SP')
    ))

    # TOS = MDR
    micro.append(_microinstr(
        ULA_B,
        _ctrl_c_de_lista(['TOS']),
        '00',
        _ctrl_b_de_nome('MDR')
    ))

    return micro


def traduzir_dup() -> list:
    """
    DUP: duplica o topo da pilha.
      MAR = SP = SP+1
      MDR = TOS; wr
    """
    micro = []

    # MAR = SP = SP+1
    micro.append(_microinstr(
        ULA_B_MAIS_1,
        _ctrl_c_de_lista(['MAR', 'SP']),
        '00',
        _ctrl_b_de_nome('SP')
    ))

    # MDR = TOS; wr
    micro.append(_microinstr(
        ULA_B,
        _ctrl_c_de_lista(['MDR']),
        '10',                    # WRITE=1
        _ctrl_b_de_nome('TOS')
    ))

    return micro


def traduzir_bipush(byte_val: int) -> list:
    """
    BIPUSH byte: carrega um byte arbitrário no topo da pilha.
      SP = MAR = SP+1
      fetch (caso especial: MBR = byte_val, H = zero_extend(byte_val))
      MDR = TOS = H; wr
    """
    micro = []

    # SP = MAR = SP+1
    micro.append(_microinstr(
        ULA_B_MAIS_1,
        _ctrl_c_de_lista(['SP', 'MAR']),
        '00',
        _ctrl_b_de_nome('SP')
    ))

    # Fetch especial: WRITE=1 e READ=1, primeiros 8 bits = byte_val
    byte_bin = format(byte_val & 0xFF, '08b')
    micro.append(byte_bin + '000000000' + '11' + '0000')

    # MDR = TOS = H; wr
    micro.append(_microinstr(
        ULA_A,
        _ctrl_c_de_lista(['MDR', 'TOS']),
        '10',                    # WRITE=1
        _ctrl_b_de_nome('MDR')   # B irrelevante
    ))

    return micro


class SimuladorIJVM:
    """
    Lê arquivo de instruções IJVM, traduz para microinstruções e executa.
    """

    def __init__(self):
        self.maquina = Mic1()

    def carregar_registradores(self, caminho: str):
        self.maquina.carregar_registradores(caminho)

    def carregar_memoria(self, caminho: str):
        self.maquina.carregar_memoria(caminho)

    def executar_arquivo(self, caminho_instrucoes: str) -> str:
        log = []

        # Estado inicial da memória
        log.append("╔══════════════════════════════════════════════════════════╗")
        log.append("║          SIMULADOR MIC-1 — INSTRUÇÕES IJVM              ║")
        log.append("╚══════════════════════════════════════════════════════════╝")
        log.append("\n  ── MEMÓRIA DE DADOS (estado inicial) ──")
        log.append(self.maquina.memoria.dump())
        log.append("\n  ── REGISTRADORES (estado inicial) ──")
        log.append("  " + self.maquina.regs.linha_str())

        with open(caminho_instrucoes, 'r') as f:
            instrucoes_raw = [l.strip() for l in f if l.strip() and not l.startswith('#')]

        for idx, linha in enumerate(instrucoes_raw):
            partes = linha.split()
            opcode = partes[0].upper()
            arg    = int(partes[1]) if len(partes) > 1 else 0

            log.append(f"\n\n{'▀'*62}")
            log.append(f"  INSTRUÇÃO IJVM #{idx+1}: {linha}")
            log.append(f"{'▄'*62}")

            # Traduz para microinstruções
            if opcode == 'ILOAD':
                micro_list = traduzir_iload(arg, self.maquina.regs, self.maquina.memoria)
            elif opcode == 'DUP':
                micro_list = traduzir_dup()
            elif opcode == 'BIPUSH':
                # arg pode ser decimal ou binário (string de 8 bits)
                if len(partes) > 1:
                    raw = partes[1]
                    byte_v = int(raw, 2) if set(raw) <= {'0','1'} and len(raw) == 8 else int(raw)
                else:
                    byte_v = 0
                micro_list = traduzir_bipush(byte_v)
            else:
                log.append(f"  [ERRO] Instrução desconhecida: '{opcode}'")
                continue

            log.append(f"  Traduzida em {len(micro_list)} microinstrução(ões):\n")

            # Executa cada microinstrução
            for j, palavra in enumerate(micro_list):
                log.append(f"  {'─'*56}")
                log.append(f"  Microinstrução {j+1}/{len(micro_list)}")
                info = self.maquina.executar_microinstrucao(palavra)
                log.append(self.maquina._formatar_info(info, mostrar_mem=True))

            log.append(f"\n  ── Memória após instrução {opcode} ──")
            log.append(self.maquina.memoria.dump())
            log.append(f"  ── Registradores após instrução {opcode} ──")
            log.append("  " + self.maquina.regs.linha_str())

        log.append("\n\n╔══════════════════════════════════════════════════════════╗")
        log.append("║                  EXECUÇÃO CONCLUÍDA                     ║")
        log.append("╚══════════════════════════════════════════════════════════╝")
        log.append("\n  ── MEMÓRIA DE DADOS (estado final) ──")
        log.append(self.maquina.memoria.dump())
        log.append("  ── REGISTRADORES (estado final) ──")
        log.append("  " + self.maquina.regs.linha_str())

        return "\n".join(log)


# ═══════════════════════════════════════════════════
#  ETAPA 1 — Simulador ULA 6 bits (arquivo .txt)
# ═══════════════════════════════════════════════════

def etapa1(caminho_programa: str, caminho_saida: str):
    """
    Etapa 1: lê arquivo de instruções de 6 bits e gera log.
    Cada linha: palavra de 6 bits  +  A B em decimal separados por espaço.
    Formato esperado:   110011 3 5
    (Se o arquivo tiver apenas a palavra de controle, A e B assumem 0)
    """
    ula = ULA6()
    log = []
    PC  = 0

    with open(caminho_programa, 'r') as f:
        linhas = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    log.append("PC   IR       A           B           S           Vai-um")
    log.append("-" * 60)

    for linha in linhas:
        partes = linha.split()
        IR = partes[0]
        A  = int(partes[1]) if len(partes) > 1 else 0
        B  = int(partes[2]) if len(partes) > 2 else 0

        S, vai_um = ula.executar(IR, A, B)
        log.append(f"{PC:<5}{IR}  {A:<12}{B:<12}{S:<12}{vai_um}")
        PC += 1

    resultado = "\n".join(log)
    with open(caminho_saida, 'w') as f:
        f.write(resultado)

    print(resultado)
    print(f"\nLog salvo em: {caminho_saida}")


# ═══════════════════════════════════════════════════
#  INTERFACE DE LINHA DE COMANDO
# ═══════════════════════════════════════════════════

AJUDA = """
Uso:  python mic1.py <modo> [argumentos]

Modos disponíveis:

  etapa1 <programa.txt> <saida.txt>
      Executa a ULA de 6 bits. Cada linha do programa deve ter:
        <ctrl_6bits>  <A_decimal>  <B_decimal>

  etapa2 <programa.txt> <registradores.txt> <saida.txt>
      Executa microinstruções de 21 bits com registradores.

  etapa3 <microinstrucoes.txt> <registradores.txt> <dados.txt> <saida.txt>
      Executa microinstruções de 23 bits com memória.

  ijvm <instrucoes.txt> <registradores.txt> <dados.txt> <saida.txt>
      Executa instruções IJVM (ILOAD x, DUP, BIPUSH byte).

  demo
      Executa uma demonstração embutida com todos os modos.
"""


def demo():
    """Demonstração completa com exemplos embutidos."""
    print("=" * 62)
    print("  DEMO: Simulador Mic-1 Modificada")
    print("=" * 62)

    # ── Demo Etapa 1 ─────────────────────────────────────────
    print("\n[ ETAPA 1 — ULA 6 bits ]\n")
    ula6 = ULA6()
    exemplos = [
        ("111100", 1, 1, "A + B  (ENA=ENB=1, F=11)"),
        ("110000", 5, 3, "A AND B"),
        ("110100", 5, 3, "A OR B"),
        ("110010", 7, 0, "NOT A"),
        ("001111", 0, 4, "B + 1  (ENB=1, INC=1)"),
    ]
    print(f"  {'Controle':<10} {'A':>6} {'B':>6}  →  {'S':>12}  {'vai_um':>6}  Descrição")
    print("  " + "-" * 60)
    for ctrl, a, b, desc in exemplos:
        S, c = ula6.executar(ctrl, a, b)
        print(f"  {ctrl:<10} {a:>6} {b:>6}  →  {S:>12}  {c:>6}  {desc}")

    # ── Demo Etapa 2 ─────────────────────────────────────────
    print("\n\n[ ETAPA 2 — ULA 8 bits + registradores ]\n")
    m = Mic1()
    m.regs.set('H',   10)
    m.regs.set('MDR', 20)
    m.regs.set('LV',   5)
    m.regs.set('SP',   3)
    m.regs.set('TOS',  7)
    m.regs.set('MAR',  0)

    print("  Registradores iniciais:")
    print("  " + m.regs.linha_str())

    # Instrução exemplo do enunciado: 001101001010000000000 (21 bits → 23 bits)
    # H = MDR, TOS = MDR
    instr_ex = "00110100101000000000000"
    print(f"\n  Executando: {instr_ex[:8]} | {instr_ex[8:17]} | {instr_ex[17:19]} | {instr_ex[19:]}")
    print("  (Sd=B, B=MDR → H=MDR e TOS=MDR)")
    info = m.executar_microinstrucao(instr_ex)
    print(m._formatar_info(info, mostrar_mem=False))

    # ── Demo Etapa 3 ─────────────────────────────────────────
    print("\n\n[ ETAPA 3 — Com memória de dados ]\n")
    m2 = Mic1()
    m2.regs.set('H',   5)
    m2.regs.set('LV',  2)
    m2.regs.set('SP',  1)
    m2.regs.set('TOS', 99)
    m2.regs.set('MAR', 0)
    m2.regs.set('MDR', 42)
    m2.memoria.dados = [10, 20, 30, 40, 50, 60, 70, 80]

    print("  Memória inicial:")
    print(m2.memoria.dump())
    print("  Registradores:")
    print("  " + m2.regs.linha_str())

    # SP = MAR = SP+1; wr  →  escreve MDR em mem[MAR]
    instr_wr = "00110101000001001010100"[0:23]
    # Ajuste: vamos usar uma instrução correta manualmente
    # ULA_B_MAIS_1, [MAR,SP], WRITE, SP
    instr_wr2 = _microinstr(ULA_B_MAIS_1, _ctrl_c_de_lista(['MAR','SP']), '10', _ctrl_b_de_nome('SP'))
    print(f"\n  Executando: MAR=SP=SP+1 ; wr")
    info2 = m2.executar_microinstrucao(instr_wr2)
    print(m2._formatar_info(info2, mostrar_mem=True))

    # ── Demo Entregável IJVM ─────────────────────────────────
    print("\n\n[ ENTREGÁVEL — Instruções IJVM ]\n")
    sim = SimuladorIJVM()
    sim.maquina.regs.set('LV',  0)
    sim.maquina.regs.set('SP',  7)
    sim.maquina.regs.set('TOS', 0)
    sim.maquina.regs.set('H',   0)
    sim.maquina.regs.set('MAR', 0)
    sim.maquina.regs.set('MDR', 0)
    sim.maquina.memoria.dados = [100, 200, 300, 400, 500, 600, 700, 800]

    # Cria arquivo temporário de instruções
    instrucoes_demo = "BIPUSH 00110011\nDUP\nILOAD 1\n"
    with open('/tmp/demo_instrucoes.txt', 'w') as f:
        f.write(instrucoes_demo)

    resultado = sim.executar_arquivo('/tmp/demo_instrucoes.txt')
    print(resultado)

    with open('/tmp/demo_saida.txt', 'w') as f:
        f.write(resultado)
    print(f"\n  Log completo salvo em: /tmp/demo_saida.txt")


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help', 'help'):
        print(AJUDA)
        sys.exit(0)

    modo = args[0].lower()

    if modo == 'demo':
        demo()

    elif modo == 'etapa1':
        if len(args) < 3:
            print("Uso: python mic1.py etapa1 <programa.txt> <saida.txt>")
            sys.exit(1)
        etapa1(args[1], args[2])

    elif modo == 'etapa2':
        if len(args) < 4:
            print("Uso: python mic1.py etapa2 <programa.txt> <registradores.txt> <saida.txt>")
            sys.exit(1)
        m = Mic1()
        m.carregar_registradores(args[2])
        resultado = m.executar_arquivo_microinstrucoes(args[1], mostrar_mem=False)
        with open(args[3], 'w') as f:
            f.write(resultado)
        print(resultado)
        print(f"\nLog salvo em: {args[3]}")

    elif modo == 'etapa3':
        if len(args) < 5:
            print("Uso: python mic1.py etapa3 <microinstrucoes.txt> <registradores.txt> <dados.txt> <saida.txt>")
            sys.exit(1)
        m = Mic1()
        m.carregar_registradores(args[2])
        m.carregar_memoria(args[3])
        resultado = m.executar_arquivo_microinstrucoes(args[1], mostrar_mem=True)
        with open(args[4], 'w') as f:
            f.write(resultado)
        print(resultado)
        print(f"\nLog salvo em: {args[4]}")

    elif modo == 'ijvm':
        if len(args) < 5:
            print("Uso: python mic1.py ijvm <instrucoes.txt> <registradores.txt> <dados.txt> <saida.txt>")
            sys.exit(1)
        sim = SimuladorIJVM()
        sim.carregar_registradores(args[2])
        sim.carregar_memoria(args[3])
        resultado = sim.executar_arquivo(args[1])
        with open(args[4], 'w') as f:
            f.write(resultado)
        print(resultado)
        print(f"\nLog salvo em: {args[4]}")

    else:
        print(f"Modo desconhecido: '{modo}'")
        print(AJUDA)
        sys.exit(1)