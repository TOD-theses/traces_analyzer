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
                "ETHER-Wei": {
                    "change": 10,
                    "currency_identifier": "Wei",
                    "owner": "0x000000000000000000000000000000000000cccc",
                    "type": "ETHER",
                }
            }
        },
        "losses": {
            "0x000000000000000000000000000000000000aaaa": {
                "ETHER-Wei": {
                    "change": -8,
                    "currency_identifier": "Wei",
                    "owner": "0x000000000000000000000000000000000000aaaa",
                    "type": "ETHER",
                }
            },
            "0x000000000000000000000000000000000000bbbb": {
                "ETHER-Wei": {
                    "change": -2,
                    "currency_identifier": "Wei",
                    "owner": "0x000000000000000000000000000000000000bbbb",
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
> 0x000000000000000000000000000000000000cccc lost 10 ETHER Wei


"""
