from dataclasses import dataclass
from typing import Mapping, TypedDict

from traces_analyzer.preprocessing.instruction import Instruction
from traces_analyzer.preprocessing.instruction_io import InstructionIOSpec

CallDataNew = TypedDict(
    "CallDataNew",
    {
        "address": str,
        "input": str,
    },
)


@dataclass(frozen=True)
class CALL(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=7,
        memory_input_offset_arg=3,
        memory_input_size_arg=4,
    )
    data: CallDataNew

    def __post_init__(self):
        self._init_data({"address": self.stack_inputs[1], "input": self.memory_input})


@dataclass(frozen=True)
class STATICCALL(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=6,
        memory_input_offset_arg=2,
        memory_input_size_arg=3,
    )
    data: CallDataNew

    def __post_init__(self):
        self._init_data({"address": self.stack_inputs[1], "input": self.memory_input})


@dataclass(frozen=True)
class DELEGATECALL(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=6,
        memory_input_offset_arg=2,
        memory_input_size_arg=3,
    )
    data: CallDataNew

    def __post_init__(self):
        self._init_data({"address": self.stack_inputs[1], "input": self.memory_input})


@dataclass(frozen=True)
class CALLCODE(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=7,
        memory_input_offset_arg=3,
        memory_input_size_arg=4,
    )
    data: CallDataNew

    def __post_init__(self):
        self._init_data({"address": self.stack_inputs[1], "input": self.memory_input})


@dataclass(frozen=True)
class STOP(Instruction):
    pass


@dataclass(frozen=True)
class RETURN(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=2)


@dataclass(frozen=True)
class REVERT(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=2)


@dataclass(frozen=True)
class SELFDESTRUCT(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=1)


@dataclass(frozen=True)
class SLOAD(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=1, stack_output_count=1)


@dataclass(frozen=True)
class POP(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=1)


@dataclass(frozen=True)
class JUMPDEST(Instruction):
    pass


@dataclass(frozen=True)
class PUSH0(Instruction):
    io_specification = InstructionIOSpec(stack_output_count=1)


@dataclass(frozen=True)
class LOG0(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=2, memory_input_offset_arg=0, memory_input_size_arg=1)


@dataclass(frozen=True)
class LOG1(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=3, memory_input_offset_arg=0, memory_input_size_arg=1)


@dataclass(frozen=True)
class LOG2(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=4, memory_input_offset_arg=0, memory_input_size_arg=1)


@dataclass(frozen=True)
class LOG3(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=5, memory_input_offset_arg=0, memory_input_size_arg=1)


@dataclass(frozen=True)
class LOG4(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=6, memory_input_offset_arg=0, memory_input_size_arg=1)


_INSTRUCTIONS: Mapping[int, type[Instruction]] = {
    0x0: STOP,
    0x50: POP,
    0x54: SLOAD,
    0x5B: JUMPDEST,
    0x5F: PUSH0,
    0xA0: LOG0,
    0xA1: LOG1,
    0xA2: LOG2,
    0xA3: LOG3,
    0xA4: LOG4,
    0xF1: CALL,
    0xF2: CALLCODE,
    0xF3: RETURN,
    0xF4: DELEGATECALL,
    0xFA: STATICCALL,
    0xFD: REVERT,
    0xFF: SELFDESTRUCT,
}

_INSTRUCTION_CLS_TO_OPCODE = dict((cls, op) for op, cls in _INSTRUCTIONS.items())


def get_instruction_class(opcode: int):
    return _INSTRUCTIONS.get(opcode)


def op_from_class(instruction_cls: type[Instruction]) -> int:
    return _INSTRUCTION_CLS_TO_OPCODE[instruction_cls]
