from tests.test_utils.test_utils import (
    _TestCounter,
    _test_call_context,
    _test_hash_addr,
    _test_oracle,
    _test_push_steps,
    assert_flow_dependencies,
)
from traces_analyzer.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_analyzer.parser.information_flow.information_flow_graph import (
    build_information_flow_graph,
)
from traces_analyzer.parser.instructions.instructions import STATICCALL, SWAP2
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata, TraceEVM


def test_exceptional_halt_executes_instruction_in_correct_context():
    root = _test_call_context()
    env = ParsingEnvironment(root)
    evm = TraceEVM(env, verify_storages=True)
    step_index = _TestCounter(0)

    steps: list[tuple[InstructionMetadata, InstructionOutputOracle]] = [
        # some content in case it wrongly tries to execute the swap in the parent context
        *_test_push_steps(
            reversed(["0x1111", "0x2222", "0x3333"]), step_index, "push_unused"
        ),
        # make a call
        *_test_push_steps(
            reversed(
                [
                    "0x0",
                    _test_hash_addr("target address"),
                    "0x0",
                    "0x0",
                    "0x0",
                    "0x0",
                ]
            ),
            step_index,
            "push_staticcall",
            base_oracle=_test_oracle(stack=["0x1111", "0x2222", "0x3333"]),
        ),
        (
            InstructionMetadata(STATICCALL.opcode, step_index.next("staticcall")),
            _test_oracle(depth=2),
        ),
        # push some content
        *_test_push_steps(
            reversed(["0", "1", "2", "3", "4"]),
            step_index,
            "push_child_content",
            base_oracle=_test_oracle(depth=2),
        ),
        # exceptional halt with swap (should either not fully parse SWAP or still execute in child)
        (
            InstructionMetadata(SWAP2.opcode, step_index.next("swap2")),
            _test_oracle(stack=["0", "0x1111", "0x2222", "0x3333"]),
        ),
    ]

    instructions = [evm.step(instr, oracle) for instr, oracle in steps]
    information_flow_graph = build_information_flow_graph(instructions)

    assert_flow_dependencies(
        information_flow_graph,
        step_index,
        [("swap2", {"push_child_content_4", "push_child_content_2"})],
    )
