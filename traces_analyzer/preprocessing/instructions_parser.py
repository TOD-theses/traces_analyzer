from collections.abc import Iterable

from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import (
    CALL,
    CALLCODE,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
    Instruction,
    parse_instruction,
)
from traces_analyzer.preprocessing.precompiled_contracts import is_precompiled_contract


def parse_instructions(events: Iterable[TraceEvent]) -> Iterable[Instruction]:
    call_frame = CallFrame(
        parent=None,
        depth=1,
        msg_sender="0x1111111111111111111111111111111111111111",
        code_address="0x1234123412341234123412341234123412341234",
        storage_address="0x1234123412341234123412341234123412341234",
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
    yield parse_instruction(current_event, None, call_frame)  # type: ignore[arg-type]


def update_call_frame(
    current_call_frame: CallFrame,
    instruction: Instruction,
    expected_depth: int,
):
    next_call_frame = current_call_frame

    if isinstance(instruction, (CALL, STATICCALL)):
        next_call_frame = CallFrame(
            parent=current_call_frame,
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.address,
            storage_address=instruction.address,
        )
    elif isinstance(instruction, (CALLCODE, DELEGATECALL)):
        next_call_frame = CallFrame(
            parent=current_call_frame,
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.address,
            storage_address=current_call_frame.storage_address,
        )
    elif isinstance(instruction, (STOP, RETURN, REVERT, SELFDESTRUCT)):
        if not current_call_frame.parent:
            raise Exception(
                "Tried to return to parent call frame, while already being at the root."
                f"{current_call_frame}. {instruction}"
            )
        next_call_frame = current_call_frame.parent

    # precompiled contracts don't produce any trace events, so we automatically change the frame back to the current one
    if is_precompiled_contract(next_call_frame.code_address):
        next_call_frame = current_call_frame

    if next_call_frame.depth != expected_depth:
        raise Exception(
            f"Unexpected call depth: CallFrame has {next_call_frame.depth},"
            f" expected {expected_depth}. {instruction}. {next_call_frame}"
        )

    return next_call_frame
