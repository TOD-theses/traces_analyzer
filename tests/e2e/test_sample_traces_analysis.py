from pathlib import Path

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.analyzer import SingleToDoubleTraceAnalyzer
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer

from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.preprocessing.instructions import SLOAD


def test_sample_traces_analysis(sample_traces_path: Path):
    attack_id = "62a8b9ece30161692b68cbb5"

    directory_loader = DirectoryLoader(sample_traces_path / attack_id)
    bundle = directory_loader.load()

    instruction_usage_analyzer = SingleToDoubleTraceAnalyzer(InstructionUsageAnalyzer(), InstructionUsageAnalyzer())
    tod_source_analyzer = TODSourceAnalyzer()
    instruction_input_analyzer = InstructionInputAnalyzer()

    run_info = RunInfo(
        analyzers=[instruction_usage_analyzer, tod_source_analyzer, instruction_input_analyzer],
        # TODO: why is the reverse one first? check this and document it
        traces_jsons=(bundle.tx_attack.trace_reverse, bundle.tx_attack.trace_actual),
    )

    runner = AnalysisRunner(run_info)
    runner.run()

    # Instruction usage has found 4 contracts
    assert len(instruction_usage_analyzer.one.get_used_opcodes_per_contract()) == 4
    assert len(instruction_usage_analyzer.two.get_used_opcodes_per_contract()) == 4

    # TOD source
    tod_source = tod_source_analyzer.get_tod_source()
    assert tod_source.found
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.program_counter == 2401
    assert tod_source.instruction_one.call_frame.code_address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"

    only_first_executions, only_second_executions = (
        instruction_input_analyzer.get_instructions_only_executed_by_one_trace()
    )
    assert len(only_first_executions) == 0
    assert len(only_second_executions) == 178  # the trace files differ exactly by 178 lines

    instruction_input_changes = instruction_input_analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) > 0
