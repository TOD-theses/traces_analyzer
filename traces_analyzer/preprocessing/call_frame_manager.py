from typing import Any, Callable, TypeGuard

from traces_analyzer.preprocessing.call_frame import CallFrame, HaltType
from traces_analyzer.preprocessing.instruction import Instruction
from traces_analyzer.preprocessing.instructions import (
    CALL,
    CALLCODE,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
)

CallTree = tuple[CallFrame, list["CallTree"]]


class CallFrameManager:
    def __init__(self, root_call_frame: CallFrame) -> None:
        self._call_tree: CallTree = (root_call_frame, [])
        self._current_call_frame = root_call_frame

    def get_current_call_frame(self) -> CallFrame:
        return self._current_call_frame

    # TODO: test and use this method
    # def get_call_tree(self) -> CallTree:
    # return self._call_tree

    def on_step(self, instruction: Instruction, next_depth: int):
        new_call_frame = update_call_frame(self._current_call_frame, instruction, next_depth)
        if new_call_frame is not self._current_call_frame:
            self._update_call_frame(new_call_frame)

    def _update_call_frame(self, new_call_frame: CallFrame):
        if new_call_frame is not self._current_call_frame.parent:
            self._insert_call_frame(new_call_frame)
        self._current_call_frame = new_call_frame

    def _insert_call_frame(self, new_call_frame: CallFrame):
        def insert_if_parent(tree: CallTree):
            call_frame, children = tree
            if call_frame is new_call_frame.parent:
                children.append((new_call_frame, []))

        _recurse_tree(self._call_tree, insert_if_parent)


def _recurse_tree(tree: CallTree, callback: Callable[[CallTree], Any]):
    callback(tree)

    _, children = tree
    for child in children:
        _recurse_tree(child, callback)


class ExpectedDepthChange(Exception):
    pass


class UnexpectedDepthChange(Exception):
    pass


def update_call_frame(
    current_call_frame: CallFrame,
    instruction: Instruction,
    next_depth: int,
):
    next_call_frame = current_call_frame

    # TODO: refactor this method
    if enters_call_frame_normal(instruction, current_call_frame.depth, next_depth):
        next_call_frame = CallFrame(
            parent=current_call_frame,
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.data["address"],
            storage_address=instruction.data["address"],
            reverted=False,
            halt_type=None,
        )
    elif enters_call_frame_without_storage(instruction, current_call_frame.depth, next_depth):
        next_call_frame = CallFrame(
            parent=current_call_frame,
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.data["address"],
            storage_address=current_call_frame.storage_address,
            reverted=False,
            halt_type=None,
        )
    elif makes_normal_halt(instruction, current_call_frame.depth, next_depth) or makes_exceptional_halt(
        current_call_frame.depth, next_depth
    ):
        if not current_call_frame.parent:
            raise UnexpectedDepthChange(
                "Tried to return to parent call frame, while already being at the root."
                f" {current_call_frame}. {instruction}"
            )
        current_call_frame.reverted = True
        current_call_frame.halt_type = (
            HaltType.NORMAL
            if makes_normal_halt(instruction, current_call_frame.depth, next_depth)
            else HaltType.EXCEPTIONAL
        )
        next_call_frame = current_call_frame.parent
    elif makes_normal_halt(instruction, 1, 0):
        # if we get here, this means that we have a STOP/... without a proper depth change
        msg = (
            "Encountered a halt without observing a correct depth change in the trace event."
            f" Found {instruction} with next depth {next_depth} and current call frame {current_call_frame}"
        )
        if current_call_frame.depth == next_depth:
            raise ExpectedDepthChange(msg)
        else:
            raise UnexpectedDepthChange(msg)
    elif current_call_frame.depth != next_depth:
        raise UnexpectedDepthChange(
            "Could not change call frame: the trace showed a change in the call depth,"
            " however the instruction should not change the depth."
            f" Expected depth change from {current_call_frame.depth} to {next_depth}. Instruction: {instruction}."
        )

    if next_call_frame.depth != next_depth:
        raise Exception(
            f"Unexpected call depth: CallFrame has {next_call_frame.depth},"
            f" expected {next_depth}. {instruction}. {next_call_frame}"
        )

    return next_call_frame


def enters_call_frame_normal(
    instruction: Instruction, current_depth: int, next_depth: int
) -> TypeGuard[CALL | STATICCALL]:
    return current_depth + 1 == next_depth and isinstance(instruction, (CALL, STATICCALL))


def enters_call_frame_without_storage(
    instruction: Instruction, current_depth: int, next_depth: int
) -> TypeGuard[DELEGATECALL | CALLCODE]:
    return current_depth + 1 == next_depth and isinstance(instruction, (DELEGATECALL, CALLCODE))


def makes_normal_halt(instruction: Instruction, current_depth: int, next_depth: int):
    return current_depth - 1 == next_depth and isinstance(instruction, (STOP, REVERT, RETURN, SELFDESTRUCT))


def makes_exceptional_halt(current_depth: int, next_depth: int):
    return current_depth - 1 == next_depth
