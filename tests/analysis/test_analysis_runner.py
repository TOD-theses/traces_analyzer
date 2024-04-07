import json
from unittest.mock import Mock

from tests.conftest import TEST_ROOT_CALLFRAME
from traces_analyzer.analysis.analyzer import DoubleInstructionAnalyzer
from traces_analyzer.analysis.analysis_runner import RunInfo, AnalysisRunner
from traces_analyzer.parser.call_frame_manager import CallTree
from traces_analyzer.parser.instructions_parser import ParsedTransaction
from traces_analyzer.parser.instructions import POP, op_from_class


def test_analysis_runner_empty_does_not_call_analyzer():
    analyzer_mock = Mock(spec_set=DoubleInstructionAnalyzer)
    empty_call_tree = CallTree(TEST_ROOT_CALLFRAME)
    empty_transaction = ParsedTransaction([], empty_call_tree)

    runner = AnalysisRunner(
        RunInfo(
            analyzers=[analyzer_mock],
            transactions=(empty_transaction, empty_transaction),
        )
    )
    runner.run()

    analyzer_mock.on_instructions.assert_not_called()


def test_analysis_runner_calls_analyzer():
    analyzer_mock = Mock(spec_set=DoubleInstructionAnalyzer)
    empty_call_tree = CallTree(TEST_ROOT_CALLFRAME)
    instructions_one = [POP(op_from_class(POP), "POP", 1, TEST_ROOT_CALLFRAME, "0x1234", (), None, None, {})]
    instructions_two = instructions_one + [
        POP(op_from_class(POP), "POP", 2, TEST_ROOT_CALLFRAME, "0x1111", (), None, None, {})
    ]

    transaction_one = ParsedTransaction(instructions_one, empty_call_tree)
    transaction_two = ParsedTransaction(instructions_two, empty_call_tree)

    runner = AnalysisRunner(
        RunInfo(
            analyzers=[analyzer_mock],
            transactions=(transaction_one, transaction_two),
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
