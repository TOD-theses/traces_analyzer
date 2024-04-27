from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.storage.storage import MemoryStorage
from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True)
class InstructionIO:
    inputs_stack: tuple[HexString, ...] = ()
    outputs_stack: tuple[HexString, ...] = ()
    input_memory: HexString | None = None
    output_memory: HexString | None = None


@dataclass(frozen=True)
class InstructionIOSpec:
    stack_input_count: int = 0
    stack_output_count: int = 0
    # all memory args are indexes for the stack_input
    # eg offset_arg 0 and size_arg 1 will use the first two stack inputs to get the memory range
    memory_input_offset_arg: int | None = None
    memory_input_size_arg: int | None = None
    memory_output_offset_arg: int | None = None
    memory_output_size_arg: int | None = None


def parse_instruction_io(
    spec: InstructionIOSpec,
    stack: Sequence[HexString],
    memory: MemoryStorage,
    next_stack: Sequence[HexString],
    next_mem: HexString | None,
) -> InstructionIO:
    inputs_stack = parse_stack_arg(stack, last_n_args=spec.stack_input_count)
    outputs_stack = parse_stack_arg(next_stack, last_n_args=spec.stack_output_count)
    input_memory = parse_memory_via_stack_args(
        memory.get_all().get_hexstring(), inputs_stack, spec.memory_input_offset_arg, spec.memory_input_size_arg
    )
    output_memory = parse_memory_via_stack_args(
        next_mem, inputs_stack, spec.memory_output_offset_arg, spec.memory_output_size_arg
    )

    return InstructionIO(
        inputs_stack=inputs_stack,
        outputs_stack=outputs_stack,
        input_memory=input_memory,
        output_memory=output_memory,
    )


def parse_stack_arg(stack: Sequence[HexString], last_n_args: int) -> tuple[HexString, ...]:
    if last_n_args == 0:
        return tuple()

    return tuple(reversed(stack[-last_n_args:]))


def parse_memory_via_stack_args(
    memory: HexString | None,
    stack_args: tuple[HexString, ...],
    offset_arg_index: int | None,
    offset_size_index: int | None,
) -> HexString | None:
    if offset_arg_index is None or offset_size_index is None:
        return None

    offset = stack_args[offset_arg_index].as_int()
    size = stack_args[offset_size_index].as_int()

    return parse_memory_arg(memory, offset, size)


def parse_memory_arg(memory: HexString | None, mem_offset: int, mem_size: int) -> HexString | None:
    # TODO: use EventMemory class instead of passing str|None
    if memory is None:
        return None
    return memory[2 * mem_offset : 2 * (mem_offset + mem_size)]
