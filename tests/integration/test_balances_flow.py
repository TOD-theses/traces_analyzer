from tests.test_utils.test_utils import _TestCounter, _test_hash_addr, _test_oracle, _test_push_steps, _test_root
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.constant_step_indexes import PRESTATE
from traces_analyzer.parser.information_flow.information_flow_graph import build_information_flow_graph
from traces_analyzer.parser.instructions.instructions import BALANCE, CALL, POP, REVERT, SLOAD, SSTORE, STOP
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_balances_across_calls() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # send value to child contract
        *_test_push_steps(
            reversed(["0x0", _test_hash_addr("target address"), "0x1234", "0", "0", "0", "0"]), step_index, "push_call"
        ),
        (InstructionMetadata(CALL.opcode, step_index.next("call")), _test_oracle(depth=2)),
        (InstructionMetadata(STOP.opcode, step_index.next("stop")), _test_oracle()),
        # get balance of target address
        *_test_push_steps(reversed([_test_hash_addr("target address")]), step_index, "push_balance_known"),
        (InstructionMetadata(BALANCE.opcode, step_index.next("balance_known")), _test_oracle(stack=["0x1234"])),
        # get balance of random address
        *_test_push_steps(
            reversed([_test_hash_addr("some other address")]),
            step_index,
            "push_balance_other",
            base_oracle=_test_oracle(stack=["0x1234"]),
        ),
        (
            InstructionMetadata(BALANCE.opcode, step_index.next("balance_other")),
            _test_oracle(stack=["0x11223344", "0x1234"]),
        ),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str | int]]] = [
        ("balance_known", {"push_balance_known_0", "call"}),
        ("balance_other", {"push_balance_other_0", PRESTATE}),
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


def test_balances_restored_on_revert() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # successfully send value to child contract
        *_test_push_steps(
            reversed(["0x0", _test_hash_addr("target address"), "0x1234", "0", "0", "0", "0"]), step_index, "push_call"
        ),
        (InstructionMetadata(CALL.opcode, step_index.next("call")), _test_oracle(depth=2)),
        (InstructionMetadata(STOP.opcode, step_index.next("stop")), _test_oracle()),
        # send value, but revert
        *_test_push_steps(
            reversed(["0x0", _test_hash_addr("target address"), "0x1234", "0", "0", "0", "0"]),
            step_index,
            "push_call_reverted",
        ),
        (InstructionMetadata(CALL.opcode, step_index.next("call_reverted")), _test_oracle(depth=2)),
        # revert
        *_test_push_steps(reversed(["0x0", "0x0"]), step_index, "push_revert", base_oracle=_test_oracle(depth=2)),
        (InstructionMetadata(REVERT.opcode, step_index.next("revert")), _test_oracle()),
        # get balance of target address
        *_test_push_steps(reversed([_test_hash_addr("target address")]), step_index, "push_balance_known"),
        (InstructionMetadata(BALANCE.opcode, step_index.next("balance_known")), _test_oracle(stack=["0x1234"])),
    ]

    instructions = []
    for instruction_metadata, oracle in steps:
        instructions.append(evm.step(instruction_metadata, oracle))

    information_flow_graph = build_information_flow_graph(instructions)

    assert len(instructions) == len(steps)
    assert len(information_flow_graph) == len(steps) + 1

    expected_dependencies: list[tuple[str, set[str | int]]] = [
        # the balance depends on the first call, as the 2nd was reverted
        ("balance_known", {"push_balance_known_0", "call"}),
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
