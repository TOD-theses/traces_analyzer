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


class Unknown(Instruction):
    pass


class CALL(Instruction):
    gas: str
    address: str
    value: str
    argsOffset: str
    argsSize: str
    retOffset: str
    retSize: str

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        stack = event.stack
        self.gas = stack[-1]
        self.address = stack[-2]
        self.value = stack[-3]
        self.argsOffset = stack[-4]
        self.argsSize = stack[-5]
        self.retOffset = stack[-6]
        self.retSize = stack[-7]


class STATICCALL(Instruction):
    gas: str
    address: str
    argsOffset: str
    argsSize: str
    retOffset: str
    retSize: str

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        stack = event.stack
        self.gas = stack[-1]
        self.address = stack[-2]
        self.argsOffset = stack[-3]
        self.argsSize = stack[-4]
        self.retOffset = stack[-5]
        self.retSize = stack[-6]


class STOP(Instruction):
    pass


class RETURN(Instruction):
    pass


class SLOAD(Instruction):
    key: str
    result: str | None

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.key = event.stack[-1]
        self.result = next_event.stack[-1]


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
