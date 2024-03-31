from pathlib import Path

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.analyzer import SingleToDoubleTraceAnalyzer
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer

from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.preprocessing.instructions import LOG3, SLOAD


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

    # Instruction differences
    only_first_executions, only_second_executions = (
        instruction_input_analyzer.get_instructions_only_executed_by_one_trace()
    )
    assert len(only_first_executions) == 0
    assert len(only_second_executions) == 178  # the trace files differ exactly by 178 lines

    instruction_input_changes = instruction_input_analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) > 0

    input_changes = instruction_input_analyzer.get_instructions_with_different_inputs()
    assert len(input_changes) > 0

    changed_logs_with_3_topics = [change for change in input_changes if change.opcode == LOG3.opcode]
    assert len(changed_logs_with_3_topics) == 2
    # event Transfer(address indexed _from, address indexed _to, uint256 _value)
    transfer_log = changed_logs_with_3_topics[0]
    assert transfer_log.stack_input_changes == []
    assert transfer_log.first_stack_input == transfer_log.second_stack_input
    assert transfer_log.first_stack_input[0] == "0x60"
    assert transfer_log.first_stack_input[1] == "0x20"
    assert transfer_log.first_stack_input[2:] == (
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "0x6da0fd433c1a5d7a4faa01111c044910a184553",
        "0x822beb1cd1bd7148d07e4107b636fd15118913bc",
    )
    assert transfer_log.program_counter == 10748
    assert transfer_log.address == '0xdac17f958d2ee523a2206206994597c13d831ec7'
    # NOTE: The value does not match the etherscan logs
    # the reason is likely, that the transaction is executed at the beginning of the block
    # but there are many other transac 45th transaction also makes a transfer of Tether: USDT Stablecoin (influencing the price)
    # eg https://etherscan.io/tx/0xa3c5c292cac5fe09ff3e3bd325c698fc6ad2be8558903453b330e38deb1cea03#eventlog
    assert transfer_log.first_memory_input == '000000000000000000000000000000000000000000000000000000069be06e4a'
    assert transfer_log.second_memory_input == '000000000000000000000000000000000000000000000000000000069f7ec680'