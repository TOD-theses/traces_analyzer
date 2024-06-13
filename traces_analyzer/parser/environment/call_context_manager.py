from dataclasses import dataclass, field
from typing import Sequence

from typing_extensions import Iterable, Self, TypeGuard

from traces_analyzer.parser.environment.call_context import CallContext, HaltType
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import (
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STOP,
    CallContextEnteringInstruction,
)
from traces_analyzer.utils.mnemonics import opcode_to_name
from traces_analyzer.utils.signatures.signature_registry import SignatureRegistry

# TODO: rename and/or split this file

# TODO: do not use a global signature registry
signature_lookup = SignatureRegistry("http://localhost:8000")


@dataclass
class CallTree:
    """A call tree, representing the current call context and all child call contexts"""

    call_context: CallContext
    parent: Self | None = None
    children: list[Self] = field(default_factory=list)

    def recurse(self) -> Iterable["CallTree"]:
        """Returns the tree nodes in a depth first order"""
        yield self

        for child in self.children:
            yield from child.recurse()

    def add(self, call_context: CallContext):
        """Add the call_context based on its parent"""
        parent_node: CallTree | None = None

        for tree in self.recurse():
            if tree.call_context == call_context.parent:
                parent_node = tree

        if not parent_node:
            raise Exception(
                f"Could not find parent tree node to add callcontext. {self} - {call_context}"
            )
        new_node = CallTree(call_context)
        parent_node.children.append(new_node)
        new_node.parent = parent_node  # type: ignore

    def __str__(self) -> str:
        hex_signature = self.call_context.calldata[:4].get_hexstring()
        signature = signature_lookup.lookup_by_hex(hex_signature) or hex_signature
        s = f"> {self.call_context.code_address}.{signature}(...)\n"
        for child in self.children:
            s += "  " + "  ".join(str(child).splitlines(True))
        return s


def build_call_tree(
    root_call_context: CallContext, instructions: Sequence[Instruction]
) -> CallTree:
    current_call_context = root_call_context
    call_tree = CallTree(current_call_context)

    for instruction in instructions:
        if instruction.call_context is not current_call_context:
            # add context if we enter (ie we don't go up)
            if instruction.call_context is not current_call_context.parent:
                call_tree.add(instruction.call_context)
            current_call_context = instruction.call_context

    return call_tree


class ExpectedDepthChange(Exception):
    pass


class UnexpectedDepthChange(Exception):
    pass


def update_call_context(
    current_call_context: CallContext,
    instruction: Instruction,
    next_depth: int | None,
):
    if next_depth is None:
        # do not enter/return a callframe at the end of the trace
        return current_call_context

    if instruction_creates_call_context(instruction):
        next_call_context = instruction.create_call_context()
    elif makes_halt(current_call_context.depth, next_depth):
        next_call_context = exit_call_context(
            current_call_context, instruction.opcode, next_depth
        )
    # sanity check
    elif is_normal_halt_opcode(instruction.opcode):
        msg = (
            "Encountered a halt without observing a correct depth change in the trace event."
            f" Found {instruction} with next depth {next_depth} and current call context {current_call_context}"
        )
        if current_call_context.depth == next_depth:
            raise ExpectedDepthChange(msg)
        else:
            raise UnexpectedDepthChange(msg)
    # sanity check
    elif current_call_context.depth != next_depth:
        raise UnexpectedDepthChange(
            "Could not change call context: the trace showed a change in the call depth,"
            " however the instruction should not change the depth."
            f" Expected depth change from {current_call_context.depth} to {next_depth}. Instruction: {instruction}."
        )
    else:
        next_call_context = current_call_context

    return next_call_context


def exit_call_context(
    current_call_context: CallContext, instruction_opcode: int, next_depth: int
) -> CallContext:
    if not current_call_context.parent:
        raise UnexpectedDepthChange(
            "Tried to return to parent call context, while already being at the root."
            f" {current_call_context}. {opcode_to_name(instruction_opcode)}"
        )

    if instruction_opcode == REVERT.opcode:
        current_call_context.reverted = True
        current_call_context.halt_type = HaltType.NORMAL
    elif makes_exceptional_halt(
        instruction_opcode, current_call_context.depth, next_depth
    ):
        current_call_context.reverted = True
        current_call_context.halt_type = HaltType.EXCEPTIONAL
    else:
        current_call_context.halt_type = HaltType.NORMAL

    return current_call_context.parent


def instruction_creates_call_context(
    instruction: Instruction,
) -> TypeGuard[CallContextEnteringInstruction]:
    return isinstance(instruction, CallContextEnteringInstruction)


_NORMAL_HALT_OPCODES = {RETURN.opcode, STOP.opcode, REVERT.opcode, SELFDESTRUCT.opcode}


def makes_halt(current_depth: int, next_depth: int):
    return current_depth - 1 == next_depth


def makes_normal_halt(opcode: int, current_depth: int, next_depth: int):
    return makes_halt(current_depth, next_depth) and is_normal_halt_opcode(opcode)


def makes_exceptional_halt(opcode: int, current_depth: int, next_depth: int):
    return makes_halt(
        current_depth, next_depth
    ) == next_depth and not is_normal_halt_opcode(opcode)


def is_normal_halt_opcode(opcode: int) -> bool:
    return opcode in _NORMAL_HALT_OPCODES
