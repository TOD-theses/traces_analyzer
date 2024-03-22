from collections.abc import Iterable

from traces_analyzer.call_frame import CallFrame
from traces_analyzer.instructions import CALL, RETURN, SLOAD, STATICCALL, STOP, Instruction, Unknown
from traces_analyzer.trace_reader import TraceEvent


def parse_events(events: Iterable[TraceEvent]) -> Iterable[Instruction]:
    call_frame = CallFrame(
        parent=None,
        depth=1,
        msg_sender="0xTODO_msg_sender",
        address="0xTODO_address",
    )

    events_iterator = events.__iter__()
    current_event = next(events_iterator)

    for next_event in events_iterator:
        instruction = parse_instruction(current_event, next_event, call_frame)
        yield instruction

        call_frame = update_call_frame(call_frame, instruction, next_event.depth)
        current_event = next_event

    # NOTE: for the last event, we pass None instead of next_event
    # if this breaks something in the future (eg if the last TraceEvent is a SLOAD
    # that tries to read the stack for the result), I'll need to change this
    yield parse_instruction(current_event, None, call_frame)  # type: ignore


INSTRUCTIONS = [CALL, STATICCALL, STOP, RETURN, SLOAD]
OPCODE_TO_INSTRUCTION = dict((i.op, i) for i in INSTRUCTIONS)  # type: ignore


def parse_instruction(event: TraceEvent, next_event: TraceEvent | None, call_frame: CallFrame):
    if event.op in OPCODE_TO_INSTRUCTION:
        instruction_type = OPCODE_TO_INSTRUCTION[event.op]
    else:
        instruction_type = Unknown

    return instruction_type.from_event(event, next_event, call_frame)  # type: ignore


def update_call_frame(
    current_call_frame: CallFrame,
    instruction: Instruction,
    expected_depth: int,
):
    # TODO: CALLCODE, DELEGATECALL
    if isinstance(instruction, (CALL, STATICCALL)):
        current_call_frame = CallFrame(
            parent=current_call_frame,
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.address,
            address=instruction.address,
        )
    # TODO: REVERT, SELFDESTRUCT
    elif isinstance(instruction, (STOP, RETURN)):
        if not current_call_frame.parent:
            raise Exception(
                "Tried to return to parent call frame, while already being at the root."
                f"{current_call_frame}. {instruction}"
            )
        current_call_frame = current_call_frame.parent

    if current_call_frame.depth != expected_depth:
        raise Exception(
            f"Unexpected call depth: CallFrame has {current_call_frame.depth},"
            f" expected {expected_depth}. {instruction}. {current_call_frame}"
        )

    return current_call_frame
