# Taller: decodificador de 7 segmentos (MyHDL → VHDL)

Decodificador combinacional de 4 bits (`bcd`, 0x0–0xF) a 7 bits (`sseg`, segmentos `abcdefg`), modelado en MyHDL, simulado, convertido a VHDL y verificado con pytest. Base: `sevensegdec.py` del curso.

## Requisitos e instalación

- Python 3 y `pip`. Probado con Python 3.14.0, MyHDL 0.11.52, pytest 9.1.1 (Windows 11).
- Opcional, para ver el VCD: gtkwave o <https://vc.drom.io/>.

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## Estructura

```
table.txt              tabla de decodificación (16 líneas x 7 bits, orden abcdefg)
sevensegdec.py         decodificador (LUT), wrapper Nexys4, read_table, CLI
test_sevensegdec.py    pruebas pytest (lógica separada de las pruebas)
requirements.txt       myhdl, pytest
hdl/                   salida generada: sevensegdec_nexys.vhd, pck_myhdl_011.vhd,
                       sevensegdec_tb.vcd, sim_output.txt
```

## Arquitectura

```
bcd[3:0] ──► LUT: decod_table[int(bcd)] ──► ssegout[6:0] ──► (invert?) ──► sseg[6:0]
              (always_comb, sin reloj)                        ~ssegout / ssegout
```

- `sevensegdec`: el decodificador. Una LUT indexada por `bcd` y una inversión opcional (`invert`) para displays activos en bajo.
- `sevensegdec_nexys`: envoltura para la placa Nexys4 DDR (copia `bcd` a los LEDs y enciende solo el primer display). Es la entidad de nivel superior que se convierte a VHDL.
- `read_table`: lee `table.txt`. **Cambio respecto al script base:** ignora líneas en blanco, valida 16 líneas de 7 bits 0/1 y lanza `ValueError` en lugar de devolver una tabla de ceros en silencio.
- El testbench original (`sevensegdec_tb`) se conserva solo para generar el VCD con `--simulation`. Las verificaciones reales están en `test_sevensegdec.py`.

## Tabla de decodificación

Convención: `a` arriba, `b` superior derecho, `c` inferior derecho, `d` abajo, `e` inferior izquierdo, `f` superior izquierdo, `g` medio. Cada línea de `table.txt` es `abcdefg`; el bit `a` es el más significativo de `sseg`. `1` = segmento encendido (activo en alto).

**Decisiones de diseño** (el enunciado las deja abiertas): el **1 va a la derecha** (segmentos `b`,`c`), el **6 es cerrado** (enciende `a`) y el **9 es cerrado** (enciende `d`).

| Entrada | Símbolo | Segmentos | `abcdefg` | Justificación |
|---|---|---|---|---|
| 0x0 | 0 | a b c d e f | `1111110` | estándar |
| 0x1 | 1 (derecha) | b c | `0110000` | estándar, a la derecha |
| 0x2 | 2 | a b d e g | `1101101` | estándar |
| 0x3 | 3 | a b c d g | `1111001` | estándar |
| 0x4 | 4 | b c f g | `0110011` | estándar |
| 0x5 | 5 | a c d f g | `1011011` | estándar |
| 0x6 | 6 cerrado | a c d e f g | `1011111` | con segmento superior |
| 0x7 | 7 | a b c | `1110000` | estándar |
| 0x8 | 8 | a b c d e f g | `1111111` | estándar |
| 0x9 | 9 cerrado | a b c d f g | `1111011` | con segmento inferior |
| 0xA | `-` guion | g | `0000001` | la barra media sola es el signo menos |
| 0xB | `_` subrayado | d | `0001000` | la barra inferior sola es un subrayado |
| 0xC | `¯` sobrerrayado | a | `1000000` | la barra superior sola es un sobrerrayado |
| 0xD | `≡` tres barras | a d g | `1001001` | las tres horizontales juntas; no se parece a ningún dígito ni letra |
| 0xE | `°` cuadro alto | a b f g | `1100011` | cuadrado en la mitad superior, como el símbolo de grado |
| 0xF | `‖` dos verticales | b c e f | `0110110` | dos barras verticales (símbolo de pausa) |

Las entradas 0xA–0xF no usan las letras A–F y evitan sus formas habituales (A=`abcefg`, b=`cdefg`, C=`adef`, d=`bcdeg`, E=`adefg`, F=`aefg`). Los 16 patrones son distintos y los símbolos 0xA–0xF no coinciden con ningún dígito (lo verifican las pruebas).

## Ejecución

Comando exacto usado (desde la carpeta `hdl/`, donde se escriben los archivos generados):

```bash
cd hdl
python ../sevensegdec.py --table ../table.txt --simulation
```

- Sin `--simulation` solo convierte a HDL. Con `--verilog` convierte a Verilog en lugar de VHDL (no usado en este trabajo).
- `--invert` (solo simulación) invierte las salidas.
- Si ya existe un `sevensegdec_tb.vcd`, MyHDL renombra el anterior con una marca de tiempo.

Salida real (`hdl/sim_output.txt`):

```
<class 'myhdl.StopSimulation'>: No more events
Simulation done.
```

El mensaje `StopSimulation: No more events` es el fin normal de la simulación (no hay más eventos). La línea `Conversion done (VHDL).` aparece después.

### Qué verifica el testbench y qué es `sseg`

El testbench aplica los 16 valores de `bcd` (cada 10 ns), espera a que la salida se estabilice y compara `sseg` con la entrada de la tabla. Solo imprime `ERROR` cuando difieren. Como el decodificador usa la misma tabla que el testbench, con una tabla consistente nunca difieren y no aparece ningún `ERROR` (0 en esta ejecución). `sseg` son 7 bits, uno por segmento, en orden `abcdefg` (bit 6 = `a`, bit 0 = `g`); un `1` enciende el segmento. El testbench original no hace fallar la ejecución cuando hay un error: por eso se migró a pytest.

### Interpretación del VCD (`hdl/sevensegdec_tb.vcd`)

Valores extraídos del VCD generado (señales `bcd`, `sseg`; `ssegout` es idéntica porque `invert=False`). Cada valor se mantiene 10 ns:

| t (ns) | bcd | sseg | t (ns) | bcd | sseg |
|---|---|---|---|---|---|
| 0 | 0000 | 1111110 | 80 | 1000 | 1111111 |
| 10 | 0001 | 0110000 | 90 | 1001 | 1111011 |
| 20 | 0010 | 1101101 | 100 | 1010 | 0000001 |
| 30 | 0011 | 1111001 | 110 | 1011 | 0001000 |
| 40 | 0100 | 0110011 | 120 | 1100 | 1000000 |
| 50 | 0101 | 1011011 | 130 | 1101 | 1001001 |
| 60 | 0110 | 1011111 | 140 | 1110 | 1100011 |
| 70 | 0111 | 1110000 | 150 | 1111 | 0110110 |

`sseg` cambia en el mismo instante que `bcd` (lógica combinacional, sin reloj ni retardo de registro) y no tiene valores intermedios. Al final (t = 160) queda en `0110110`, el valor de 0xF.

> **Pendiente (lo hace el estudiante):** abrir el VCD en gtkwave o vc.drom.io y adjuntar las capturas de pantalla; no se pudieron tomar desde este entorno.

## VHDL generado

Archivos: [`hdl/sevensegdec_nexys.vhd`](hdl/sevensegdec_nexys.vhd) (entidad) y [`hdl/pck_myhdl_011.vhd`](hdl/pck_myhdl_011.vhd) (paquete de apoyo de MyHDL).

- Puertos: `bcd` (in, 4 bits), `sseg` (out, 7), `bcdled` (out, 4), `ssanodes` (out, 8) e `invert` (in, 1 bit). `invert` queda como puerto de entrada porque en la conversión se pasa como `Signal(False)` sin conectar; en el hardware se puede cambiar con un interruptor.
- La LUT se convierte en un `process (bcd)` con un `case to_integer(bcd)` de 16 ramas, una por fila de la tabla (la última rama es `when others` y corresponde a 0xF). Un proceso con `case` y sin reloj ni registros es lógica combinacional: la herramienta de síntesis lo implementa como una tabla de verdad de 4 entradas y 7 salidas (un LUT de 4 entradas por segmento en una FPGA).
- Un segundo proceso aplica `not` a la salida si `invert = '1'` (displays activos en bajo).
- `bcdled <= bcd` y `ssanodes <= 254` (`11111110`, solo se enciende el primer display) son asignaciones concurrentes.

## Pruebas

```bash
python -m pytest -v
```

Resultado de la última ejecución: **70 passed**. Las pruebas cubren:

- Formato de `table.txt` (16 líneas, 7 bits, patrones únicos) y las decisiones 1 / 6 / 9.
- Los 16 casos parametrizados, tres veces: entrada de la tabla, salida simulada del decodificador y salida con `invert=True`.
- Detección de errores: voltear un bit de cualquier entrada hace fallar la prueba (16 casos), y `read_table` rechaza archivos con menos líneas, líneas cortas o caracteres que no sean 0/1.
- Que cada uno de los 16 patrones aparezca en el VHDL generado (en un directorio temporal).

`EXPECTED` está escrita a mano dentro de las pruebas, independiente de `table.txt`. Prueba negativa realizada: con la línea 8 de la tabla cambiada de `1110000` a `1110001`, fallaron 4 pruebas (`test_table_entry[0x7]`, `test_decoder_output[0x7]`, `test_decoder_inverted[0x7]` y `test_vhdl_contains_table`); tras restaurar el archivo volvieron a pasar las 70.

## Validación

| Aspecto | Estado |
|---|---|
| Tabla de 16 líneas × 7 bits, decisiones 1/6/9 declaradas, 0xA–0xF sin letras A–F y justificados | Hecho |
| Simulación con la tabla propia, sin `ERROR`, VCD generado y revisado | Hecho (valores verificados contra la tabla) |
| VHDL generado y coherente con `table.txt` (16/16 ramas) | Hecho (comprobado por script y por pytest) |
| Pruebas pytest parametrizadas, lógica separada | Hecho (70 pasan) |
| Compilar o simular el VHDL con una herramienta externa (p. ej. GHDL) | **No verificado**: no hay GHDL instalado |
| Capturas del VCD en gtkwave / vc.drom.io | **Pendiente** (las toma el estudiante) |
| Verilog (`--verilog`) | No ejecutado (no es requisito; se eligió VHDL) |
| Aspecto visual de los símbolos 0xA–0xF en un display real | No verificado (solo se razonó sobre los segmentos) |
| Subida al repositorio propio de GitHub | Pendiente (la hace el estudiante) |
