from copy import deepcopy
from typing_extensions import override

from collections import defaultdict
from typing import Sequence, TypedDict
from traces_analyzer.features.extractors.currency_changes import CurrencyChange
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_parser.parser.instructions.instructions import Instruction

CURRENCY_CHANGES_BY_ADDR = dict[str, dict[str, CurrencyChange]]


class GainsAndLosses(TypedDict):
    gains: CURRENCY_CHANGES_BY_ADDR
    losses: CURRENCY_CHANGES_BY_ADDR


class FinancialGainLossEvaluation(Evaluation):
    @property
    @override
    def _type_key(self):
        return "financial_gain_loss"

    @property
    @override
    def _type_name(self):
        return "Financial gains and losses"

    def __init__(
        self,
        currency_changes_normal: Sequence[tuple[Instruction, CurrencyChange]],
        currency_changes_reverse: Sequence[tuple[Instruction, CurrencyChange]],
    ):
        super().__init__()
        self._gains_and_losses = compute_gains_and_losses(
            currency_changes_normal, currency_changes_reverse
        )

    @override
    def _dict_report(self) -> dict:
        return dict(self._gains_and_losses)

    @override
    def _cli_report(self) -> str:
        # TODO
        s = "Gains in normal compared to reverse scenario:\n"
        for addr, gains in self._gains_and_losses["gains"].items():
            for change in gains.values():
                s += f'> {addr} gained {change["change"]} {change["type"]} {change["currency_identifier"]}\n'
        s = "Losses in normal compared to reverse scenario:\n"
        for addr, gains in self._gains_and_losses["gains"].items():
            for change in gains.values():
                s += f'> {addr} lost {change["change"]} {change["type"]} {change["currency_identifier"]}\n'

        return s

    def get_gains_and_losses(self) -> GainsAndLosses:
        return self._gains_and_losses


def compute_gains_and_losses(
    changes_normal: Sequence[tuple[Instruction, CurrencyChange]],
    changes_reverse: Sequence[tuple[Instruction, CurrencyChange]],
) -> GainsAndLosses:
    grouped_normal = group_by_address(changes_normal)
    grouped_reverse = group_by_address(changes_reverse)

    net_changes = add_changes(grouped_normal, negated_changes(grouped_reverse))
    return split_to_gains_and_losses(net_changes)


def group_by_address(
    changes: Sequence[tuple[Instruction, CurrencyChange]],
) -> CURRENCY_CHANGES_BY_ADDR:
    groups: CURRENCY_CHANGES_BY_ADDR = defaultdict(dict)

    for _, change in changes:
        addr = change["owner"]
        key = f'{change["type"]}-{change["currency_identifier"]}'
        if key not in groups[addr]:
            groups[addr][key] = deepcopy(change)
        else:
            groups[addr][key]["change"] += change["change"]

    return groups


def split_to_gains_and_losses(changes: CURRENCY_CHANGES_BY_ADDR) -> GainsAndLosses:
    gains: dict[str, dict[str, CurrencyChange]] = defaultdict(dict)
    losses: dict[str, dict[str, CurrencyChange]] = defaultdict(dict)
    for addr, c in changes.items():
        for key, change in c.items():
            if change["change"] > 0:
                gains[addr][key] = change
            if change["change"] < 0:
                losses[addr][key] = change

    return {
        "gains": gains,
        "losses": losses,
    }


def add_changes(base: CURRENCY_CHANGES_BY_ADDR, *operands: CURRENCY_CHANGES_BY_ADDR):
    result = deepcopy(base)

    for operand in operands:
        for addr, changes in operand.items():
            for key, change in changes.items():
                if key not in result[addr]:
                    result[addr][key] = deepcopy(change)
                else:
                    result[addr][key]["change"] += change["change"]

    return result


def negated_changes(changes: CURRENCY_CHANGES_BY_ADDR):
    result = deepcopy(changes)

    for addr, c in result.items():
        for key in c:
            result[addr][key]["change"] *= -1

    return result
