from tests.test_utils.test_utils import (
    _TestCounter,
    _test_addr,
    assert_flow_dependencies,
    _test_hash_addr,
    _test_oracle,
    _test_push_steps,
    _test_root,
)
from traces_analyzer.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_analyzer.parser.information_flow.information_flow_graph import (
    build_information_flow_graph,
)
from traces_analyzer.parser.instructions.instructions import (
    CALL,
    CALLDATACOPY,
    CALLVALUE,
    LOG0,
    MSIZE,
    MSTORE,
    MSTORE8,
    POP,
    RETURN,
    RETURNDATASIZE,
)
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_call_data_and_return_data_flow() -> None:
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
        (
            InstructionMetadata(MSTORE.opcode, step_index.next("mstore")),
            _test_oracle(memory=initial_root_memory),
        ),
        # call with abcdef as calldata and value 0x1234
        # writes 16 bytes from the call return data to 0x0
        *_test_push_steps(
            reversed(
                [
                    "0x0",
                    _test_hash_addr("target address"),
                    "0x1234",
                    hex(0x20 + 29),
                    "3",
                    "0x0",
                    "0x10",
                ]
            ),
            step_index,
            "push_call",
            base_oracle=_test_oracle(memory=initial_root_memory),
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(depth=2),
        ),
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
            base_oracle=_test_oracle(
                depth=2, stack=["0x1234"], memory=calldata_child_memory
            ),
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
        (
            InstructionMetadata(POP.opcode, step_index.next("pop")),
            _test_oracle(memory=post_call_memory),
        ),
        # log the returned data
        *_test_push_steps(
            reversed(["0x0", "0x10"]),
            step_index,
            "push_log0",
            base_oracle=_test_oracle(memory=post_call_memory),
        ),
        (
            InstructionMetadata(LOG0.opcode, step_index.next("log0")),
            _test_oracle(memory=post_call_memory),
        ),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [
            ("pop", {"call"}),
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
        ],
    )


def test_call_to_eoa() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # call with value 0x1234
        *_test_push_steps(
            reversed(
                [
                    "0x10",
                    _test_hash_addr("target address"),
                    "0x1234",
                    "0x0",
                    "0x0",
                    "0x0",
                    "0x0",
                ]
            ),
            step_index,
            "push_call",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(stack=["0x1"]),
        ),
        (InstructionMetadata(POP.opcode, step_index.next("pop")), _test_oracle()),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [
            (
                "pop",
                {"call"},
            ),
        ],
    )


def test_call_to_precompiled_contract() -> None:
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    initial_memory = "00" * 29 + "abcdef"
    post_memory = "abcdef" + "00" * 26 + "abcdef"

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # store abcdef in memory
        *_test_push_steps(reversed(["0x0", "0xabcdef"]), step_index, "push_mstore"),
        (
            InstructionMetadata(MSTORE.opcode, step_index.next("mstore")),
            _test_oracle(memory=initial_memory),
        ),
        # call 0x4 (identity precompiled contract)
        *_test_push_steps(
            reversed(
                [
                    "0x10",
                    _test_addr("0x4"),
                    "0x0",
                    hex(32 - 3),  # offset
                    "0x3",  # size
                    "0x0",  # return offset
                    "0x3",  # return size
                ]
            ),
            step_index,
            "push_call",
            base_oracle=_test_oracle(memory=initial_memory),
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(stack=["0x1"], memory=post_memory),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop")),
            _test_oracle(memory=post_memory),
        ),
        (
            InstructionMetadata(MSIZE.opcode, step_index.next("msize")),
            _test_oracle(stack=["0x20"], memory=post_memory),
        ),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [
            ("pop", {"call"}),
            # the push, as the value from mstore is still in memory.
            # the call, as it returned new data (not 100% accurate if we would model it as a real identity)
            ("msize", {"push_mstore_0", "call"}),
        ],
    )


def test_call_to_eoa_sets_returndata() -> None:
    """Check that returndata depends on the last call, even if it did not execute any code"""
    root = _test_root()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # call that enters contract and executes code there
        *_test_push_steps(
            reversed(
                [
                    "0x10",
                    _test_hash_addr("target address"),
                    "0x1234",
                    "0x0",
                    "0x0",
                    "0x0",  # return offset
                    "0x20",  # return size
                ]
            ),
            step_index,
            "push_call",
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call")),
            _test_oracle(depth=2),
        ),
        *_test_push_steps(
            reversed(["0x0", "aa" * 32]),
            step_index,
            "push_mstore",
            base_oracle=_test_oracle(depth=2),
        ),
        (
            InstructionMetadata(MSTORE.opcode, step_index.next("mstore")),
            _test_oracle(depth=2, memory="aa" * 32),
        ),
        *_test_push_steps(
            reversed(["0x0", "0x20"]),
            step_index,
            "push_return",
            base_oracle=_test_oracle(depth=2, memory="aa" * 32),
        ),
        (
            InstructionMetadata(RETURN.opcode, step_index.next("return")),
            _test_oracle(depth=1, stack=["0x1"], memory="aa" * 32),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop")),
            _test_oracle(memory="aa" * 32),
        ),
        # returndatasize for the first call
        (
            InstructionMetadata(
                RETURNDATASIZE.opcode, step_index.next("returndatasize")
            ),
            _test_oracle(stack=["0x20"], memory="aa" * 32),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop_size")),
            _test_oracle(memory="aa" * 32),
        ),
        # call to EOA
        *_test_push_steps(
            reversed(
                [
                    "0x10",
                    _test_hash_addr("other target address"),
                    "0x1234",
                    "0x0",
                    "0x0",
                    "0x0",
                    "0x0",
                ]
            ),
            step_index,
            "push_call_eoa",
            base_oracle=_test_oracle(memory="aa" * 32),
        ),
        (
            InstructionMetadata(CALL.opcode, step_index.next("call_eoa")),
            _test_oracle(stack=["0x1"], memory="aa" * 32),
        ),
        (
            InstructionMetadata(POP.opcode, step_index.next("pop_eoa")),
            _test_oracle(memory="aa" * 32),
        ),
        # returndatasize for the eoa call
        (
            InstructionMetadata(
                RETURNDATASIZE.opcode, step_index.next("returndatasize_eoa")
            ),
            _test_oracle(stack=["0x0"], memory="aa" * 32),
        ),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [
            ("pop", {"call"}),
            ("returndatasize", {"push_mstore_0"}),
        ],
    )
