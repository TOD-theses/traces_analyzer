from collections import defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from typing import Callable, Generic, Hashable, Mapping, Sequence, TypeVar

from typing_extensions import override

from traces_analyzer.features.feature_extractor import DoulbeInstructionFeatureExtractor
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.storage.storage_writes import StackAccess
from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True)
class StackInputChange:
    index: int
    first_value: HexString
    second_value: HexString


@dataclass(frozen=True)
class MemoryInputChange:
    first_value: HexString | None
    second_value: HexString | None


@dataclass(frozen=True)
class InstructionInputChange:
    """Same instruction with different inputs"""

    address: HexString
    program_counter: int
    opcode: int

    instruction_one: Instruction
    instruction_two: Instruction

    stack_input_changes: list[StackInputChange]
    memory_input_change: MemoryInputChange | None


class InstructionDifferencesFeatureExtractor(DoulbeInstructionFeatureExtractor):
    """Analyze how the instruction inputs of two traces differ"""

    def __init__(self) -> None:
        super().__init__()
        self._instructions_one: list[Instruction] = []
        self._instructions_two: list[Instruction] = []

    @override
    def on_instructions(
        self,
        first_instruction: Instruction | None,
        second_instruction: Instruction | None,
    ):
        if first_instruction:
            self._instructions_one.append(first_instruction)

        if second_instruction:
            self._instructions_two.append(second_instruction)

    def get_instructions_only_executed_by_one_trace(
        self,
    ) -> tuple[list[Instruction], list[Instruction]]:
        comparison = _compare_instructions(
            self._instructions_one,
            self._instructions_two,
            _get_location_opcode_key,
            _get_location_opcode_key,
        )
        only_first: list[Instruction] = []
        only_second: list[Instruction] = []
        for x in comparison:
            only_first.extend(x.only_first)
            only_second.extend(x.only_second)
        return (only_first, only_second)

    def get_instructions_with_different_inputs(self) -> list[InstructionInputChange]:
        # TODO: the order of the comparison is non-deterministc. Should we change it to be deterministic somehow?
        comparison = _compare_instructions(
            self._instructions_one,
            self._instructions_two,
            _get_location_opcode_key,
            _get_location_opcode_inputs_key,
        )
        changes = []
        for x in comparison:
            for change in x.changes:
                changes.append(_create_input_change(change[0], change[1]))
        return changes


def _create_input_change(
    instruction_one: Instruction, instruction_two: Instruction
) -> InstructionInputChange:
    stack_input_changes = _create_stack_input_changes(
        instruction_one.get_accesses().stack, instruction_two.get_accesses().stack
    )
    memory_change = _create_memory_input_change(
        _get_mem_accesses_hexstring(instruction_one),
        _get_mem_accesses_hexstring(instruction_two),
    )

    return InstructionInputChange(
        address=instruction_one.call_context.code_address,
        program_counter=instruction_one.program_counter,
        opcode=instruction_one.opcode,
        instruction_one=instruction_one,
        instruction_two=instruction_two,
        stack_input_changes=stack_input_changes,
        memory_input_change=memory_change,
    )


def _create_stack_input_changes(
    stack_one: Sequence[StackAccess], stack_two: Sequence[StackAccess]
) -> list[StackInputChange]:
    changes = []
    for i, (first_input, second_input) in enumerate(zip_longest(stack_one, stack_two)):
        if first_input != second_input:
            changes.append(
                StackInputChange(
                    index=i,
                    first_value=first_input.value.get_hexstring(),
                    second_value=second_input.value.get_hexstring(),
                )
            )

    return changes


def _create_memory_input_change(
    memory_one: HexString | None, memory_two: HexString | None
) -> MemoryInputChange | None:
    if memory_one == memory_two:
        return None
    return MemoryInputChange(memory_one, memory_two)


def _get_location_opcode_key(instruction: Instruction) -> tuple:
    return (
        instruction.call_context.code_address,
        instruction.program_counter,
        instruction.opcode,
    )


def _get_location_opcode_inputs_key(instruction: Instruction) -> tuple:
    stack_inputs_tuple = tuple(
        stack_access.value.get_hexstring()
        for stack_access in instruction.get_accesses().stack
    )
    return (
        *_get_location_opcode_key(instruction),
        stack_inputs_tuple,
        _get_mem_accesses_hexstring(instruction),
    )


def _get_mem_accesses_hexstring(instruction: Instruction) -> HexString | None:
    mem_accesses = instruction.get_accesses().memory
    assert len(mem_accesses) <= 1
    if mem_accesses:
        return mem_accesses[0].value.get_hexstring()
    return None


CommonKey = TypeVar("CommonKey", bound=Hashable)
ChangeKey = TypeVar("ChangeKey", bound=Hashable)


@dataclass(frozen=True)
class InstructionsComparison(Generic[CommonKey]):
    common_key: CommonKey
    only_first: list[Instruction]
    only_second: list[Instruction]
    changes: list[tuple[Instruction, Instruction]]


def _compare_instructions(
    instructions_one: Sequence[Instruction],
    instructions_two: Sequence[Instruction],
    get_common_key: Callable[[Instruction], CommonKey],
    get_change_key: Callable[[Instruction], ChangeKey],
) -> list[InstructionsComparison[CommonKey]]:
    grouped_one = _group_instructions_by_key(instructions_one, get_common_key)
    grouped_two = _group_instructions_by_key(instructions_two, get_common_key)

    return _compare_groups_by(grouped_one, grouped_two, get_change_key)


def _group_instructions_by_key(
    instructions: Sequence[Instruction], get_key: Callable[[Instruction], CommonKey]
) -> dict[CommonKey, list[Instruction]]:
    groups: dict[CommonKey, list[Instruction]] = defaultdict(list)

    for instr in instructions:
        groups[get_key(instr)].append(instr)

    return groups


def _compare_groups_by(
    groups_one: Mapping[CommonKey, Sequence[Instruction]],
    groups_two: Mapping[CommonKey, Sequence],
    get_key: Callable[[Instruction], ChangeKey],
) -> list[InstructionsComparison[CommonKey]]:
    all_keys = set(groups_one.keys()) | set(groups_two.keys())
    all_changes: list[InstructionsComparison] = []

    for key in all_keys:
        items_first = groups_one.get(key, [])
        items_second = groups_two.get(key, [])
        common_length = min(len(items_first), len(items_second))

        # TODO: use some kind of git-diff algorithm
        # currently, if one trace has an additional instruction at the start, everything would be marked as a change
        # but it's probably overkill. We're usually already comparing the same code location,
        # there won't be many differences
        changes: list[tuple[Instruction, Instruction]] = []

        for i in range(common_length):
            if (
                get_key(items_first[i]).__hash__()
                != get_key(items_second[i]).__hash__()
            ):
                changes.append((items_first[i], items_second[i]))
        if len(items_first) != len(items_second) or changes:
            all_changes.append(
                InstructionsComparison(
                    common_key=key,
                    only_first=list(items_first[common_length:]),
                    only_second=list(items_second[common_length:]),
                    changes=changes,
                )
            )

    return all_changes
