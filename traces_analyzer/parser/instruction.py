from dataclasses import dataclass
from typing import ClassVar

from typing_extensions import Mapping

from traces_analyzer.parser.call_frame import CallFrame
from traces_analyzer.parser.instruction_io import InstructionIOSpec


@dataclass(frozen=True)
class Instruction:
    opcode: int
    name: str
    program_counter: int
    call_frame: CallFrame
    stack_inputs: tuple[str, ...]
    stack_outputs: tuple[str, ...]
    memory_input: str | None
    memory_output: str | None
    data: Mapping[str, object]
    io_specification: ClassVar[InstructionIOSpec] = InstructionIOSpec()

    def _init_data(self, data: Mapping[str, object]):
        # set data despite being frozen
        object.__setattr__(self, "data", data)

    # TODO: __str__
