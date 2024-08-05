# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_financial_gain_loss_evaluation evaluation_dict"] = {
    "evaluation_type": "financial_gain_loss",
    "report": {
        "gains": {
            "0x000000000000000000000000000000000000cccc": {
                "ETHER": {
                    "change": 10,
                    "owner": "0x000000000000000000000000000000000000cccc",
                    "token_address": None,
                    "type": "ETHER",
                }
            }
        },
        "losses": {
            "0x000000000000000000000000000000000000aaaa": {
                "ETHER": {
                    "change": -8,
                    "owner": "0x000000000000000000000000000000000000aaaa",
                    "token_address": None,
                    "type": "ETHER",
                }
            },
            "0x000000000000000000000000000000000000bbbb": {
                "ETHER": {
                    "change": -2,
                    "owner": "0x000000000000000000000000000000000000bbbb",
                    "token_address": None,
                    "type": "ETHER",
                }
            },
        },
    },
}

snapshots[
    "test_financial_gain_loss_evaluation evaluation_str"
] = """=== Evaluation: Financial gains and losses ===
Losses in normal compared to reverse scenario:
> 0x000000000000000000000000000000000000cccc lost 10 ETHER (in Wei)


"""
