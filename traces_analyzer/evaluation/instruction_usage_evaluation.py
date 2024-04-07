from typing import Iterable, Mapping

from typing_extensions import override

from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.utils.mnemonics import opcode_to_name


class InstructionUsageEvaluation(Evaluation):
    _type_key = "instruction_usage"
    _type_name = "Instruction usage"

    def __init__(
        self,
        opcodes_per_contract_one: Mapping[str, set[int]],
        opcodes_per_contract_two: Mapping[str, set[int]],
        filter_opcodes: Iterable[int] | None = None,
    ):
        super().__init__()
        self._opcodes_one = opcodes_per_contract_one
        self._opcodes_two = opcodes_per_contract_two
        self._RELEVANT_OPCODES = filter_opcodes

    @override
    def _dict_report(self) -> dict:
        return {
            "opcodes_first": self._sorted_opcodes(self._opcodes_one),
            "opcodes_second": self._sorted_opcodes(self._opcodes_two),
            "opcodes_relevant_merged": self._relevant_opcodes(self._merged_opcodes()),
        }

    @override
    def _cli_report(self) -> str:
        opcodes = self._relevant_opcodes(self._merged_opcodes())

        result = "Relevant instructions by code address:\n"
        for addr, ops in opcodes.items():
            result += f"{addr}: {[opcode_to_name(int(op, 16)) for op in ops]}\n"

        return result

    def _sorted_opcodes(self, opcodes: Mapping[str, Iterable[int]]) -> Mapping[str, list[str]]:
        return dict((addr, [hex(op).upper().replace("X", "x") for op in sorted(ops)]) for addr, ops in opcodes.items())

    def _relevant_opcodes(self, opcodes: Mapping[str, Iterable[int]]) -> Mapping[str, list[str]]:
        relevant_opcodes: dict[str, Iterable[int]] = dict(
            (addr, self._filter_relevant_opcodes(ops)) for addr, ops in opcodes.items()
        )
        return self._sorted_opcodes(relevant_opcodes)

    def _filter_relevant_opcodes(self, opcodes: Iterable[int]) -> Iterable[int]:
        if not self._RELEVANT_OPCODES:
            return opcodes
        return [op for op in opcodes if op in self._RELEVANT_OPCODES]

    def _merged_opcodes(self) -> dict[str, Iterable[int]]:
        merged: dict[str, Iterable[int]] = {}

        for addr in list(self._opcodes_one.keys()) + list(self._opcodes_two.keys()):
            merged[addr] = set(list(self._opcodes_one.get(addr, set())) + list(self._opcodes_two.get(addr, set())))

        return merged
