from itertools import zip_longest
from pathlib import Path
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.instructions import SLOAD
from traces_analyzer.parser import parse_events
from traces_analyzer.runner.runner import RunInfo, Runner
from traces_analyzer.trace_reader import read_trace_file


def test_runner(sample_traces_path: Path):
    trace_normal_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_normal"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )
    trace_attack_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_attack"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )

    with open(trace_normal_path) as trace_normal_file, open(trace_attack_path) as trace_attack_file:
        tod_source_analyzer = TODSourceAnalyzer()
        instruction_input_analyzer = InstructionInputAnalyzer()

        run_info = RunInfo(
            analyzers=[tod_source_analyzer, instruction_input_analyzer],
            traces_jsons=(trace_normal_file, trace_attack_file),
        )

        runner = Runner(run_info)
        runner.run()

        # assert that analysis tools found something
        assert tod_source_analyzer.found_tod_source()
        _, only_second = instruction_input_analyzer.get_instructions_only_executed_by_one_trace()
        assert only_second
