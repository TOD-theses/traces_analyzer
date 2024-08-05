from typing import TypedDict

from typing_extensions import override

from traces_analyzer.features.feature_extractor import SingleInstructionFeatureExtractor
from traces_parser.parser.instructions.instruction import Instruction
from traces_parser.parser.instructions.instructions import (
    CALL,
    CALLCODE,
    LOG0,
    LOG1,
    LOG2,
    LOG3,
    LOG4,
)


class CURRENCY:
    ETHER = "ETHER"


class CurrencyChange(TypedDict):
    type: str
    """Type of the currency, e.g. ETHER or ERC-20, ..."""
    token_address: str | None
    """ID for the currency. For Ether this is None, for tokens this is the storage address that emitted the LOG"""
    owner: str
    """Address for which a change occurred"""
    change: int
    """Positive or negative change"""


class CurrencyChangesFeatureExtractor(SingleInstructionFeatureExtractor):
    """Track all currency changes"""

    def __init__(self) -> None:
        super().__init__()
        self.currency_changes: list[tuple[Instruction, CurrencyChange]] = []

    @override
    def on_instruction(self, instruction: Instruction):
        if instruction.call_context.reverted:
            return

        if isinstance(instruction, (CALL, CALLCODE)):
            sender = instruction.child_caller
            receiver = instruction.child_code_address
            value = instruction.child_value.get_hexstring().as_int()
            self.currency_changes.append(
                (
                    instruction,
                    {
                        "type": CURRENCY.ETHER,
                        "token_address": None,
                        "owner": sender.with_prefix(),
                        "change": -value,
                    },
                )
            )
            self.currency_changes.append(
                (
                    instruction,
                    {
                        "type": CURRENCY.ETHER,
                        "token_address": None,
                        "owner": receiver.with_prefix(),
                        "change": value,
                    },
                )
            )

        if isinstance(instruction, (LOG0, LOG1, LOG2, LOG3, LOG4)):
            # TODO
            pass
