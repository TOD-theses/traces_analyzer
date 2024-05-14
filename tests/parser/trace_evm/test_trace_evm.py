from tests.test_utils.test_utils import _TestCounter, _test_group, _test_oracle, _test_push_steps, _test_root, mock_env
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.instructions.instructions import MLOAD, MSTORE, PUSH32, STATICCALL
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_trace_evm_mload():
    env = mock_env(
        step_index=3,
        storage_step_index=2,
        stack_contents=["2"],
        memory_content="000011223344",
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


def test_trace_evm_staticcall_precompiled() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        *_test_push_steps(reversed(["0x2", "0xabcdef" + "00" * 29]), step_index, "push_mstore", _test_oracle()),
        (InstructionMetadata(MSTORE.opcode, step_index.next("mstore")), _test_oracle(memory="0000abcdef")),
        *_test_push_steps(
            reversed([hex(1234), hex(2), hex(2), hex(3), hex(10), hex(32)]),
            step_index,
            "push_staticcall",
            _test_oracle(memory="0000abcdef"),
        ),
        (
            InstructionMetadata(STATICCALL.opcode, step_index.next("staticcall")),
            _test_oracle(
                memory="0000abcdef0000000000995da3cf545787d65f9ced52674e92ee8171c87c7a4008aa4349ec47d21609a7",
                stack=[hex(1)],
            ),
        ),
    ]

    for instruction_metadata, oracle in steps:
        evm.step(instruction_metadata, oracle)

    assert len(env.stack.get_all()) == 1
    assert env.stack.get_all()[0].get_hexstring().as_int() == 0x1
    assert (
        env.memory.get_all().get_hexstring()
        == "0000abcdef0000000000995da3cf545787d65f9ced52674e92ee8171c87c7a4008aa4349ec47d21609a7"
        + "00" * (64 - 10 - 32)
    )
