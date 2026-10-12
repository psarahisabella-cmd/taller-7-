"""Pruebas del decodificador de 7 segmentos (pytest).

La lógica vive en sevensegdec.py; aquí solo se verifica.
EXPECTED está escrita a mano, independiente de table.txt, para que un error
en la tabla (o en el decodificador) haga fallar las pruebas.
"""
from pathlib import Path

import pytest
from myhdl import Signal, Simulation, delay, instance, intbv

from sevensegdec import read_table, sevensegdec, sevensegdec_nexys

TABLE_FILE = Path(__file__).parent / "table.txt"

# orden de bits: abcdefg (a = bit más a la izquierda)
EXPECTED = (
    "1111110",  # 0
    "0110000",  # 1  (derecha: b,c)
    "1101101",  # 2
    "1111001",  # 3
    "0110011",  # 4
    "1011011",  # 5
    "1011111",  # 6  (cerrado: con a)
    "1110000",  # 7
    "1111111",  # 8
    "1111011",  # 9  (cerrado: con d)
    "0000001",  # 10 guion         g
    "0001000",  # 11 subrayado     d
    "1000000",  # 12 sobrerrayado  a
    "1001001",  # 13 tres barras   a,d,g
    "1100011",  # 14 cuadro alto   a,b,f,g
    "0110110",  # 15 dos verticales b,c,e,f
)
CASES = [(n, int(p, 2)) for n, p in enumerate(EXPECTED)]
IDS = [f"0x{n:X}" for n, _ in CASES]


def decode(table, value, invert=False):
    """Simula el decodificador con una entrada y devuelve sseg como int."""
    bcd, sseg = Signal(intbv(0)[4:]), Signal(intbv(0)[7:])
    uut = sevensegdec(bcd, sseg, table, invert)
    out = []

    @instance
    def stimulus():
        bcd.next = value
        yield delay(10)
        out.append(int(sseg))

    Simulation(uut, stimulus).run(quiet=1)
    return out[0]


@pytest.fixture(scope="module")
def table():
    return read_table(str(TABLE_FILE))


# --- tabla -----------------------------------------------------------------

def test_table_file_format():
    lines = TABLE_FILE.read_text().split("\n")
    assert len(lines) == 16, "16 líneas, sin línea en blanco final"
    assert all(len(x) == 7 and set(x) <= {"0", "1"} for x in lines)


def test_table_patterns_are_unique(table):
    assert len(set(table)) == 16


def test_digit_conventions(table):
    a, b, c, d, e, f, g = (1 << k for k in range(6, -1, -1))
    assert table[1] == b | c            # 1 a la derecha
    assert table[6] & a                 # 6 cerrado
    assert table[9] & d                 # 9 cerrado
    assert table[8] == 0x7F             # 8 enciende todo


def test_custom_symbols_are_not_digits(table):
    assert not set(table[10:]) & set(table[:10])


# --- decodificador: 16 casos -------------------------------------------------

@pytest.mark.parametrize("n, pattern", CASES, ids=IDS)
def test_table_entry(table, n, pattern):
    assert table[n] == pattern


@pytest.mark.parametrize("n, pattern", CASES, ids=IDS)
def test_decoder_output(table, n, pattern):
    assert decode(table, n) == pattern


@pytest.mark.parametrize("n, pattern", CASES, ids=IDS)
def test_decoder_inverted(table, n, pattern):
    assert decode(table, n, invert=True) == ~pattern & 0x7F


# --- las pruebas deben detectar errores --------------------------------------

@pytest.mark.parametrize("n, pattern", CASES, ids=IDS)
def test_detects_flipped_bit(table, n, pattern):
    bad = list(table)
    bad[n] ^= 0b0000100  # un solo segmento mal
    assert decode(tuple(bad), n) != pattern


def test_read_table_rejects_bad_files(tmp_path):
    for content in ("1111110\n" * 15, "1111110\n" * 15 + "111111\n", "x" * 7 + "\n" * 16):
        f = tmp_path / "bad.txt"
        f.write_text(content)
        with pytest.raises(ValueError):
            read_table(str(f))


# --- VHDL --------------------------------------------------------------------

def test_vhdl_contains_table(table, tmp_path):
    top = sevensegdec_nexys(
        Signal(intbv(0)[4:]), Signal(intbv(0)[7:]), Signal(intbv(0)[4:]),
        Signal(intbv(0)[8:]), table, Signal(False),
    )
    top.convert(hdl="VHDL", path=str(tmp_path))
    vhd = (tmp_path / "sevensegdec_nexys.vhd").read_text()
    for n, pattern in CASES:
        assert f'ssegout <= "{pattern:07b}"' in vhd, f"entrada {n}"
