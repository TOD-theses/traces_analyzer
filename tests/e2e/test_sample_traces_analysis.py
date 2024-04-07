from pathlib import Path

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.analyzer import SingleToDoubleInstructionAnalyzer
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer

from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.parser.instructions import LOG3, SLOAD, op_from_class


def test_sample_traces_analysis(sample_traces_path: Path):
    attack_id = "62a8b9ece30161692b68cbb5"

    directory_loader = DirectoryLoader(sample_traces_path / attack_id)
    bundle = directory_loader.load()

    instruction_usage_analyzer = SingleToDoubleInstructionAnalyzer(
        InstructionUsageAnalyzer(), InstructionUsageAnalyzer()
    )
    tod_source_analyzer = TODSourceAnalyzer()
    instruction_input_analyzer = InstructionInputAnalyzer()

    run_info = RunInfo(
        analyzers=[instruction_usage_analyzer, tod_source_analyzer, instruction_input_analyzer],
        # TODO: why is the reverse one first? check this and document it
        traces_jsons=(bundle.tx_attack.trace_reverse, bundle.tx_attack.trace_actual),
        sender=bundle.tx_attack.caller,
        to=bundle.tx_attack.to,
        calldata=bundle.tx_attack.calldata,
    )

    runner = AnalysisRunner(run_info)
    runner.run()

    assert bundle.tx_attack.hash == "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0"

    # Instruction usage has found 4 contracts
    assert len(instruction_usage_analyzer.one.get_used_opcodes_per_contract()) == 4
    assert len(instruction_usage_analyzer.two.get_used_opcodes_per_contract()) == 4

    # TOD source
    tod_source = tod_source_analyzer.get_tod_source()
    assert tod_source.found
    assert tod_source.instruction_one.opcode == op_from_class(SLOAD)
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

    changed_logs_with_3_topics = [change for change in input_changes if change.opcode == op_from_class(LOG3)]
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
    assert transfer_log.address == "0xdac17f958d2ee523a2206206994597c13d831ec7"
    # NOTE: The value does not match the etherscan logs
    # the reason is likely, that the transaction is executed at the beginning of the block
    # but there are many other transac 45th transaction also makes a transfer of Tether: USDT Stablecoin (influencing the price)
    # eg https://etherscan.io/tx/0xa3c5c292cac5fe09ff3e3bd325c698fc6ad2be8558903453b330e38deb1cea03#eventlog
    assert transfer_log.first_memory_input == "000000000000000000000000000000000000000000000000000000069be06e4a"
    assert transfer_log.second_memory_input == "000000000000000000000000000000000000000000000000000000069f7ec680"

    # Call Trees are as expected
    # see https://etherscan.io/tx-decoder?tx=0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0
    # and https://etherscan.io/vmtrace?txhash=0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0&type=parity
    call_tree_normal = runner.get_call_trees()[0]
    assert not any(c.call_frame.reverted for c in call_tree_normal.recurse())
    assert len(call_tree_normal.children) == 4
    weth9_call, weth9_transfer, uniswap_staticcall, uniswap_swap = call_tree_normal.children
    assert len(weth9_call.children) == len(weth9_transfer.children) == len(uniswap_staticcall.children) == 0
    assert len(uniswap_swap.children) == 3
    tether_transfer, weth_balance, tether_balance = uniswap_swap.children
    assert len(tether_transfer.children) == len(weth_balance.children) == len(tether_balance.children) == 0

    assert call_tree_normal.call_frame.code_address == "0x11111112542d85b3ef69ae05771c2dccff4faa26"
    assert weth9_call.call_frame.code_address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    assert weth9_transfer.call_frame.code_address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    # TODO: correct parsing of addresses with leading 0s
    # assert uniswap_staticcall.call_frame.code_address == "0x06da0fd433c1a5d7a4faa01111c044910a184553"
    # assert uniswap_swap.call_frame.code_address == " 0x06da0fd433c1a5d7a4faa01111c044910a184553"
    assert tether_transfer.call_frame.code_address == "0xdac17f958d2ee523a2206206994597c13d831ec7"
    assert weth_balance.call_frame.code_address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    assert tether_balance.call_frame.code_address == "0xdac17f958d2ee523a2206206994597c13d831ec7"

    # TODO: calldata parsing from metadata file
    # assert call_tree_normal.call_frame.calldata == "000000000000000000000000000000000000000000000000000000069c35828a"
    assert weth9_call.call_frame.calldata == "d0e30db0"
    assert (
        weth9_transfer.call_frame.calldata
        == "a9059cbb00000000000000000000000006da0fd433c1a5d7a4faa01111c044910a18455300000000000000000000000000000000000000000000000062884461f1460000"
    )
    assert uniswap_staticcall.call_frame.calldata == "0902f1ac"
    # NOTE: similar to the changed log, the swap call has a different amount1Out and the transfer call has a different _value compared to the etherscan trace
    assert (
        uniswap_swap.call_frame.calldata
        == "022c0d9f0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000069be06e4a000000000000000000000000822beb1cd1bd7148d07e4107b636fd15118913bc00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000"
    )
    assert (
        tether_transfer.call_frame.calldata
        == "a9059cbb000000000000000000000000822beb1cd1bd7148d07e4107b636fd15118913bc000000000000000000000000000000000000000000000000000000069be06e4a"
    )
    assert (
        weth_balance.call_frame.calldata == "70a0823100000000000000000000000006da0fd433c1a5d7a4faa01111c044910a184553"
    )
    assert (
        tether_balance.call_frame.calldata == "70a0823100000000000000000000000006da0fd433c1a5d7a4faa01111c044910a184553"
    )
