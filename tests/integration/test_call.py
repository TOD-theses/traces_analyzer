from tests.test_utils.test_utils import _TestCounter, _test_hash_addr, _test_oracle, _test_push_steps, _test_root
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_graph import build_information_flow_graph
from traces_analyzer.parser.instructions.instructions import (
    CALL,
    CALLDATACOPY,
    CALLVALUE,
    LOG0,
    MSTORE,
    MSTORE8,
    RETURN,
)
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_call_data_flow() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    initial_root_memory = "00" * 0x20 + "00" * 29 + "abcdef"
    calldata_child_memory = "abcdef" + 29 * "00"
    calldata_value_memory = "abcdef000034" + 26 * "00"
    post_call_memory = "abcdef000034" + 55 * "00" + "abcdef"

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # write to memory
        *_test_push_steps(reversed(["0x20", "0xabcdef"]), step_index, "push_mstore"),
        (InstructionMetadata(MSTORE.opcode, step_index.next("mstore")), _test_oracle(memory=initial_root_memory)),
        # call with abcdef as calldata and value 0x1234
        # writes 16 bytes from the call return data to 0x0
        *_test_push_steps(
            reversed(["0x0", _test_hash_addr("target address"), "0x1234", hex(0x20 + 29), "3", "0x0", "0x10"]),
            step_index,
            "push_call",
            base_oracle=_test_oracle(memory=initial_root_memory),
        ),
        (InstructionMetadata(CALL.opcode, step_index.next("call")), _test_oracle(depth=2)),
        # take calldata and callvalue and return them
        *_test_push_steps(
            reversed(["0x0", "0x0", "0x3"]),
            step_index,
            "push_calldatacopy",
            base_oracle=_test_oracle(depth=2),
        ),
        (
            InstructionMetadata(CALLDATACOPY.opcode, step_index.next("calldatacopy")),
            _test_oracle(depth=2, memory=calldata_child_memory),
        ),
        (
            InstructionMetadata(CALLVALUE.opcode, step_index.next("callvalue")),
            _test_oracle(depth=2, stack=["0x1234"], memory=calldata_child_memory),
        ),
        *_test_push_steps(
            reversed(["0x5"]),
            step_index,
            "push_mstore8",
            base_oracle=_test_oracle(depth=2, stack=["0x1234"], memory=calldata_child_memory),
        ),
        (
            InstructionMetadata(MSTORE8.opcode, step_index.next("mstore8")),
            _test_oracle(depth=2, memory=calldata_value_memory),
        ),
        *_test_push_steps(
            reversed(["0x0", "0x6"]),
            step_index,
            "push_return",
            base_oracle=_test_oracle(depth=2, memory=calldata_value_memory),
        ),
        (
            InstructionMetadata(RETURN.opcode, step_index.next("return")),
            _test_oracle(depth=1, stack=["0x1"], memory=post_call_memory),
        ),
        # log the returned data
        *_test_push_steps(
            reversed(["0x0", "0x10"]),
            step_index,
            "push_log0",
            base_oracle=_test_oracle(depth=1, stack=["0x1"], memory=post_call_memory),
        ),
        (
            InstructionMetadata(LOG0.opcode, step_index.next("log0")),
            _test_oracle(depth=1, stack=["0x1"], memory=post_call_memory),
        ),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str | int]]] = [
        (
            "log0",
            {
                # abcdef passed through calldata and return
                "push_mstore_0",
                # memory expansion to 0x40 (0x20 + the padded abcdef is only 0x30 big, memory is multiples of 0x20)
                "mstore",
                # 0x1234 passed through callvalue and return
                "push_call_4",
                # memory expansion 0x20
                "calldatacopy",
                # stack args for LOG0
                "push_log0_0",
                "push_log0_1",
            },
        ),
    ]

    for name, should_depend_on in expected_dependencies:
        edges = sorted(information_flow_graph.in_edges(step_index.lookup(name)))
        expected_edges = sorted(
            [
                (
                    step_index.lookup(dependency_name) if isinstance(dependency_name, str) else dependency_name,
                    step_index.lookup(name),
                )
                for dependency_name in should_depend_on
            ]
        )
        assert edges == expected_edges, (
            f"Instruction '{name}' should depend on '{should_depend_on}." f" Found {edges}, expected {expected_edges}'."
        )
