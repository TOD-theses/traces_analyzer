from tests.test_utils.test_utils import _TestCounter, _test_oracle, _test_root
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_graph import build_information_flow_graph
from traces_analyzer.parser.instructions.instructions import KECCAK256, LOG1, MCOPY, MSTORE, PUSH32
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_information_flow() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=False)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mstore_value")), _test_oracle(stack=["0xabcdef"])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mstore_offset")), _test_oracle(stack=["0x20"])),
        (InstructionMetadata(MSTORE.opcode, step_index.next("mstore")), _test_oracle()),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mcopy_size")), _test_oracle(stack=[hex(32)])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mcopy_offset")), _test_oracle(stack=["0x20"])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mcopy_dstoffset")), _test_oracle(stack=["0x50"])),
        (InstructionMetadata(MCOPY.opcode, step_index.next("mcopy")), _test_oracle()),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_keccak256_size")), _test_oracle(stack=["0x3"])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_keccak256_offset")), _test_oracle(stack=["0x50"])),
        (
            InstructionMetadata(KECCAK256.opcode, step_index.next("keccak256")),
            _test_oracle(stack=["0xb1f1f26239f5476c09b367f6b4fcfa4f410c7938676514889db27a387c000238"]),
        ),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_mstore_2_offset")), _test_oracle(stack=["0x20"])),
        (InstructionMetadata(MSTORE.opcode, step_index.next("mstore_2")), _test_oracle()),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_log1_topic")), _test_oracle(stack=["0xaaaaaa"])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_log1_size")), _test_oracle(stack=[hex(32)])),
        (InstructionMetadata(PUSH32.opcode, step_index.next("push_log1_offset")), _test_oracle(stack=["0x20"])),
        (InstructionMetadata(LOG1.opcode, step_index.next("log1")), _test_oracle()),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str]]] = [
        ("push_mstore_value", set()),
        ("push_mstore_offset", set()),
        ("mstore", {"push_mstore_value", "push_mstore_offset"}),
        ("push_mcopy_size", set()),
        ("push_mcopy_offset", set()),
        ("push_mcopy_dstoffset", set()),
        ("mcopy", {"push_mcopy_size", "push_mcopy_offset", "push_mcopy_dstoffset", "push_mstore_value"}),
        ("push_keccak256_size", set()),
        ("push_keccak256_offset", set()),
        ("keccak256", {"push_keccak256_size", "push_keccak256_offset", "push_mstore_value"}),
        ("push_mstore_2_offset", set()),
        ("mstore_2", {"push_mstore_2_offset", "keccak256"}),
        ("push_log1_topic", set()),
        ("push_log1_size", set()),
        ("push_log1_offset", set()),
        ("log1", {"push_log1_topic", "push_log1_size", "push_log1_offset", "keccak256"}),
    ]

    for name, should_depend_on in expected_dependencies:
        edges = sorted(information_flow_graph.in_edges(step_index.lookup(name)))
        expected_edges = sorted(
            [(step_index.lookup(dependency_name), step_index.lookup(name)) for dependency_name in should_depend_on]
        )
        assert edges == expected_edges, (
            f"Instruction '{name}' should depend on '{should_depend_on}." f" Found {edges}, expected {expected_edges}'."
        )

    # test if edge attributes are set
    keccak_log_edge = information_flow_graph[step_index.lookup("keccak256")][step_index.lookup("log1")][0]
    assert (
        keccak_log_edge["storage_byte_group"].get_hexstring()
        == "b1f1f26239f5476c09b367f6b4fcfa4f410c7938676514889db27a387c000238"
    )
