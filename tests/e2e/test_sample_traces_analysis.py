from pathlib import Path

import pytest

from traces_analyzer.features.feature_extraction_runner import (
    FeatureExtractionRunner,
    RunInfo,
)
from traces_analyzer.features.feature_extractor import (
    SingleToDoubleInstructionFeatureExtractor,
)
from traces_analyzer.features.extractors.instruction_differences import (
    InstructionDifferencesFeatureExtractor,
)

from traces_analyzer.features.extractors.instruction_usages import (
    InstructionUsagesFeatureExtractor,
)
from traces_analyzer.features.extractors.tod_source import TODSourceFeatureExtractor
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.parser.events_parser import parse_events
from traces_analyzer.parser.instructions.instructions import LOG3, SLOAD
from traces_analyzer.parser.instructions_parser import (
    TransactionParsingInfo,
    parse_instructions,
)
from traces_analyzer.utils.hexstring import HexString
from snapshottest.pytest import PyTestSnapshotTest


@pytest.mark.slow
def test_sample_traces_analysis_e2e(
    sample_traces_path: Path, snapshot: PyTestSnapshotTest
) -> None:
    attack_id = "62a8b9ece30161692b68cbb5"

    directory_loader = DirectoryLoader(sample_traces_path / attack_id)
    bundle = directory_loader.load()

    transactions_actual = parse_instructions(
        TransactionParsingInfo(
            bundle.tx_victim.caller,
            bundle.tx_victim.to,
            bundle.tx_victim.calldata,
            bundle.tx_victim.value,
        ),
        parse_events(bundle.tx_victim.trace_actual),
    )
    transactions_reverse = parse_instructions(
        TransactionParsingInfo(
            bundle.tx_victim.caller,
            bundle.tx_victim.to,
            bundle.tx_victim.calldata,
            bundle.tx_victim.value,
        ),
        parse_events(bundle.tx_victim.trace_reverse),
    )

    instruction_usage_analyzer = SingleToDoubleInstructionFeatureExtractor(
        InstructionUsagesFeatureExtractor(), InstructionUsagesFeatureExtractor()
    )
    tod_source_analyzer = TODSourceFeatureExtractor()
    instruction_input_analyzer = InstructionDifferencesFeatureExtractor()

    run_info = RunInfo(
        feature_extractors=[
            instruction_usage_analyzer,
            tod_source_analyzer,
            instruction_input_analyzer,
        ],
        # TODO: why is the reverse one first? check this and document it
        transactions=(transactions_actual, transactions_reverse),
    )

    runner = FeatureExtractionRunner(run_info)
    runner.run()

    assert (
        bundle.tx_victim.hash.with_prefix()
        == "0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6"
    )

    # Instruction usage has found 17 contracts
    assert len(instruction_usage_analyzer.one.get_used_opcodes_per_contract()) == 17
    assert len(instruction_usage_analyzer.two.get_used_opcodes_per_contract()) == 17

    # TOD source
    tod_source = tod_source_analyzer.get_tod_source()
    assert tod_source.found
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.program_counter == 2401
    assert (
        tod_source.instruction_one.call_context.code_address.with_prefix()
        == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    )

    # Instruction differences
    only_first_executions, only_second_executions = (
        instruction_input_analyzer.get_instructions_only_executed_by_one_trace()
    )
    # The same instructions have been executed, only with different inputs/outputs
    assert len(only_first_executions) == 0
    assert len(only_second_executions) == 0

    instruction_input_changes = (
        instruction_input_analyzer.get_instructions_with_different_inputs()
    )
    assert len(instruction_input_changes) > 0

    input_changes = instruction_input_analyzer.get_instructions_with_different_inputs()
    assert len(input_changes) > 0

    changed_logs_with_3_topics = [
        change for change in input_changes if change.opcode == LOG3.opcode
    ]
    assert len(changed_logs_with_3_topics) == 3
    # event Transfer(address indexed _from, address indexed _to, uint256 _value)
    # TODO: the order of the changed inputs is non-deterministc. Should we change it to be deterministic somehow?
    transfer_log = next(log for log in changed_logs_with_3_topics if log.program_counter == 10748)
    assert transfer_log.stack_input_changes == []
    assert (
        transfer_log.instruction_one.get_accesses().stack
        == transfer_log.instruction_two.get_accesses().stack
    )
    assert (
        transfer_log.instruction_one.get_accesses().memory
        != transfer_log.instruction_two.get_accesses().memory
    )
    accesses = transfer_log.instruction_one.get_accesses()
    assert accesses.stack[0].value.get_hexstring().as_int() == 0x60
    assert accesses.stack[1].value.get_hexstring().as_int() == 0x20
    assert accesses.stack[2].value.get_hexstring() == HexString(
        "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    ).as_size(32)
    assert accesses.stack[3].value.get_hexstring() == HexString(
        "6da0fd433c1a5d7a4faa01111c044910a184553"
    ).as_size(32)
    assert accesses.stack[4].value.get_hexstring() == HexString(
        "def171fe48cf0115b1d80b88dc8eab59176fee57"
    ).as_size(32)

    assert transfer_log.instruction_one.step_index == 41452
    assert transfer_log.instruction_two.step_index == 41452
    assert transfer_log.program_counter == 10748
    assert (
        transfer_log.address.with_prefix()
        == "0xdac17f958d2ee523a2206206994597c13d831ec7"
    )
    assert (
        transfer_log.instruction_one.get_accesses().memory[0].value.get_hexstring()
        == "0000000000000000000000000000000000000000000000000000001da378f333"
    )
    assert (
        transfer_log.instruction_two.get_accesses().memory[0].value.get_hexstring()
        == "0000000000000000000000000000000000000000000000000000001da7149a9e"
    )

    # Call Trees are as expected
    # see https://etherscan.io/tx-decoder?tx=0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6
    # and https://etherscan.io/vmtrace?txhash=0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6&type=parity
    call_tree_normal = runner.get_call_trees()[0]

    snapshot.assert_match(str(call_tree_normal), "call_tree")

    assert not any(c.call_context.reverted for c in call_tree_normal.recurse())
    assert len(call_tree_normal.children) == 1
    multiswap_call = call_tree_normal.children[0]
    assert len(multiswap_call.children) == 7

    assert (
        multiswap_call.call_context.code_address.with_prefix()
        == "0xa7465ccd97899edcf11c56d2d26b49125674e45f"
    )
    # calldata is not part of the str representation, so the snapshot test does not cover it
    assert (
        multiswap_call.call_context.calldata.get_hexstring()
        == "a94e78ef00000000000000000000000000000000000000000000000000000000000000200000000000000000000000007fc66500c84a76ad7e9c93437bfc5ac33e2ddae900000000000000000000000000000000000000000000004f3372af4a4db400000000000000000000000000000000000000000000000000000000009438a009d600000000000000000000000000000000000000000000000000000094aacd32b200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e60000000000000000000000000000000000000000000000000000000006179191c77949380370611ecbc552de99c7747f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000640000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000003200000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e07000000000000000000000000000000000000000000000000000000000000019000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4dfc14d2af169b0d36c4eff567ada9b2e0cae044f0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de4d75ea151a61d06868e31f8988d28dfe5e9df57b400000000000000000000000000000000000000000000000000000000000000050000000000000000000000006317c5e82a06e1d8bf200d21f4510ac2c038ac810000000000000000000000000000000000000000000000000000000000001db000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001000000000000000000000000c697051d1c6296c24ae3bcef39aca743861d9a8100000000000000000000000000000000000000000000003c3157290f82bc00000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000003a0430bf7cd2633af111ce3204db4b0990857a6f0000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002e000000000000000000000000000000000000000000000000000000000000004400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000def1c0ded9bec7f1a1670819833240f027b25eff0000000000000000000000000000000000000000000000000000000000000a2800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001c0000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000026fe426cf0000000000000000000000000000000000000000000000002447f63d3c99d93ed0000000000000000000000000000006daea1723962647b7e189d311d757fb793000000000000000000000000def171fe48cf0115b1d80b88dc8eab59176fee570000000000000000000000008591204047dc7d6edc782fa3cc8ee29e2bdd61e50000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006179191c026280466a8fd8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000001c96ad2c1c7cc01ae27bb49f214e96e6c7ee6c5f88aa790d45fd0268c0422cf8e44209553f8e62741e464657e563f70c6f1d5d4ecdc4dd881d4b5e736cc45514190000000000000000000000000000000000000000000000000000000000000004000000000000000000000000f9234cb08edb93c0d4a4d4c70cc3ffd070e78e0700000000000000000000000000000000000000000000000000000000000007d000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000004de406da0fd433c1a5d7a4faa01111c044910a184553000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000d51a44d3fae010294c616388b506acda1bfaae46000000000000000000000000000000000000000000000000000000000000151800000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    )
