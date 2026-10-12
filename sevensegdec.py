#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seven segment decoder: Example script to generate a seven segment decoder
based on a lookup table (LUT). It includes testing and conversion to VHDL/verilog
"""

from myhdl import *
import argparse

# implementation

@block
def sevensegdec(bcd: Signal, sseg: Signal, decod_table: tuple, invert: bool = False):
    """Seven segment decoder"""

    # internal signal for optional bit inversion
    ssegout = Signal(intbv(0)[7:])

    @always_comb
    def logic():
        """LUT implementation: based on a decoder table"""
        ssegout.next = decod_table[int(bcd)]

    @always_comb
    def invertproc():
        """Inverting process for output"""
        if invert:
            sseg.next = ~ssegout
        else:
            sseg.next = ssegout
        
    # this will include logic and invertproc
    return instances()
    
# testbench

@block
def sevensegdec_tb(decod_table: tuple, invert: bool = False):
    """Testbench for Seven segment decoder"""

    # Testbench signals
    bcd_tb = Signal(intbv(0)[4:])
    sseg_tb = Signal(intbv(0)[7:])
    
    uut = sevensegdec(bcd_tb, sseg_tb, decod_table, invert)
    
    @instance
    def stimulus():
        """Stimulus generation"""

        # run for each possible value
        for bcd_in in range(len(decod_table)):
            # stimulus input
            bcd_tb.next = bcd_in
            yield delay(10)
            
            # output check
            sseg_readed = int(sseg_tb.val)
            sseg_expect = decod_table[int(bcd_tb.val)]
            if sseg_readed != sseg_expect:
                print(f"ERROR: on ({now()}) bcd input '{bcd_tb.val}': expected differ {sseg_expect:07b} != {sseg_readed:07b}")
            
    # this will include uut and stimulus
    return instances()

@block
def sevensegdec_nexys(bcd: Signal, sseg: Signal, bcdled: Signal, ssanodes: Signal, decod_table: tuple, invert: bool = False):
    """Envelope for running a demo in the Nexys4 DDR board for the Seven segment decoder"""

    # Main decoder instance
    ssdec = sevensegdec(bcd, sseg, decod_table, invert)

    @always_comb
    def logic():
        """Process to fill the LEDs for switches and display anodes"""
        bcdled.next = bcd
        ssanodes.next = intbv(0xfe)[8:] # only turn on first display, it is turned on with 0.

    # this will include ssdec and logic
    return instances()

def read_table(table_file: str) -> tuple:
    """Read the decoder table from text file:
        * Each line contains a string with 0s and 1s, in order "abcdefg"
        * It must contain 16 lines, one for each 4-bit digit
    """
    if table_file == "":
        return tuple([0 for x in range(16)])
    with open(table_file) as f:
        lines = [x.strip() for x in f.readlines() if x.strip() != ""]
    # fail loudly: a silent zero table would hide a wrong file
    if len(lines) != 16 or any(len(x) != 7 or set(x) - {"0", "1"} for x in lines):
        raise ValueError(f"{table_file}: expected 16 lines of 7 bits (0/1)")
    return tuple([int(x, base=2) for x in lines])
    
def run():
    """Entrypoint"""
    parser = argparse.ArgumentParser(description="Seven segment decoder")
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="If enabled, run simulation in python",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the outputs (simulation only)",
    )
    parser.add_argument(
        "--verilog",
        action="store_true",
        help="Convert to verilog instead of VHDL",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="",
        help="Decoder table to include")
    args = parser.parse_args()

    if args.table != "":
        table = read_table(args.table)
    else:
        print("No table entered, put zero table by default.")
        table = read_table("")

    if args.simulation:
        # simulation
        tb = sevensegdec_tb(table, args.invert)
        tb.config_sim(trace=True)
        tb.run_sim()
        print("Simulation done.")
    
    # conversion

    # Signal list for sevensegdec_nexys
    ss_sig = {
        "bcd": Signal(intbv(0)[4:]),
        "sseg": Signal(intbv(0)[7:]),
        "bcdled": Signal(intbv(0)[4:]),
        "ssanodes": Signal(intbv(0)[8:]),
        "invert": Signal(False),
        "decod_table": table
        }
    sscomponent = sevensegdec_nexys(**ss_sig)

    # which language output
    if args.verilog:
        langout = "verilog"
    else:
        langout = "VHDL"
    sscomponent.convert(hdl=langout)

    print(f"Conversion done ({langout}).")
    
if __name__ == "__main__":
    run()