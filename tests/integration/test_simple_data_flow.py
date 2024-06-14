from tests.test_utils.test_utils import (
    _TestCounter,
    _test_oracle,
    _test_push_steps,
    _test_root,
    assert_flow_dependencies,
)
from traces_parser.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_parser.parser.information_flow.information_flow_graph import (
    build_information_flow_graph,
)
from traces_parser.parser.instructions.instructions import (
    KECCAK256,
    LOG1,
    MCOPY,
    MSTORE,
)
from traces_parser.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_simple_information_flow() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=False)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        *_test_push_steps(reversed(["0x20", "0xabcdef"]), step_index, "push_mstore"),
        (InstructionMetadata(MSTORE.opcode, step_index.next("mstore")), _test_oracle()),
        *_test_push_steps(
            reversed(["0x50", "0x20", hex(32)]), step_index, "push_mcopy"
        ),
        (InstructionMetadata(MCOPY.opcode, step_index.next("mcopy")), _test_oracle()),
        *_test_push_steps(reversed(["0x50", "0x3"]), step_index, "push_keccak256"),
        (
            InstructionMetadata(KECCAK256.opcode, step_index.next("keccak256")),
            _test_oracle(
                stack=[
                    "0xb1f1f26239f5476c09b367f6b4fcfa4f410c7938676514889db27a387c000238"
                ]
            ),
        ),
        *_test_push_steps(reversed(["0x20"]), step_index, "push_mstore2"),
        (
            InstructionMetadata(MSTORE.opcode, step_index.next("mstore_2")),
            _test_oracle(),
        ),
        *_test_push_steps(
            reversed(["0x20", hex(32), "0xaaaaaa"]), step_index, "push_log1"
        ),
        (InstructionMetadata(LOG1.opcode, step_index.next("log1")), _test_oracle()),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [
            ("push_mstore_0", set()),
            ("push_mstore_1", set()),
            ("mstore", {"push_mstore_0", "push_mstore_1"}),
            ("push_mcopy_0", set()),
            ("push_mcopy_1", set()),
            ("push_mcopy_2", set()),
            (
                "mcopy",
                {"push_mcopy_0", "push_mcopy_1", "push_mcopy_2", "push_mstore_0"},
            ),
            ("push_keccak256_0", set()),
            ("push_keccak256_1", set()),
            ("keccak256", {"push_keccak256_0", "push_keccak256_1", "push_mstore_0"}),
            ("push_mstore2_0", set()),
            ("mstore_2", {"push_mstore2_0", "keccak256"}),
            ("push_log1_0", set()),
            ("push_log1_1", set()),
            ("push_log1_2", set()),
            ("log1", {"push_log1_0", "push_log1_1", "push_log1_2", "keccak256"}),
        ],
    )

    # test if edge attributes are set
    keccak_log_edge = information_flow_graph[step_index.lookup("keccak256")][
        step_index.lookup("log1")
    ][0]
    assert (
        keccak_log_edge["storage_byte_group"].get_hexstring()
        == "b1f1f26239f5476c09b367f6b4fcfa4f410c7938676514889db27a387c000238"
    )
