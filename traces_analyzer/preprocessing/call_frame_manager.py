from dataclasses import dataclass, field
from hashlib import sha256
from typing import Iterable, TypeGuard

from traces_analyzer.preprocessing.call_frame import CallFrame, HaltType
from traces_analyzer.preprocessing.instruction import Instruction
from traces_analyzer.preprocessing.instructions import (
    CALL,
    CALLCODE,
    CREATE,
    CREATE2,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
)


@dataclass
class CallTree:
    """A call tree, representing the current call frame and all child call frames"""

    call_frame: CallFrame
    children: list["CallTree"] = field(default_factory=list)

    def recurse(self) -> Iterable["CallTree"]:
        """Returns the tree nodes in a depth first order"""
        yield self

        for child in self.children:
            yield from child.recurse()

    def add(self, call_frame: CallFrame):
        """Add the call_frame based on its parent"""
        parent_node: CallTree | None = None

        for tree in self.recurse():
            if tree.call_frame == call_frame.parent:
                parent_node = tree

        if not parent_node:
            raise Exception(f"Could not find parent tree node to add callframe. {self} - {call_frame}")
        parent_node.children.append(CallTree(call_frame))

    def __str__(self) -> str:
        s = f"> {self.call_frame.code_address}.{self.call_frame.calldata[:8]}({self.call_frame.calldata[8:]})\n"
        for child in self.children:
            s += "  " + str(child)
        return s


class CallFrameManager:
    def __init__(self, root_call_frame: CallFrame) -> None:
        self._call_tree = CallTree(root_call_frame)
        self._current_call_frame = root_call_frame

    def get_current_call_frame(self) -> CallFrame:
        return self._current_call_frame

    def get_call_tree(self) -> CallTree:
        return self._call_tree

    def on_step(self, instruction: Instruction, next_depth: int):
        new_call_frame = update_call_frame(self._current_call_frame, instruction, next_depth)
        if new_call_frame != self._current_call_frame:
            self._update_call_frame(new_call_frame)

    def _update_call_frame(self, new_call_frame: CallFrame):
        if new_call_frame is not self._current_call_frame.parent:
            self._call_tree.add(new_call_frame)
        self._current_call_frame = new_call_frame


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
            calldata=instruction.memory_input or "",  # TODO: use appropriate method instead
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.data["address"],
            storage_address=instruction.data["address"],
        )
    elif enters_call_frame_without_storage(instruction, current_call_frame.depth, next_depth):
        next_call_frame = CallFrame(
            parent=current_call_frame,
            calldata=instruction.memory_input or "",  # TODO: use appropriate method instead
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=instruction.data["address"],
            storage_address=current_call_frame.storage_address,
        )
    elif creates_contract(instruction, current_call_frame.depth, next_depth):
        # NOTE: we currently do not compute the correct addresses
        created_contract_addr = "0x" + sha256(current_call_frame.code_address.encode()).hexdigest()[12:]
        next_call_frame = CallFrame(
            parent=current_call_frame,
            calldata=instruction.memory_input or "",
            depth=current_call_frame.depth + 1,
            msg_sender=current_call_frame.code_address,
            code_address=created_contract_addr,
            storage_address=created_contract_addr,
            is_contract_initialization=True,
        )
    elif makes_normal_halt(instruction, current_call_frame.depth, next_depth) or makes_exceptional_halt(
        current_call_frame.depth, next_depth
    ):
        if not current_call_frame.parent:
            raise UnexpectedDepthChange(
                "Tried to return to parent call frame, while already being at the root."
                f" {current_call_frame}. {instruction}"
            )
        next_call_frame = current_call_frame.parent

        if isinstance(instruction, REVERT):
            current_call_frame.reverted = True
            current_call_frame.halt_type = HaltType.NORMAL
        elif not makes_normal_halt(instruction, current_call_frame.depth, next_depth):
            current_call_frame.reverted = True
            current_call_frame.halt_type = HaltType.EXCEPTIONAL
        else:
            current_call_frame.halt_type = HaltType.NORMAL

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


def creates_contract(instruction: Instruction, current_depth: int, next_depth: int):
    return current_depth + 1 == next_depth and isinstance(instruction, (CREATE, CREATE2))


def makes_normal_halt(instruction: Instruction, current_depth: int, next_depth: int):
    return current_depth - 1 == next_depth and isinstance(instruction, (STOP, REVERT, RETURN, SELFDESTRUCT))


def makes_exceptional_halt(current_depth: int, next_depth: int):
    return current_depth - 1 == next_depth
