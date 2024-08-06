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

from traces_analyzer.types.currency_change import CURRENCY_TYPE, CurrencyChange
from traces_analyzer.utils.events.event import CurrencyChangeEvent
from traces_analyzer.utils.events.events_decoder import EventsDecoder
from traces_analyzer.utils.events.tokens.erc_1155 import (
    ERC1155TransferBatchEvent,
    ERC1155TransferSingleEvent,
)
from traces_analyzer.utils.events.tokens.erc_20 import ERC20TransferEvent
from traces_analyzer.utils.events.tokens.erc_721 import ERC721TransferEvent
from traces_analyzer.utils.events.tokens.erc_777 import (
    ERC777BurnedEvent,
    ERC777MintedEvent,
    ERC777SentEvent,
)


class CurrencyChangesFeatureExtractor(SingleInstructionFeatureExtractor):
    """Track all currency changes"""

    def __init__(self) -> None:
        super().__init__()
        self.event_decoder = EventsDecoder(
            [
                ERC20TransferEvent,
                ERC721TransferEvent,
                ERC777MintedEvent,
                ERC777SentEvent,
                ERC777BurnedEvent,
                ERC1155TransferSingleEvent,
                ERC1155TransferBatchEvent,
            ]
        )
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
                        "type": CURRENCY_TYPE.ETHER,
                        "currency_identifier": "Wei",
                        "owner": sender.with_prefix(),
                        "change": -value,
                    },
                )
            )
            self.currency_changes.append(
                (
                    instruction,
                    {
                        "type": CURRENCY_TYPE.ETHER,
                        "currency_identifier": "Wei",
                        "owner": receiver.with_prefix(),
                        "change": value,
                    },
                )
            )

        if isinstance(instruction, (LOG0, LOG1, LOG2, LOG3, LOG4)):
            accesses = instruction.get_accesses()
            topics = [access.value.get_hexstring() for access in accesses.stack[2:]]
            data = accesses.memory[0].value.get_hexstring()
            if not topics:
                return

            event = self.event_decoder.decode_event(
                topics, data, instruction.call_context.storage_address
            )
            if event:
                assert isinstance(event, CurrencyChangeEvent), f"Invalid event: {event}"
                self.currency_changes.extend(
                    [(instruction, c) for c in event.get_currency_changes()]
                )
