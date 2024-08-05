# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_currency_changes_extractor currency changes"] = [
    (
        GenericRepr("<CALL@000000000000000000000000000000000000aaaa:1#0>"),
        {
            "change": -10,
            "owner": "0x000000000000000000000000000000000000aaaa",
            "token_address": None,
            "type": "ETHER",
        },
    ),
    (
        GenericRepr("<CALL@000000000000000000000000000000000000aaaa:1#0>"),
        {
            "change": 10,
            "owner": "0x000000000000000000000000000000000000bbbb",
            "token_address": None,
            "type": "ETHER",
        },
    ),
    (
        GenericRepr("<CALLCODE@000000000000000000000000000000000000aaaa:1#0>"),
        {
            "change": -20,
            "owner": "0x000000000000000000000000000000000000aaaa",
            "token_address": None,
            "type": "ETHER",
        },
    ),
    (
        GenericRepr("<CALLCODE@000000000000000000000000000000000000aaaa:1#0>"),
        {
            "change": 20,
            "owner": "0x000000000000000000000000000000000000cccc",
            "token_address": None,
            "type": "ETHER",
        },
    ),
    (
        GenericRepr("<CALL@000000000000000000000000000000000000bbbb:1#0>"),
        {
            "change": -10,
            "owner": "0x000000000000000000000000000000000000bbbb",
            "token_address": None,
            "type": "ETHER",
        },
    ),
    (
        GenericRepr("<CALL@000000000000000000000000000000000000bbbb:1#0>"),
        {
            "change": 10,
            "owner": "0x000000000000000000000000000000000000cccc",
            "token_address": None,
            "type": "ETHER",
        },
    ),
]
