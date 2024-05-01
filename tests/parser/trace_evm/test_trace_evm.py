from tests.test_utils.test_utils import _test_group, _test_oracle, mock_env
from traces_analyzer.parser.instructions.instructions import MLOAD
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_trace_evm_mload():
    env = mock_env(
        step_index=3,
        stack_contents=["2"],
        memory_content=_test_group("000011223344", 2),
    )
    evm = TraceEVM(env, verify_storages=False)
    mload_metadata = InstructionMetadata(MLOAD.opcode, 1)

    mload = evm.step(mload_metadata, _test_oracle())

    padded_value = "11223344" + (28) * 2 * "0"
    accesses = mload.get_accesses()
    assert len(accesses.memory) == 1
    assert accesses.memory[0].offset == 0x2
    assert accesses.memory[0].value.get_hexstring() == padded_value
    # the access outside of memory range is padded by the current instruction (3)
    assert accesses.memory[0].value.depends_on_instruction_indexes() == {2, 3}
    assert mload.stack_outputs == (padded_value,)
