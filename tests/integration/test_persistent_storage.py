from tests.test_utils.test_utils import (
    _TestCounter,
    _test_hash_addr,
    _test_oracle,
    _test_push_steps,
    _test_root,
)
from traces_analyzer.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_analyzer.parser.information_flow.constant_step_indexes import PRESTATE
from traces_analyzer.parser.information_flow.information_flow_graph import (
    build_information_flow_graph,
)
from traces_analyzer.parser.instructions.instructions import (
    CALL,
    POP,
    SLOAD,
    SSTORE,
    STOP,
)
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_persistent_storage_across_calls() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # store data in child context
        *_test_push_steps(
            reversed(
                ["0x1234", _test_hash_addr("target address"), "0", "0", "0", "0", "0"]
            ),
            step_index,
            "push_call",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(depth=2),
        ),
        *_test_push_steps(
            reversed(["0x20", "0xabcdef"]),
            step_index,
            "push_sstore",
            base_oracle=_test_oracle(depth=2),
        ),
        (
            InstructionMetadata(SSTORE.opcode, step_index.next("sstore")),
            _test_oracle(depth=2),
        ),
        (InstructionMetadata(STOP.opcode, step_index.next("stop")), _test_oracle()),
        # sload in root should use oracle
        *_test_push_steps(
            reversed(["0x20"]), step_index, "push_sload_root", _test_oracle()
        ),
        (
            InstructionMetadata(SLOAD.opcode, step_index.next("sload_root")),
            _test_oracle(stack=["0x12345678"]),
        ),
        (InstructionMetadata(POP.opcode, step_index.next("pop")), _test_oracle()),
        # sload in child should use previously stored value
        *_test_push_steps(
            reversed(
                ["0x1234", _test_hash_addr("target address"), "0", "0", "0", "0", "0"]
            ),
            step_index,
            "push_call2",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call2")),
            _test_oracle(depth=2),
        ),
        *_test_push_steps(
            reversed(["0x20"]), step_index, "push_sload_child", _test_oracle(depth=2)
        ),
        (
            InstructionMetadata(SLOAD.opcode, step_index.next("sload_child")),
            _test_oracle(stack=["0xabcdef"], depth=2),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop2")),
            _test_oracle(depth=2),
        ),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str | int]]] = [
        ("sload_root", {"push_sload_root_0", PRESTATE}),
        ("sload_child", {"push_sload_child_0", "push_sstore_0"}),
    ]

    for name, should_depend_on in expected_dependencies:
        edges = sorted(information_flow_graph.in_edges(step_index.lookup(name)))
        expected_edges = sorted(
            [
                (
                    step_index.lookup(dependency_name)
                    if isinstance(dependency_name, str)
                    else dependency_name,
                    step_index.lookup(name),
                )
                for dependency_name in should_depend_on
            ]
        )
        assert edges == expected_edges, (
            f"Instruction '{name}' should depend on '{should_depend_on}."
            f" Found {edges}, expected {expected_edges}'."
        )


def test_persistent_storage_is_dropped_on_revert() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # store data in child context
        *_test_push_steps(
            reversed(
                ["0x1234", _test_hash_addr("target address"), "0", "0", "0", "0", "0"]
            ),
            step_index,
            "push_call",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(depth=2),
        ),
        *_test_push_steps(
            reversed(["0x20", "0xabcdef"]),
            step_index,
            "push_sstore",
            base_oracle=_test_oracle(depth=2),
        ),
        (
            InstructionMetadata(SSTORE.opcode, step_index.next("sstore")),
            _test_oracle(depth=2),
        ),
        # exceptional halt as call depth changed unexpectedly back to 1; eg out of gas
        # and enter child context again
        *_test_push_steps(
            reversed(
                ["0x1234", _test_hash_addr("target address"), "0", "0", "0", "0", "0"]
            ),
            step_index,
            "push_call",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(depth=2),
        ),
        # sload should now use oracle
        *_test_push_steps(
            reversed(["0x20"]), step_index, "push_sload", _test_oracle(depth=2)
        ),
        (
            InstructionMetadata(SLOAD.opcode, step_index.next("sload")),
            _test_oracle(stack=["0x12345678"], depth=2),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop2")),
            _test_oracle(depth=2),
        ),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str | int]]] = [
        ("sload", {"push_sload_0", PRESTATE}),
    ]

    for name, should_depend_on in expected_dependencies:
        edges = sorted(information_flow_graph.in_edges(step_index.lookup(name)))
        expected_edges = sorted(
            [
                (
                    step_index.lookup(dependency_name)
                    if isinstance(dependency_name, str)
                    else dependency_name,
                    step_index.lookup(name),
                )
                for dependency_name in should_depend_on
            ]
        )
        assert edges == expected_edges, (
            f"Instruction '{name}' should depend on '{should_depend_on}."
            f" Found {edges}, expected {expected_edges}'."
        )
