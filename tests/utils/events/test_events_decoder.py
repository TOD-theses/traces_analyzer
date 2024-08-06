from traces_parser.datatypes.hexstring import HexString
from traces_analyzer.utils.events.events_decoder import EventsDecoder
from traces_analyzer.utils.events.tokens.erc_1155 import (
    ERC1155TransferBatchEvent,
    ERC1155TransferSingleEvent,
)
from traces_analyzer.utils.events.tokens.erc_20 import ERC20TransferEvent
from traces_analyzer.utils.events.tokens.erc_721 import ERC721TransferEvent

from tests.test_utils.test_utils import _test_addr

from snapshottest.pytest import PyTestSnapshotTest

from traces_analyzer.utils.events.tokens.erc_777 import (
    ERC777BurnedEvent,
    ERC777MintedEvent,
    ERC777SentEvent,
)
from eth_abi.abi import encode


def get_events_decoder():
    return EventsDecoder(
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


_token_address = _test_addr("0xabcd")


def test_events_decoder_erc20_transfer(snapshot: PyTestSnapshotTest):
    sender = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    to = HexString("000000000000000000000000d68060e9b273492d643a8eca70ad18c9ce2fb378")
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC20TransferEvent.signature(), sender, to]
    data = value

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC20TransferEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc721_transfer(snapshot: PyTestSnapshotTest):
    sender = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    to = HexString("000000000000000000000000d68060e9b273492d643a8eca70ad18c9ce2fb378")
    token_id = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC721TransferEvent.signature(), sender, to, token_id]
    data = HexString("")

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC721TransferEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc777_mint(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    to = HexString("000000000000000000000000d68060e9b273492d643a8eca70ad18c9ce2fb378")
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC777MintedEvent.signature(), operator, to]
    data = value + HexString.zeros(32 * 2)

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC777MintedEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc777_sent(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString(
        "000000000000000000000000ffffffffffffffffffffffffffffffffffffffff"
    )
    to = HexString("000000000000000000000000d68060e9b273492d643a8eca70ad18c9ce2fb378")
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC777SentEvent.signature(), operator, sender, to]
    data = value + HexString.zeros(32 * 2)

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC777SentEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc777_burned(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    holder = HexString(
        "000000000000000000000000d68060e9b273492d643a8eca70ad18c9ce2fb378"
    )
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC777BurnedEvent.signature(), operator, holder]
    data = value + HexString.zeros(32 * 2)

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC777BurnedEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_mint_single(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString.zeros(32)
    to = HexString("000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    token_id = HexString(
        "abababababababababababababababababababababababababababababababab"
    )
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC1155TransferSingleEvent.signature(), operator, sender, to]
    data = token_id + value

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferSingleEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_transfer_single(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString(
        "000000000000000000000000ffffffffffffffffffffffffffffffffffffffff"
    )
    to = HexString("000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    token_id = HexString(
        "abababababababababababababababababababababababababababababababab"
    )
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC1155TransferSingleEvent.signature(), operator, sender, to]
    data = token_id + value

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferSingleEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_burn_single(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString(
        "000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    )
    to = HexString.zeros(32)
    token_id = HexString(
        "abababababababababababababababababababababababababababababababab"
    )
    value = HexString(
        "0000000000000000000000000000000000000000000000000bde68a8201b8caf"
    )
    topics = [ERC1155TransferSingleEvent.signature(), operator, sender, to]
    data = token_id + value

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferSingleEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_mint_batch(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString.zeros(32)
    to = HexString("000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    token_ids = [
        HexString(
            "abababababababababababababababababababababababababababababababab"
        ).as_int(),
        HexString(
            "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd"
        ).as_int(),
    ]
    values = [
        HexString(
            "0000000000000000000000000000000000000000000000000000000000001111"
        ).as_int(),
        HexString(
            "0000000000000000000000000000000000000000000000000000000000002222"
        ).as_int(),
    ]
    topics = [ERC1155TransferBatchEvent.signature(), operator, sender, to]
    data = HexString(encode(["uint256[]", "uint256[]"], [token_ids, values]).hex())

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferBatchEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_transfer_batch(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString(
        "000000000000000000000000ffffffffffffffffffffffffffffffffffffffff"
    )
    to = HexString("000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    token_ids = [
        HexString(
            "abababababababababababababababababababababababababababababababab"
        ).as_int(),
        HexString(
            "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd"
        ).as_int(),
    ]
    values = [
        HexString(
            "0000000000000000000000000000000000000000000000000000000000001111"
        ).as_int(),
        HexString(
            "0000000000000000000000000000000000000000000000000000000000002222"
        ).as_int(),
    ]
    topics = [ERC1155TransferBatchEvent.signature(), operator, sender, to]
    data = HexString(encode(["uint256[]", "uint256[]"], [token_ids, values]).hex())

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferBatchEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")


def test_events_decoder_erc1155_burn_batch(snapshot: PyTestSnapshotTest):
    operator = HexString(
        "000000000000000000000000916b2aff900d06c526b4935f999462b65f1a24fe"
    )
    sender = HexString(
        "000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    )
    to = HexString.zeros(32)
    token_ids = [
        HexString(
            "abababababababababababababababababababababababababababababababab"
        ).as_int(),
        HexString(
            "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd"
        ).as_int(),
    ]
    values = [
        HexString(
            "0000000000000000000000000000000000000000000000000000000000001111"
        ).as_int(),
        HexString(
            "0000000000000000000000000000000000000000000000000000000000002222"
        ).as_int(),
    ]
    topics = [ERC1155TransferBatchEvent.signature(), operator, sender, to]
    data = HexString(encode(["uint256[]", "uint256[]"], [token_ids, values]).hex())

    decoder = get_events_decoder()
    event = decoder.decode_event(topics, data, _token_address)

    assert isinstance(event, ERC1155TransferBatchEvent)
    snapshot.assert_match(event.get_currency_changes(), "currency_changes")
