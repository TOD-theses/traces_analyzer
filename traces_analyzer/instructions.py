from abc import ABC
from dataclasses import dataclass
from typing import Dict

from typing_extensions import Self

from traces_analyzer.call_frame import CallFrame
from traces_analyzer.trace_reader import TraceEvent


@dataclass
class Instruction(ABC):
    opcode: int
    program_counter: int
    call_frame: CallFrame

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        self.opcode = event.op
        self.program_counter = event.pc
        self.call_frame = call_frame

    @classmethod
    def from_event(cls, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame) -> Self:
        return cls(event, next_event, call_frame)


class StackInstruction(Instruction):
    """Instruction that takes arguments from the stack and/or pushes to the next events stack"""

    stack_input_count = 0
    # stack outputs are only parsed from the next events stack
    # so we can't use this for eg CALL, where the output is only known many events later
    stack_output_count = 0
    stack_inputs: tuple[str, ...] = ()
    stack_outputs: tuple[str, ...] = ()

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)

        if self.stack_input_count:
            self.stack_inputs = tuple(reversed(event.stack[-self.stack_input_count :]))
        if self.stack_output_count:
            self.stack_outputs = tuple(reversed(next_event.stack[-self.stack_output_count :]))


class Unknown(Instruction):
    pass


class CALL(StackInstruction):
    stack_input_count = 7
    gas: str
    address: str
    value: str
    args_offset: str
    args_size: str
    ret_offset: str
    ret_size: str

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
    stack_input_count = 6
    gas: str
    address: str
    args_offset: str
    args_size: str
    ret_offset: str
    ret_size: str

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.gas = self.stack_inputs[0]
        self.address = self.stack_inputs[1]
        self.args_offset = self.stack_inputs[2]
        self.args_size = self.stack_inputs[3]
        self.ret_offset = self.stack_inputs[4]
        self.ret_size = self.stack_inputs[5]


class STOP(Instruction):
    pass


class RETURN(StackInstruction):
    stack_input_count = 2


class SLOAD(StackInstruction):
    stack_input_count = 1
    stack_output_count = 1
    key: str
    result: str

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.key = self.stack_inputs[0]
        self.result = self.stack_outputs[0]


OPCODE_TO_INSTRUCTION_TYPE: Dict[int, type[Instruction]] = {
    0x0: STOP,
    0x54: SLOAD,
    0xF1: CALL,
    0xF3: RETURN,
    0xFA: STATICCALL,
}


def parse_instruction(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
    instruction_type = instruction_type_from_opcode(event.op)

    return instruction_type.from_event(event, next_event, call_frame)


def instruction_type_from_opcode(opcode: int) -> type[Instruction]:
    return OPCODE_TO_INSTRUCTION_TYPE.get(opcode, Unknown)
