from abc import ABC
from typing import cast

from typing_extensions import Self, TypedDict

from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instruction_io import InstructionIOSpec, parse_instruction_io
from traces_analyzer.preprocessing.mnemonics import opcode_to_name

INSTRUCTION_UNKNOWN_NAME = "UNKNOWN"

EmptyDict = TypedDict("EmptyDict", {})


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
        self.data: EmptyDict = {}

        self._parse_inputs(event, next_event)

    def _parse_inputs(self, event: TraceEvent, next_event: TraceEvent):
        io = parse_instruction_io(
            InstructionIOSpec(self.stack_input_count, self.stack_output_count),
            event.stack,
            event.memory,
            next_event.stack if next_event else [],
            next_event.memory if next_event else None,
        )
        self.stack_inputs: tuple[str, ...] = io.inputs_stack
        self.stack_outputs: tuple[str, ...] = io.outputs_stack
        self.memory_input: str | None = None
        self.memory_output: str | None = None

    @classmethod
    def from_events(cls, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame) -> Self:
        return cls(event, next_event, call_frame)

    def __str__(self) -> str:
        return (
            "<Instruction"
            f" name={self.name}"
            f" op={hex(self.opcode)}"
            f" location={self.program_counter}@{self.call_frame.code_address}"
            f" data={self.data}"
            ">"
        )


class Unknown(Instruction):
    pass


CallWithValueData = TypedDict(
    "CallWithValueData",
    {
        "address": str,
        "value": int,
        "input": str,
    },
)
CallData = TypedDict(
    "CallData",
    {
        "address": str,
        "input": str,
    },
)


class CALL(Instruction):
    opcode = 0xF1
    stack_input_count = 7

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        io = parse_instruction_io(
            InstructionIOSpec(
                stack_input_count=self.stack_input_count,
                memory_input_offset_arg=3,
                memory_input_size_arg=4,
            ),
            event.stack,
            event.memory,
            next_event.stack if next_event else [],
            next_event.memory if next_event else None,
        )
        self.memory_input = cast(str, io.input_memory)
        self.data: CallWithValueData = {"address": self.stack_inputs[1], "value": int(self.stack_inputs[2], 16), "input": self.memory_input}


class STATICCALL(Instruction):
    opcode = 0xFA
    stack_input_count = 6

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        io = parse_instruction_io(
            InstructionIOSpec(
                stack_input_count=self.stack_input_count,
                memory_input_offset_arg=2,
                memory_input_size_arg=3,
            ),
            event.stack,
            event.memory,
            next_event.stack if next_event else [],
            next_event.memory if next_event else None,
        )
        self.memory_input = cast(str, io.input_memory)
        self.data: CallData = {"address": self.stack_inputs[1], "input": self.memory_input}


class DELEGATECALL(Instruction):
    opcode = 0xF4
    stack_input_count = 6

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        io = parse_instruction_io(
            InstructionIOSpec(
                stack_input_count=self.stack_input_count,
                memory_input_offset_arg=2,
                memory_input_size_arg=3,
            ),
            event.stack,
            event.memory,
            next_event.stack if next_event else [],
            next_event.memory if next_event else None,
        )
        self.memory_input = cast(str, io.input_memory)
        self.data: CallData = {"address": self.stack_inputs[1], "input": self.memory_input}


class CALLCODE(Instruction):
    opcode = 0xF2
    stack_input_count = 7

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        io = parse_instruction_io(
            InstructionIOSpec(
                stack_input_count=self.stack_input_count,
                memory_input_offset_arg=3,
                memory_input_size_arg=4,
            ),
            event.stack,
            event.memory,
            next_event.stack if next_event else [],
            next_event.memory if next_event else None,
        )
        self.memory_input = cast(str, io.input_memory)
        self.data: CallData = {"address": self.stack_inputs[1], "input": self.memory_input}


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

SLoadData = TypedDict('SLoadData', { 'key': str, 'result': str })

class SLOAD(Instruction):
    opcode = 0x54
    stack_input_count = 1
    stack_output_count = 1

    def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        super().__init__(event, next_event, call_frame)
        self.data: SLoadData = { 'key': self.stack_inputs[0], 'result': self.stack_outputs[0] }


class POP(Instruction):
    opcode = 0x50
    stack_input_count = 1


class JUMPDEST(Instruction):
    opcode = 0x5B


class PUSH0(Instruction):
    opcode = 0x5F
    stack_output_count = 1

LogData = TypedDict('LogData', { 'topics': tuple[str, ...], 'value': str })

def _make_log_n_instruction(op: int, topics: int):
    class LOG_N(Instruction):
        opcode = op
        stack_input_count = 2 + topics

        def __init__(self, event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
            super().__init__(event, next_event, call_frame)
            io = parse_instruction_io(
                InstructionIOSpec(
                    stack_input_count=self.stack_input_count,
                    memory_input_offset_arg=0,
                    memory_input_size_arg=1,
                ),
                event.stack,
                event.memory,
                next_event.stack if next_event else [],
                next_event.memory if next_event else None,
            )
            self.memory_input = cast(str, io.input_memory)
            self.data: LogData = { 'topics': tuple(self.stack_inputs[2:]), 'value': self.memory_input }


    return LOG_N


LOG0 = _make_log_n_instruction(0xA0, 0)
LOG1 = _make_log_n_instruction(0xA1, 1)
LOG2 = _make_log_n_instruction(0xA2, 2)
LOG3 = _make_log_n_instruction(0xA3, 3)
LOG4 = _make_log_n_instruction(0xA4, 4)


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
