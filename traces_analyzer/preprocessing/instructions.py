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

    stack_input_count = 0
    # stack outputs are only parsed from the next events stack
    # so we can't use this for eg CALL, where the output is only known many events later
    stack_output_count = 0

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        self.opcode = event.op
        self.name = opcode_to_name(self.opcode, INSTRUCTION_UNKNOWN_NAME)
        self.program_counter = event.pc
        self.call_frame = call_frame

        self._parse_inputs(event, next_event)

    def _parse_inputs(self, event: TraceEvent, next_event: TraceEvent):
        self.stack_inputs: tuple[str, ...] = ()
        self.stack_outputs: tuple[str, ...] = ()
        self.memory_input: str | None = None
        self.memory_output: str | None = None

        if self.stack_input_count:
            self.stack_inputs = tuple(reversed(event.stack[-self.stack_input_count :]))
        if self.stack_output_count:
            self.stack_outputs = tuple(reversed(next_event.stack[-self.stack_output_count :]))

    @classmethod
    def from_events(cls, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame) -> Self:
        return cls(event, next_event, call_frame)

    def __str__(self) -> str:
        return (
            "<Instruction"
            f" name={self.name}"
            f" op={hex(self.opcode)}"
            f" location={self.program_counter}@{self.call_frame.code_address}"
            ">"
        )


class Unknown(Instruction):
    pass


class CALL(Instruction):
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

        self.memory_input = event.mem_at(int(self.args_offset, 16), int(self.args_size, 16))


class STATICCALL(Instruction):
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

        self.memory_input = event.mem_at(int(self.args_offset, 16), int(self.args_size, 16))


class DELEGATECALL(Instruction):
    opcode = 0xF4
    stack_input_count = 6

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.gas = self.stack_inputs[0]
        self.address = self.stack_inputs[1]
        self.args_offset = self.stack_inputs[2]
        self.args_size = self.stack_inputs[3]
        self.ret_offset = self.stack_inputs[4]
        self.ret_size = self.stack_inputs[5]

        self.memory_input = event.mem_at(int(self.args_offset, 16), int(self.args_size, 16))


class CALLCODE(Instruction):
    opcode = 0xF2
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

        self.memory_input = event.mem_at(int(self.args_offset, 16), int(self.args_size, 16))


class STOP(Instruction):
    opcode = 0x0


class RETURN(Instruction):
    opcode = 0xF3
    stack_input_count = 2


class REVERT(Instruction):
    opcode = 0xFD
    stack_input_count = 2


class SELFDESTRUCT(Instruction):
    opcode = 0xFF
    stack_input_count = 1


class SLOAD(Instruction):
    opcode = 0x54
    stack_input_count = 1
    stack_output_count = 1

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.key = self.stack_inputs[0]
        self.result = self.stack_outputs[0]


class POP(Instruction):
    opcode = 0x50
    stack_input_count = 1


class JUMPDEST(Instruction):
    opcode = 0x5B


class PUSH0(Instruction):
    opcode = 0x5F
    stack_output_count = 1


def _make_log_n_instruction(op: int, topics: int):
    class LOG_N(Instruction):
        opcode = op
        stack_input_count = 2 + topics

        def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
            super().__init__(event, next_event, call_frame)
            self.offset = self.stack_inputs[0]
            self.size = self.stack_inputs[1]
            self.topics = [self.stack_inputs[2:]]

            if self.opcode == LOG3.opcode and self.program_counter == 10748:
                print('LOG3', event.memory, self)
            self.memory_input = event.mem_at(int(self.offset, 16), int(self.size, 16))

    return LOG_N


LOG0 = _make_log_n_instruction(0xA0, 0)
LOG1 = _make_log_n_instruction(0xA1, 1)
LOG2 = _make_log_n_instruction(0xA2, 2)
LOG3 = _make_log_n_instruction(0xA3, 3)
LOG4 = _make_log_n_instruction(0xA4, 4)

"""
class LOG1(Instruction):
    opcode = 0xA1
    stack_input_count = 3

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.offset = self.stack_inputs[0]
        self.size = self.stack_inputs[1]
        self.topics = [self.stack_inputs[2]]

        self.memory_input = event.mem_at(int(self.offset, 16), int(self.size, 16))
"""


DEFINED_INSTRUCTIONS = [
    STOP,
    SLOAD,
    CALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    CALLCODE,
    DELEGATECALL,
    POP,
    JUMPDEST,
    LOG0,
    LOG1,
    LOG2,
    LOG3,
    LOG4,
]
OPCODE_TO_INSTRUCTION_TYPE: dict[int, type[Instruction]] = dict((i.opcode, i) for i in DEFINED_INSTRUCTIONS)

# sanity check that we always specified the opcode
for opcode, instruction_type in OPCODE_TO_INSTRUCTION_TYPE.items():
    if opcode < 0:
        raise Exception(f"Please specify the opcode for {instruction_type} (found {opcode})")


def parse_instruction(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
    instruction_type = instruction_type_from_opcode(event.op)

    return instruction_type.from_events(event, next_event, call_frame)


def instruction_type_from_opcode(opcode: int) -> type[Instruction]:
    return OPCODE_TO_INSTRUCTION_TYPE.get(opcode, Unknown)
