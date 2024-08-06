import json
import pytest
from traces_analyzer.loader.event_parser import (
    VmTraceDictEventsParser,
    VmTraceEventsParser,
)
from traces_analyzer.loader.in_memory_loader import InMemoryLoader
from traces_analyzer.loader.types import TxData

vm_trace = """{
    "failed": false,
    "gas": 798496,
    "returnValue": "000000000000000000000000000000000000000000000000000000949cbea634",
    "structLogs": [
        {
            "depth": 1,
            "gas": 1537802,
            "gasCost": 3,
            "memory": [],
            "op": "PUSH1",
            "pc": 0,
            "stack": []
        },
        {
            "depth": 1,
            "gas": 1537799,
            "gasCost": 3,
            "memory": [],
            "op": "PUSH1",
            "pc": 2,
            "stack": [
                "0x80"
            ]
        },
        {
            "depth": 1,
            "gas": 1537796,
            "gasCost": 12,
            "memory": [],
            "op": "MSTORE",
            "pc": 4,
            "stack": [
                "0x80",
                "0x40"
            ]
        },
        {
            "depth": 1,
            "gas": 1537784,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "PUSH1",
            "pc": 5,
            "stack": []
        },
        {
            "depth": 1,
            "gas": 1537781,
            "gasCost": 2,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "CALLDATASIZE",
            "pc": 7,
            "stack": [
                "0x4"
            ]
        },
        {
            "depth": 1,
            "gas": 1537779,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "LT",
            "pc": 8,
            "stack": [
                "0x4",
                "0xea4"
            ]
        },
        {
            "depth": 1,
            "gas": 1537776,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "PUSH2",
            "pc": 9,
            "stack": [
                "0x0"
            ]
        },
        {
            "depth": 1,
            "gas": 1537773,
            "gasCost": 10,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "JUMPI",
            "pc": 12,
            "stack": [
                "0x0",
                "0x19a"
            ]
        },
        {
            "depth": 1,
            "gas": 1537763,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "PUSH1",
            "pc": 13,
            "stack": []
        },
        {
            "depth": 1,
            "gas": 1537760,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "CALLDATALOAD",
            "pc": 15,
            "stack": [
                "0x0"
            ]
        },
        {
            "depth": 1,
            "gas": 1537757,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "PUSH1",
            "pc": 16,
            "stack": [
                "0xa94e78ef00000000000000000000000000000000000000000000000000000000"
            ]
        },
        {
            "depth": 1,
            "gas": 1537754,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "SHR",
            "pc": 18,
            "stack": [
                "0xa94e78ef00000000000000000000000000000000000000000000000000000000",
                "0xe0"
            ]
        },
        {
            "depth": 1,
            "gas": 1537751,
            "gasCost": 3,
            "memory": [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000080"
            ],
            "op": "DUP1",
            "pc": 19,
            "stack": [
                "0xa94e78ef"
            ]
        }
    ]
}
"""


@pytest.mark.parametrize(
    "data,parser",
    [
        (vm_trace, VmTraceEventsParser()),
        (json.loads(vm_trace), VmTraceDictEventsParser()),
    ],
)
def test_in_memory_loader(data, parser):
    id = "test"
    tx: TxData = {
        "hash": "0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6",
        "from": "0x8591204047dc7d6edc782fa3cc8ee29e2bdd61e5",
        "to": "0xdef171fe48cf0115b1d80b88dc8eab59176fee57",
        "input": "a94e78ef00000000000000000000000000000000000000000000000000000000000000200000000000000000000000007fc66500c84a76ad7e9c93437bfc5ac33e2ddae900000000000000000000000000000000000000000000004f3372af4a4db400000000000000000000000000000000000000000000000000000000009438a009d600000000000000000000000000000000000000000000000000000094aacd32b200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e60000000000000000000000000000000000000000000000000000000006179191c77949380370611ecbc552de99c7747f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000640000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000003200000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e07000000000000000000000000000000000000000000000000000000000000019000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4dfc14d2af169b0d36c4eff567ada9b2e0cae044f0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4d75ea151a61d06868e31f8988d28dfe5e9df57b400000000000000000000000000000000000000000000000000000000000000050000000000000000000000006317c5e82a06e1d8bf200d21f4510ac2c038ac810000000000000000000000000000000000000000000000000000000000001db000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001000000000000000000000000c697051d1c6296c24ae3bcef39aca743861d9a8100000000000000000000000000000000000000000000003c3157290f82bc00000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002e000000000000000000000000000000000000000000000000000000000000004400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000def1c0ded9bec7f1a1670819833240f027b25eff0000000000000000000000000000000000000000000000000000000000000a2800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001c0000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000026fe426cf0000000000000000000000000000000000000000000000002447f63d3c99d93ed0000000000000000000000000000006daea1723962647b7e189d311d757fb793000000000000000000000000def171fe48cf0115b1d80b88dc8eab59176fee570000000000000000000000008591204047dc7d6edc782fa3cc8ee29e2bdd61e50000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006179191c026280466a8fd8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000001c96ad2c1c7cc01ae27bb49f214e96e6c7ee6c5f88aa790d45fd0268c0422cf8e44209553f8e62741e464657e563f70c6f1d5d4ecdc4dd881d4b5e736cc45514190000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de406da0fd433c1a5d7a4faa01111c044910a184553000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000d51a44d3fae010294c616388b506acda1bfaae46000000000000000000000000000000000000000000000000000000000000151800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "value": "0x0",
    }

    with InMemoryLoader(
        id,
        tx,
        tx,
        data,
        data,
        data,
        data,
        parser=parser,
    ) as bundle:
        assert bundle.id == id

        assert (
            bundle.tx_a.hash.with_prefix()
            == "0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6"
        )
        assert (
            bundle.tx_a.caller.with_prefix()
            == "0x8591204047dc7d6edc782fa3cc8ee29e2bdd61e5"
        )
        assert (
            bundle.tx_a.to.with_prefix() == "0xdef171fe48cf0115b1d80b88dc8eab59176fee57"
        )
        assert (
            bundle.tx_a.calldata
            == "a94e78ef00000000000000000000000000000000000000000000000000000000000000200000000000000000000000007fc66500c84a76ad7e9c93437bfc5ac33e2ddae900000000000000000000000000000000000000000000004f3372af4a4db400000000000000000000000000000000000000000000000000000000009438a009d600000000000000000000000000000000000000000000000000000094aacd32b200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e60000000000000000000000000000000000000000000000000000000006179191c77949380370611ecbc552de99c7747f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000640000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000003200000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e07000000000000000000000000000000000000000000000000000000000000019000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4dfc14d2af169b0d36c4eff567ada9b2e0cae044f0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4d75ea151a61d06868e31f8988d28dfe5e9df57b400000000000000000000000000000000000000000000000000000000000000050000000000000000000000006317c5e82a06e1d8bf200d21f4510ac2c038ac810000000000000000000000000000000000000000000000000000000000001db000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001000000000000000000000000c697051d1c6296c24ae3bcef39aca743861d9a8100000000000000000000000000000000000000000000003c3157290f82bc00000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002e000000000000000000000000000000000000000000000000000000000000004400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000def1c0ded9bec7f1a1670819833240f027b25eff0000000000000000000000000000000000000000000000000000000000000a2800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001c0000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000026fe426cf0000000000000000000000000000000000000000000000002447f63d3c99d93ed0000000000000000000000000000006daea1723962647b7e189d311d757fb793000000000000000000000000def171fe48cf0115b1d80b88dc8eab59176fee570000000000000000000000008591204047dc7d6edc782fa3cc8ee29e2bdd61e50000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006179191c026280466a8fd8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000001c96ad2c1c7cc01ae27bb49f214e96e6c7ee6c5f88aa790d45fd0268c0422cf8e44209553f8e62741e464657e563f70c6f1d5d4ecdc4dd881d4b5e736cc45514190000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de406da0fd433c1a5d7a4faa01111c044910a184553000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000d51a44d3fae010294c616388b506acda1bfaae46000000000000000000000000000000000000000000000000000000000000151800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        )
        assert bundle.tx_a.value.as_int() == 0

        assert len(list(bundle.tx_a.events_normal)) == 13
        assert len(list(bundle.tx_a.events_reverse)) == 13
