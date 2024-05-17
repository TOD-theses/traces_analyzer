from dataclasses import dataclass, field
from hashlib import sha256
from typing import Sequence

from typing_extensions import Iterable, Self, TypeGuard

from traces_analyzer.parser.environment.call_context import CallContext, HaltType
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import (
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
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString
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
        hex_signature = self.call_context.calldata[:8]
        signature = (
            signature_lookup.lookup_by_hex(hex_signature.get_hexstring())
            or hex_signature
        )
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
    next_call_context = current_call_context

    # TODO: refactor this method
    if next_depth is None:
        # do not enter/return a callframe at the end of the trace
        return next_call_context

    if enters_call_context(instruction, current_call_context.depth, next_depth):
        call_config = instruction.get_data()
        code_address = call_config["address"]
        storage_address = (
            call_config["address"]
            if call_config["updates_storage_address"]
            else current_call_context.storage_address
        )
        caller = current_call_context.storage_address
        if isinstance(instruction, DELEGATECALL):
            caller = current_call_context.msg_sender

        next_call_context = CallContext(
            parent=current_call_context,
            initiating_instruction=instruction,
            calldata=call_config["input"],
            value=call_config["value"],
            depth=current_call_context.depth + 1,
            msg_sender=caller,
            code_address=code_address,
            storage_address=storage_address,
        )
    elif creates_contract(instruction, current_call_context.depth, next_depth):
        # NOTE: we currently do not compute the correct addresses
        created_contract_addr = (
            "0x"
            + sha256(
                current_call_context.code_address.with_prefix().encode()
            ).hexdigest()[12:]
        )
        next_call_context = CallContext(
            parent=current_call_context,
            initiating_instruction=instruction,
            calldata=StorageByteGroup(),
            # TODO: correct value
            value=StorageByteGroup.deprecated_from_hexstring(HexString.from_int(0)),
            depth=current_call_context.depth + 1,
            msg_sender=current_call_context.code_address,
            code_address=HexString(created_contract_addr),
            storage_address=HexString(created_contract_addr),
            is_contract_initialization=True,
        )
    elif makes_halt(current_call_context.depth, next_depth):
        next_call_context = exit_call_context(
            current_call_context, instruction.opcode, next_depth
        )
    elif is_normal_halt_opcode(instruction.opcode):
        msg = (
            "Encountered a halt without observing a correct depth change in the trace event."
            f" Found {instruction} with next depth {next_depth} and current call context {current_call_context}"
        )
        if current_call_context.depth == next_depth:
            raise ExpectedDepthChange(msg)
        else:
            raise UnexpectedDepthChange(msg)
    elif current_call_context.depth != next_depth:
        raise UnexpectedDepthChange(
            "Could not change call context: the trace showed a change in the call depth,"
            " however the instruction should not change the depth."
            f" Expected depth change from {current_call_context.depth} to {next_depth}. Instruction: {instruction}."
        )

    if next_call_context.depth != next_depth:
        raise Exception(
            f"Unexpected call depth: CallContext has {next_call_context.depth},"
            f" expected {next_depth}. {instruction}. {next_call_context}"
        )

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


def enters_call_context(
    instruction: Instruction, current_depth: int, next_depth: int
) -> TypeGuard[CALL | STATICCALL | DELEGATECALL | CALLCODE]:
    return current_depth + 1 == next_depth and isinstance(
        instruction, (CALL, STATICCALL, DELEGATECALL, CALLCODE)
    )


def creates_contract(
    instruction: Instruction, current_depth: int, next_depth: int
) -> TypeGuard[CREATE | CREATE2]:
    return current_depth + 1 == next_depth and isinstance(
        instruction, (CREATE, CREATE2)
    )


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
