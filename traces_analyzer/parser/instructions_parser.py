from collections.abc import Iterable
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.call_frame import CallFrame
from traces_analyzer.parser.call_frame_manager import CallFrameManager, CallTree
from traces_analyzer.parser.events_parser import TraceEvent, parse_events
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions import get_instruction_class
from traces_analyzer.utils.mnemonics import opcode_to_name


@dataclass
class TransactionParsingInfo:
    trace_events_json: Iterable[str]
    sender: str
    to: str
    calldata: str


@dataclass
class ParsedTransaction:
    instructions: Sequence[Instruction]
    call_tree: CallTree


def parse_instructions(parsing_info: TransactionParsingInfo) -> ParsedTransaction:
    call_frame_manager = _setup_call_frame_manager(parsing_info.sender, parsing_info.to, parsing_info.calldata)

    events = parse_events(parsing_info.trace_events_json)
    instructions = list(_parse_instructions(events, call_frame_manager))

    return ParsedTransaction(instructions, call_frame_manager.get_call_tree())


def _setup_call_frame_manager(sender: str, to: str, calldata: str) -> CallFrameManager:
    return CallFrameManager(
        CallFrame(
            parent=None,
            calldata=calldata,
            depth=1,
            msg_sender=sender,
            code_address=to,
            storage_address=to,
        )
    )


def _parse_instructions(events: Iterable[TraceEvent], call_frame_manager: CallFrameManager) -> Iterable[Instruction]:
    events_iterator = events.__iter__()
    try:
        current_event = next(events_iterator)
    except StopIteration:
        # no events to parse
        return []

    for next_event in events_iterator:
        instruction = parse_instruction(current_event, next_event, call_frame_manager.get_current_call_frame())
        call_frame_manager.on_step(instruction, next_event.depth)
        current_event = next_event

        yield instruction

    # NOTE: for the last event, we pass None instead of next_event
    # if this breaks something in the future (eg if the last TraceEvent is a SLOAD
    # that tries to read the stack for the result), I'll need to change this
    yield parse_instruction(current_event, None, call_frame_manager.get_current_call_frame())  # type: ignore[arg-type]


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
