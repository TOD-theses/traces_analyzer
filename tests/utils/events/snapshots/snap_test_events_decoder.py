# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_events_decoder_erc1155_burn_batch currency_changes"] = [
    {
        "change": -4369,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
    {
        "change": -8738,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
]

snapshots["test_events_decoder_erc1155_burn_single currency_changes"] = [
    {
        "change": -855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    }
]

snapshots["test_events_decoder_erc1155_mint_batch currency_changes"] = [
    {
        "change": 4369,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
    {
        "change": 8738,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
]

snapshots["test_events_decoder_erc1155_mint_single currency_changes"] = [
    {
        "change": 855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    }
]

snapshots["test_events_decoder_erc1155_transfer_batch currency_changes"] = [
    {
        "change": -4369,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xffffffffffffffffffffffffffffffffffffffff",
        "type": "ERC-1155",
    },
    {
        "change": 4369,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
    {
        "change": -8738,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        "owner": "0xffffffffffffffffffffffffffffffffffffffff",
        "type": "ERC-1155",
    },
    {
        "change": 8738,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
]

snapshots["test_events_decoder_erc1155_transfer_single currency_changes"] = [
    {
        "change": -855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xffffffffffffffffffffffffffffffffffffffff",
        "type": "ERC-1155",
    },
    {
        "change": 855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0xabababababababababababababababababababababababababababababababab",
        "owner": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "type": "ERC-1155",
    },
]

snapshots["test_events_decoder_erc20_transfer currency_changes"] = [
    {
        "change": -855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0x916b2aff900d06c526b4935f999462b65f1a24fe",
        "type": "ERC-20",
    },
    {
        "change": 855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0xd68060e9b273492d643a8eca70ad18c9ce2fb378",
        "type": "ERC-20",
    },
]

snapshots["test_events_decoder_erc721_transfer currency_changes"] = [
    {
        "change": -1,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0x0000000000000000000000000000000000000000000000000bde68a8201b8caf",
        "owner": "0x916b2aff900d06c526b4935f999462b65f1a24fe",
        "type": "ERC-721",
    },
    {
        "change": 1,
        "currency_identifier": "0x000000000000000000000000000000000000abcd-0x0000000000000000000000000000000000000000000000000bde68a8201b8caf",
        "owner": "0xd68060e9b273492d643a8eca70ad18c9ce2fb378",
        "type": "ERC-721",
    },
]

snapshots["test_events_decoder_erc777_burned currency_changes"] = [
    {
        "change": -855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0xd68060e9b273492d643a8eca70ad18c9ce2fb378",
        "type": "ERC-777",
    }
]

snapshots["test_events_decoder_erc777_mint currency_changes"] = [
    {
        "change": 855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0xd68060e9b273492d643a8eca70ad18c9ce2fb378",
        "type": "ERC-777",
    }
]

snapshots["test_events_decoder_erc777_sent currency_changes"] = [
    {
        "change": -855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0xffffffffffffffffffffffffffffffffffffffff",
        "type": "ERC-777",
    },
    {
        "change": 855236050549443759,
        "currency_identifier": "0x000000000000000000000000000000000000abcd",
        "owner": "0xd68060e9b273492d643a8eca70ad18c9ce2fb378",
        "type": "ERC-777",
    },
]
