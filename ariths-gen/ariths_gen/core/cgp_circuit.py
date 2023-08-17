from ariths_gen.wire_components import (
    Wire,
    ConstantWireValue0,
    ConstantWireValue1,
    Bus
)
from ariths_gen.core.arithmetic_circuits import (
    GeneralCircuit
)

from ariths_gen.core.logic_gate_circuits import (
    MultipleInputLogicGate
)
from ariths_gen.one_bit_circuits.one_bit_components import (
    HalfAdder,
    FullAdder
)
from ariths_gen.one_bit_circuits.logic_gates import (
    AndGate,
    NandGate,
    OrGate,
    NorGate,
    XorGate,
    XnorGate,
    NotGate
)
import re


class UnsignedCGPCircuit(GeneralCircuit):
    """Unsigned circuit variant that loads CGP code and is able to export it to C/verilog/Blif/CGP."""

    def __init__(self, code: str, input_widths: list, prefix: str = "", name: str = "cgp", **kwargs):
        cgp_prefix, cgp_core, cgp_outputs = re.match(
            r"{(.*)}(.*)\(([^()]+)\)", code).groups()

        c_in, c_out, c_rows, c_cols, c_ni, c_no, c_lback = map(
            int, cgp_prefix.split(","))

        assert sum(
            input_widths) == c_in, f"CGP input width {c_in} doesn't match input_widths {input_widths}"

        inputs = [Bus(N=bw, prefix=f"input_{chr(i)}")
                  for i, bw in enumerate(input_widths, start=0x61)]

        # Adding values to the list
        self.vals = {}
        j = 2  # Start from two, 0=False, 1=True
        for iid, bw in enumerate(input_widths):
            for i in range(bw):
                assert j not in self.vals
                self.vals[j] = inputs[iid].get_wire(i)
                j += 1

        super().__init__(prefix=prefix, name=name, out_N=c_out, inputs=inputs, **kwargs)
        cgp_core = cgp_core.split(")(")

        i = 0
        for definition in cgp_core:
            i, in_a, in_b, fn = map(int, re.match(
                r"\(?\[(\d+)\](\d+),(\d+),(\d+)\)?", definition).groups())

            assert in_a < i
            assert in_b < i
            comp_set = dict(prefix=f"{self.prefix}_core_{i:03d}", parent_component=self)

            a, b = self._get_wire(in_a), self._get_wire(in_b)
            if fn == 0:  # IDENTITY
                o = a
            elif fn == 1:  # NOT
                o = self.add_component(NotGate(a, **comp_set)).out
            elif fn == 2:  # AND
                o = self.add_component(AndGate(a, b, **comp_set)).out
            elif fn == 3:  # OR
                o = self.add_component(OrGate(a, b, **comp_set)).out
            elif fn == 4:  # XOR
                o = self.add_component(XorGate(a, b, **comp_set)).out
            elif fn == 5:  # NAND
                o = self.add_component(NandGate(a, b, **comp_set)).out
            elif fn == 6:  # NOR
                o = self.add_component(NorGate(a, b, **comp_set)).out
            elif fn == 7:  # XNOR
                o = self.add_component(XnorGate(a, b, **comp_set)).out
            elif fn == 8:  # TRUE
                o = ConstantWireValue1()
            elif fn == 9:  # FALSE
                o = ConstantWireValue0()

            assert i not in self.vals
            self.vals[i] = o

        # Output connection
        for i, o in enumerate(map(int, cgp_outputs.split(","))):
            w = self._get_wire(o)
            self.out.connect(i, w)

    @staticmethod
    def get_inputs_outputs(code: str):
        cgp_prefix, cgp_core, cgp_outputs = re.match(
            r"{(.*)}(.*)\(([^()]+)\)", code).groups()

        c_in, c_out, c_rows, c_cols, c_ni, c_no, c_lback = map(
            int, cgp_prefix.split(","))

        return c_in, c_out

    def _get_wire(self, i):
        if i == 0:
            return ConstantWireValue0()
        if i == 1:
            return ConstantWireValue1()
        return self.vals[i]


class SignedCGPCircuit(UnsignedCGPCircuit):
    """Signed circuit variant that loads CGP code and is able to export it to C/verilog/Blif/CGP."""
    def __init__(self, code: str, input_widths: list, prefix: str = "", name: str = "cgp", **kwargs):
        super().__init__(code=code, input_widths=input_widths, prefix=prefix, name=name, signed=True, **kwargs)
        self.c_data_type = "int64_t"
