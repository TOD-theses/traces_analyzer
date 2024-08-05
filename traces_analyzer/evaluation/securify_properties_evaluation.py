from typing import Mapping
from typing_extensions import override

from collections import Counter
from typing import Sequence, TypedDict
from traces_analyzer.features.extractors.instruction_location_grouper import (
    InstructionLocation,
)
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_parser.parser.instructions.instructions import CALL


class SecurifyProperties(TypedDict):
    # TODO: witness
    TOD_Transfer: bool
    TOD_Amount: bool
    TOD_Receiver: bool


CALLS_BY_LOC = Mapping[InstructionLocation, Sequence[CALL]]


class SecurifyPropertiesEvaluation(Evaluation):
    @property
    @override
    def _type_key(self):
        return "securify_properties"

    @property
    @override
    def _type_name(self):
        return "Securify properties"

    def __init__(
        self,
        calls_normal: CALLS_BY_LOC,
        calls_reverse: CALLS_BY_LOC,
    ):
        super().__init__()
        self._properties = check_securify_properties(calls_normal, calls_reverse)

    @override
    def _dict_report(self) -> dict:
        return dict(self._properties)

    @override
    def _cli_report(self) -> str:
        return f"""Seurify properties:
TOD Transfer: {self._properties['TOD_Transfer']}
TOD Amount: {self._properties['TOD_Amount']}
TOD Receiver: {self._properties['TOD_Receiver']}
"""


def check_securify_properties(
    calls_normal: CALLS_BY_LOC, calls_reverse: CALLS_BY_LOC
) -> SecurifyProperties:
    tod_transfer = check_tod_transfer(calls_normal, calls_reverse)
    return {
        "TOD_Transfer": tod_transfer,
        "TOD_Amount": not tod_transfer
        and check_tod_amount(calls_normal, calls_reverse),
        "TOD_Receiver": not tod_transfer
        and check_tod_receiver(calls_normal, calls_reverse),
    }


def check_tod_transfer(calls_normal: CALLS_BY_LOC, calls_reverse: CALLS_BY_LOC) -> bool:
    for loc in set(calls_normal) | set(calls_reverse):
        if loc not in calls_normal or loc not in calls_reverse:
            return True
        if len(calls_normal[loc]) != len(calls_reverse[loc]):
            return True
    return False


def check_tod_amount(calls_normal: CALLS_BY_LOC, calls_reverse: CALLS_BY_LOC) -> bool:
    for loc in set(calls_normal) | set(calls_reverse):
        # count the occurrences of each value
        amounts_normal = [c.child_value.get_hexstring() for c in calls_normal[loc]]
        amounts_reverse = [c.child_value.get_hexstring() for c in calls_reverse[loc]]

        if amounts_normal != amounts_reverse:
            return True
    return False


def check_tod_receiver(calls_normal: CALLS_BY_LOC, calls_reverse: CALLS_BY_LOC) -> bool:
    for loc in set(calls_normal) | set(calls_reverse):
        # count the occurrences of each recipient
        recipients_normal = Counter([c.child_code_address for c in calls_normal[loc]])
        recipients_reverse = Counter([c.child_code_address for c in calls_reverse[loc]])

        if recipients_normal != recipients_reverse:
            return True
    return False
