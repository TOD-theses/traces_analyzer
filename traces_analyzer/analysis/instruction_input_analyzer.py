import dataclasses
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable

from typing_extensions import override

from traces_analyzer.analysis.analyzer import DoubleInstructionAnalyzer
from traces_analyzer.parser.instruction import Instruction


@dataclass(frozen=True)
class InstructionKey:
    address: str
    program_counter: int
    opcode: int


@dataclass(frozen=True)
class InstructionKeyWithInputs(InstructionKey):
    stack_inputs: tuple[str, ...]
    memory_input: str | None

    def without_inputs(self) -> InstructionKey:
        return InstructionKey(
            address=self.address,
            program_counter=self.program_counter,
            opcode=self.opcode,
        )


@dataclass(frozen=True)
class StackInputChange:
    index: int
    first_value: str
    second_value: str


@dataclass(frozen=True)
class MemoryInputChange:
    first_value: str | None
    second_value: str | None


@dataclass(frozen=True)
class InstructionInputChange:
    """Same instruction with different inputs"""

    address: str
    program_counter: int
    opcode: int

    first_stack_input: tuple[str, ...]
    second_stack_input: tuple[str, ...]
    first_memory_input: str | None
    second_memory_input: str | None
    stack_input_changes: list[StackInputChange]
    memory_input_change: MemoryInputChange | None


@dataclass
class InstructionExecution:
    address: str
    program_counter: int
    opcode: int
    stack_inputs: tuple[str, ...]


def to_instruction_execution(key: InstructionKeyWithInputs):
    return InstructionExecution(
        address=key.address,
        program_counter=key.program_counter,
        opcode=key.opcode,
        stack_inputs=key.stack_inputs,
    )


class InstructionInputAnalyzer(DoubleInstructionAnalyzer):
    """Analyze how the instruction inputs of two traces differ"""

    def __init__(self) -> None:
        super().__init__()
        self._counter: Counter[InstructionKeyWithInputs] = Counter()

    @override
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        if first_instruction:
            key = to_key(first_instruction)
            self._counter.update([key])
            self._delete_if_zero(key)

        if second_instruction:
            key = to_key(second_instruction)
            self._counter.subtract([key])
            self._delete_if_zero(key)

    def _delete_if_zero(self, key: InstructionKeyWithInputs):
        if self._counter[key] == 0:
            self._counter.pop(key)

    def get_instructions_only_executed_by_one_trace(
        self,
    ) -> tuple[list[InstructionExecution], list[InstructionExecution]]:
        groups_first, groups_second = self._group_instructions_without_inputs()

        only_first = get_additional_keys_first_group(groups_first, groups_second)
        only_second = get_additional_keys_first_group(groups_second, groups_first)

        return only_first, only_second

    def get_instructions_with_different_inputs(self) -> list[InstructionInputChange]:
        return [create_input_change(a, b) for a, b in self._match_instructions_with_different_inputs()]

    def _match_instructions_with_different_inputs(
        self,
    ) -> Iterable[tuple[InstructionKeyWithInputs, InstructionKeyWithInputs]]:
        groups_first, groups_second = self._group_instructions_without_inputs()

        # match each key from the first trace to a key from the second
        # ignore the inputs for the matching
        for first_key_without_inputs, first_keys in groups_first.items():
            for first_key in first_keys:
                if groups_second.get(first_key_without_inputs):
                    # pop from the start, so we try to match them in the same order
                    second_key = groups_second[first_key_without_inputs].pop(0)

                    yield (first_key, second_key)

    def _group_instructions_without_inputs(
        self,
    ) -> tuple[
        dict[InstructionKey, list[InstructionKeyWithInputs]], dict[InstructionKey, list[InstructionKeyWithInputs]]
    ]:
        """Split the instructions by trace and group them by their keys without inputs"""
        keys_first = flatten(
            [clone_key_with_inputs_times(key, abs(count)) for (key, count) in self._counter.items() if count > 0]
        )
        keys_second = flatten(
            [clone_key_with_inputs_times(key, abs(count)) for (key, count) in self._counter.items() if count < 0]
        )

        groups_first = group_by_key_without_inputs(keys_first)
        groups_second = group_by_key_without_inputs(keys_second)

        return groups_first, groups_second


def flatten(matrix: list[list]) -> list:
    return [item for row in matrix for item in row]


def to_key(instruction: Instruction) -> InstructionKeyWithInputs:
    return InstructionKeyWithInputs(
        address=instruction.call_frame.code_address,
        program_counter=instruction.program_counter,
        opcode=instruction.opcode,
        stack_inputs=instruction.stack_inputs,
        memory_input=instruction.memory_input,
    )


def clone_key_with_inputs_times(key: InstructionKeyWithInputs, n: int) -> list[InstructionKeyWithInputs]:
    return [dataclasses.replace(key) for _ in range(n)]


def group_by_key_without_inputs(
    keys: list[InstructionKeyWithInputs],
) -> dict[InstructionKey, list[InstructionKeyWithInputs]]:
    groups: dict[InstructionKey, list[InstructionKeyWithInputs]] = defaultdict(list)

    for key in keys:
        groups[key.without_inputs()].append(key)

    return groups


def get_additional_keys_first_group(
    groups_first: dict[InstructionKey, list[InstructionKeyWithInputs]],
    groups_second: dict[InstructionKey, list[InstructionKeyWithInputs]],
):
    only_first: list[InstructionExecution] = []

    for first_key_without_inputs, first_keys in groups_first.items():
        second_keys = groups_second.get(first_key_without_inputs, [])
        if len(first_keys) > len(second_keys):
            additional_keys = first_keys[len(second_keys) :]
            only_first.extend(to_instruction_execution(k) for k in additional_keys)

    return only_first


def create_input_change(
    first_key: InstructionKeyWithInputs, second_key: InstructionKeyWithInputs
) -> InstructionInputChange:
    stack_input_changes: list[StackInputChange] = []
    memory_change: MemoryInputChange | None = None

    for i, (first_input, second_input) in enumerate(zip_longest(first_key.stack_inputs, second_key.stack_inputs)):
        if first_input != second_input:
            stack_input_changes.append(StackInputChange(index=i, first_value=first_input, second_value=second_input))

    if first_key.memory_input != second_key.memory_input:
        memory_change = MemoryInputChange(first_key.memory_input, second_key.memory_input)

    return InstructionInputChange(
        address=first_key.address,
        program_counter=first_key.program_counter,
        opcode=first_key.opcode,
        first_stack_input=first_key.stack_inputs,
        second_stack_input=second_key.stack_inputs,
        first_memory_input=first_key.memory_input,
        second_memory_input=second_key.memory_input,
        stack_input_changes=stack_input_changes,
        memory_input_change=memory_change,
    )
