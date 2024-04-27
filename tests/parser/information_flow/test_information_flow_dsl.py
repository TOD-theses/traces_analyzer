from dataclasses import dataclass
from typing import Any
from tests.conftest import TEST_ROOT_CALLCONTEXT
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_dsl import (
    FlowNode,
    FlowNodeWithResult,
    FlowWithResult,
    mem_range,
    mem_write,
    noop,
    stack_arg,
    stack_push,
    stack_set,
)
from traces_analyzer.parser.storage.storage import HexStringStorageValue, HexStringStorageValue, StorageValue
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString

dummy_output_oracle = InstructionOutputOracle([], HexString(""), None)


@dataclass
class TestFlowNode(FlowNodeWithResult):
    value: StorageValue

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return FlowWithResult(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
            result=self.value,
        )


def _test_value(value: str) -> HexStringStorageValue:
    return HexStringStorageValue(HexString(value))


def _test_node(value: StorageValue | str) -> FlowNode:
    if isinstance(value, StorageValue):
        return TestFlowNode(arguments=(), value=value)
    return TestFlowNode(arguments=(), value=_test_value(value))


def test_noop():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = noop().compute(env, dummy_output_oracle)

    assert flow.accesses == StorageAccesses()
    assert flow.writes == StorageWrites()


def test_stack_arg_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_value("10"))

    flow = stack_arg(0).compute(env, dummy_output_oracle)

    assert len(flow.accesses.stack) == 1
    assert flow.accesses.stack[0].index == 0
    assert flow.accesses.stack[0].value.get_hexstring() == "10".rjust(64, "0")

    assert len(flow.writes.stack_pops) == 1


def test_stack_arg_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_value("10"))

    flow = stack_arg(_test_node("00")).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == HexString("10").as_size(32)


def test_mem_range_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.memory.set(0, _test_value("00112233445566778899"))

    flow = mem_range(2, 4).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == "22334455"
    assert len(flow.accesses.memory) == 1
    assert flow.accesses.memory[0].offset == 2
    assert flow.accesses.memory[0].value == _test_value("22334455")


def test_mem_range_stack_args():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_value("4"))
    env.stack.push(_test_value("2"))
    env.memory.set(0, _test_value("00112233445566778899"))

    flow = mem_range(stack_arg(0), stack_arg(1)).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == "22334455"


def test_stack_push_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = stack_push("1234").compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "1234"


def test_stack_push_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = stack_push(_test_node("1234")).compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "1234"


def test_stack_set_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = stack_set(3, "1234").compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "1234"


def test_stack_set_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = stack_set(_test_node("3"), _test_node("1234")).compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "1234"


def test_mem_write_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = mem_write(2, "22334455").compute(env, dummy_output_oracle)

    assert not flow.accesses.memory
    assert len(flow.writes.memory) == 1
    assert flow.writes.memory[0].offset == 2
    assert flow.writes.memory[0].value.get_hexstring() == "22334455"
