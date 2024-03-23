from traces_analyzer.analysis.tod_source_analyzer import TODSource
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import SLOAD, Instruction


def test_tod_source_evaluation_found():
    sload_event = TraceEvent(1234, SLOAD.opcode, ["0x1122"], 0)
    event_first_trace = TraceEvent(1235, 0x0, ["0x10"], 0)
    event_second_trace = TraceEvent(1235, 0x0, ["0x20"], 0)
    call_frame = CallFrame(parent=None, depth=0, msg_sender="0xsender", address="0xaddress")

    tod_source = TODSource(
        found=True,
        instruction_one=Instruction(sload_event, event_first_trace, call_frame),
        instruction_two=Instruction(sload_event, event_second_trace, call_frame),
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "tod_source",
        "report": {
            "found": True,
            "source": {
                "location": {
                    "address": "0xaddress",
                    "pc": 1234,
                },
                "instruction": {
                    "opcode": SLOAD.opcode,
                },
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "TOD source" in evaluation_str
    assert hex(SLOAD.opcode) in evaluation_str


def test_tod_source_not_found():
    tod_source = TODSource(
        found=False,
        instruction_one=None,
        instruction_two=None,
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "tod_source",
        "report": {
            "found": False,
            "source": None,
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "TOD source" in evaluation_str
    assert "not found" in evaluation_str
