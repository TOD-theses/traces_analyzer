from traces_analyzer.parser.call_frame import CallFrame
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions import get_instruction_class
from traces_analyzer.utils.mnemonics import opcode_to_name


def parse_instruction(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame) -> Instruction:
    opcode = event.op
    name = opcode_to_name(opcode) or "UNKNOWN"
    program_counter = event.pc

    cls = get_instruction_class(opcode) or Instruction
    spec = cls.io_specification

    io = parse_instruction_io(
        spec,
        event.stack,
        event.memory,
        next_event.stack if next_event else [],
        next_event.memory if next_event else None,
    )
    return cls(
        opcode,
        name,
        program_counter,
        call_frame,
        io.inputs_stack,
        io.outputs_stack,
        io.input_memory,
        io.output_memory,
        {},
    )
