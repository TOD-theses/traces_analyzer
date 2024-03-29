from pathlib import Path
from traces_analyzer.analysis.analyzer import SingleToDoubleTraceAnalyzer
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.analysis.analysis_runner import RunInfo, AnalysisRunner
from traces_analyzer.preprocessing.instructions import SLOAD


def test_runner(sample_traces_path: Path):
    trace_actual_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "actual"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )
    trace_reverse_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "reverse"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )

    with open(trace_reverse_path) as trace_reverse_file, open(trace_actual_path) as trace_actual_file:
        instruction_usage_analyzer = SingleToDoubleTraceAnalyzer(InstructionUsageAnalyzer(), InstructionUsageAnalyzer())
        tod_source_analyzer = TODSourceAnalyzer()
        instruction_input_analyzer = InstructionInputAnalyzer()

        run_info = RunInfo(
            analyzers=[instruction_usage_analyzer, tod_source_analyzer, instruction_input_analyzer],
            traces_jsons=(trace_reverse_file, trace_actual_file),
        )

        runner = AnalysisRunner(run_info)
        runner.run()

        # assert that analysis tools found something
        assert len(instruction_usage_analyzer.one.get_used_opcodes_per_contract()) == 4
        assert len(instruction_usage_analyzer.two.get_used_opcodes_per_contract()) == 4

        assert tod_source_analyzer.get_tod_source().found
        assert tod_source_analyzer.get_tod_source().instruction_one.opcode == SLOAD.opcode

        _, only_second = instruction_input_analyzer.get_instructions_only_executed_by_one_trace()
        assert only_second
