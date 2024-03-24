from abc import ABC

from typing_extensions import Self

from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.mnemonics import opcode_to_name

INSTRUCTION_UNKNOWN_NAME = "UNKNOWN"


class Instruction(ABC):
    # statically defined opcode for the class
    # will be overwritten by the trace events opcode on an instance level
    opcode: int = -1

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        self.opcode = event.op
        self.name = opcode_to_name(self.opcode, INSTRUCTION_UNKNOWN_NAME)
        self.program_counter = event.pc
        self.call_frame = call_frame

    @classmethod
    def from_event(cls, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame) -> Self:
        return cls(event, next_event, call_frame)

    def __str__(self) -> str:
        return (
            "<Instruction"
            f" name={self.name}"
            f" op={hex(self.opcode)}"
            f" location={self.program_counter}@{self.call_frame.address}"
            ">"
        )


class StackInstruction(Instruction):
    """Instruction that takes arguments from the stack and/or pushes to the next events stack"""

    stack_input_count = 0
    # stack outputs are only parsed from the next events stack
    # so we can't use this for eg CALL, where the output is only known many events later
    stack_output_count = 0

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.stack_inputs: tuple[str, ...] = ()
        self.stack_outputs: tuple[str, ...] = ()

        if self.stack_input_count:
            self.stack_inputs = tuple(reversed(event.stack[-self.stack_input_count :]))
        if self.stack_output_count:
            self.stack_outputs = tuple(reversed(next_event.stack[-self.stack_output_count :]))


class Unknown(Instruction):
    pass


class CALL(StackInstruction):
    opcode = 0xF1
    stack_input_count = 7

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.gas = self.stack_inputs[0]
        self.address = self.stack_inputs[1]
        self.value = self.stack_inputs[2]
        self.args_offset = self.stack_inputs[3]
        self.args_size = self.stack_inputs[4]
        self.ret_offset = self.stack_inputs[5]
        self.ret_size = self.stack_inputs[6]


class STATICCALL(StackInstruction):
    opcode = 0xFA
    stack_input_count = 6

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.gas = self.stack_inputs[0]
        self.address = self.stack_inputs[1]
        self.args_offset = self.stack_inputs[2]
        self.args_size = self.stack_inputs[3]
        self.ret_offset = self.stack_inputs[4]
        self.ret_size = self.stack_inputs[5]


class STOP(Instruction):
    opcode = 0x0


class RETURN(StackInstruction):
    opcode = 0xF3
    stack_input_count = 2


class REVERT(StackInstruction):
    opcode = 0xFD
    stack_input_count = 2


class SELFDESTRUCT(StackInstruction):
    opcode = 0xFF
    stack_input_count = 1


class SLOAD(StackInstruction):
    opcode = 0x54
    stack_input_count = 1
    stack_output_count = 1

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.key = self.stack_inputs[0]
        self.result = self.stack_outputs[0]


DEFINED_INSTRUCTIONS = [STOP, SLOAD, CALL, RETURN, REVERT, SELFDESTRUCT, STATICCALL]
OPCODE_TO_INSTRUCTION_TYPE: dict[int, type[Instruction]] = dict((i.opcode, i) for i in DEFINED_INSTRUCTIONS)

# sanity check that we always specified the opcode
for opcode, instruction_type in OPCODE_TO_INSTRUCTION_TYPE.items():
    if opcode < 0:
        raise Exception(f"Please specify the opcode for {instruction_type} (found {opcode})")


def parse_instruction(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
    instruction_type = instruction_type_from_opcode(event.op)

    return instruction_type.from_event(event, next_event, call_frame)


def instruction_type_from_opcode(opcode: int) -> type[Instruction]:
    return OPCODE_TO_INSTRUCTION_TYPE.get(opcode, Unknown)
