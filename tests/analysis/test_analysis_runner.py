import json
from unittest.mock import Mock

from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.analysis.analysis_runner import RunInfo, AnalysisRunner
from traces_analyzer.preprocessing.instructions import POP, op_from_class


def test_analysis_runner_empty_does_not_call_analyzer():
    analyzer_mock = Mock(spec_set=DoubleTraceAnalyzer)

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

    analyzer_mock.on_analysis_step.assert_not_called()


def test_analysis_runner_calls_analyzer():
    analyzer_mock = Mock(spec_set=DoubleTraceAnalyzer)
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

    calls = analyzer_mock.on_analysis_step.call_args_list
    assert len(calls) == 2
    call_1, call_2 = calls
    step_1 = call_1.args[0]
    step_2 = call_2.args[0]
    assert isinstance(step_1, AnalysisStepDoubleTrace)
    assert isinstance(step_2, AnalysisStepDoubleTrace)

    # first step both are available
    assert step_1.trace_event_one.op == op_from_class(POP)
    assert step_1.trace_event_two.op == op_from_class(POP)
    assert step_1.instruction_one.opcode == op_from_class(POP)
    assert step_1.instruction_two.opcode == op_from_class(POP)
    assert step_1.instruction_one.call_frame.depth == 1

    # second step only the 2nd trace had an event
    assert step_2.trace_event_one is None
    assert step_2.trace_event_two.op == op_from_class(POP)
    assert step_2.instruction_one is None
    assert step_2.instruction_two.opcode == op_from_class(POP)


def json_dumps_all(items: list[dict]) -> list[str]:
    return [json.dumps(item) for item in items]
