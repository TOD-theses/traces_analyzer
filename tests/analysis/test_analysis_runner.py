import json
from unittest.mock import Mock

from traces_analyzer.analysis.analyzer import DoubleInstructionAnalyzer
from traces_analyzer.analysis.analysis_runner import RunInfo, AnalysisRunner
from traces_analyzer.preprocessing.instructions import POP, op_from_class


def test_analysis_runner_empty_does_not_call_analyzer():
    analyzer_mock = Mock(spec_set=DoubleInstructionAnalyzer)

    runner = AnalysisRunner(
        RunInfo(
            analyzers=[analyzer_mock],
            traces_jsons=([], []),
            sender="0xsender",
            to="0xrootcontract",
            calldata="",
        )
    )
    runner.run()

    analyzer_mock.on_instructions.assert_not_called()


def test_analysis_runner_calls_analyzer():
    analyzer_mock = Mock(spec_set=DoubleInstructionAnalyzer)
    trace_one = [{"pc": 1, "op": op_from_class(POP), "stack": ["0x1234"], "depth": 1}]
    trace_two = trace_one + [{"pc": 2, "op": op_from_class(POP), "stack": ["0x1111"], "depth": 1}]

    runner = AnalysisRunner(
        RunInfo(
            analyzers=[analyzer_mock],
            traces_jsons=(json_dumps_all(trace_one), json_dumps_all(trace_two)),
            sender="0xsender",
            to="0xrootcontract",
            calldata="",
        )
    )
    runner.run()

    calls = analyzer_mock.on_instructions.call_args_list
    assert len(calls) == 2
    call_1, call_2 = calls
    instructions_first_call = call_1.args
    instructions_second_call = call_2.args

    assert instructions_first_call[0].opcode == op_from_class(POP)
    assert instructions_first_call[1].opcode == op_from_class(POP)
    assert instructions_first_call[0].call_frame.depth == 1

    assert instructions_second_call[0] is None
    assert instructions_second_call[1].opcode == op_from_class(POP)


def json_dumps_all(items: list[dict]) -> list[str]:
    return [json.dumps(item) for item in items]
