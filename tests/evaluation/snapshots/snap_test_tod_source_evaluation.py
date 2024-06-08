# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_tod_source_evaluation_found evaluation_dict"] = {
    "evaluation_type": "tod_source",
    "report": {
        "found": True,
        "source": {
            "instruction": {"opcode": 84},
            "location": {
                "address": "0x8435ee7783a18a29b0c91ae375c302bbf9d73cac",
                "pc": 1234,
            },
        },
    },
}

snapshots[
    "test_tod_source_evaluation_found evaluation_str"
] = """=== Evaluation: TOD source ===
SLOAD at 8435ee7783a18a29b0c91ae375c302bbf9d73cac:1234
> output first trace:   ('0000000000000000000000000000000000000000000000000000000000001122',) | None
> output second trace:  ('0000000000000000000000000000000000000000000000000000000000001122',) | None

"""

snapshots["test_tod_source_not_found evaluation_dict_not_found"] = {
    "evaluation_type": "tod_source",
    "report": {"found": False, "source": None},
}

snapshots[
    "test_tod_source_not_found evaluation_str_not_found"
] = """=== Evaluation: TOD source ===
TOD source not found.

"""
