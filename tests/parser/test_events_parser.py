from traces_analyzer.parser.events_parser import parse_events
from traces_analyzer.utils.hexstring import HexString


def test_events_parser():
    jsonl = [
        '{"pc":0,"op":96,"gas":"0x2284c","gasCost":"0x3","stack":[],"depth":1,"returnData":"0x","refund":"0x0","memSize":"0","opName":"PUSH1","memory":"0x"}',
        '{"pc":2,"op":96,"gas":"0x22849","gasCost":"0x3","stack":["0x80"],"depth":1,"returnData":"0x","refund":"0x0","memSize":"0","opName":"PUSH1","memory":"0x"}',
        '{"pc":4,"op":82,"gas":"0x22846","gasCost":"0xc","stack":["0x80","0x40"],"depth":1,"returnData":"0x","refund":"0x0","memSize":"0","opName":"MSTORE","memory":"0x"}',
        '{"pc":5,"op":96,"gas":"0x2283a","gasCost":"0x3","stack":[],"depth":1,"returnData":"0x","refund":"0x0","memSize":"96","opName":"PUSH1","memory":"0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080"}',
    ]

    events = list(parse_events(jsonl))

    assert len(events) == 4
    assert events[0].op == 96
    assert events[0].pc == 0
    assert events[0].stack == []
    assert events[0].memory == ""
    assert events[0].depth == 1

    assert events[1].op == 96
    assert events[1].pc == 2
    assert events[1].stack == [HexString("80").as_size(32)]
    assert events[1].memory == ""
    assert events[1].depth == 1

    assert events[2].op == 82
    assert events[2].pc == 4
    assert events[2].stack == [HexString("40").as_size(32), HexString("80").as_size(32)]
    assert events[2].memory == ""
    assert events[2].depth == 1

    assert events[3].op == 96
    assert events[3].pc == 5
    assert events[3].stack == []
    assert (
        events[3].memory
        == "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080"
    )
    assert events[3].depth == 1
