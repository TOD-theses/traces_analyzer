from dataclasses import dataclass
from typing import Any
from tests.conftest import TEST_ROOT_CALLCONTEXT
from tests.test_utils.test_utils import _test_group, _test_group32
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_dsl import (
    FlowNode,
    FlowNodeWithResult,
    FlowWithResult,
    mem_range,
    mem_write,
    noop,
    return_data_range,
    return_data_size,
    return_data_write,
    stack_arg,
    stack_push,
    stack_set,
    to_size,
)
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import ReturnDataAccess, ReturnWrite, StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString

dummy_output_oracle = InstructionOutputOracle([], HexString(""), None)


@dataclass
class _TestFlowNode(FlowNodeWithResult):
    value: StorageByteGroup

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return FlowWithResult(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
            result=self.value,
        )


def _test_node(value: StorageByteGroup | str) -> FlowNode:
    if isinstance(value, StorageByteGroup):
        return _TestFlowNode(arguments=(), value=value)
    return _TestFlowNode(arguments=(), value=_test_group(value))


def test_noop():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)

    flow = noop().compute(env, dummy_output_oracle)

    assert flow.accesses == StorageAccesses()
    assert flow.writes == StorageWrites()


def test_stack_arg_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_group32("10", 1234))

    flow = stack_arg(0).compute(env, dummy_output_oracle)

    assert len(flow.accesses.stack) == 1
    assert flow.accesses.stack[0].index == 0
    assert flow.accesses.stack[0].value.get_hexstring() == "10".rjust(64, "0")
    assert flow.accesses.stack[0].value.depends_on_instruction_indexes() == {1234}

    assert len(flow.writes.stack_pops) == 1

    assert flow.result == flow.accesses.stack[0].value


def test_stack_arg_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_group32("10", 1234))

    flow = stack_arg(_test_node("00")).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == HexString("10").as_size(32)
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_mem_range_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.memory.set(0, _test_group("00112233445566778899", 1234), -1)

    flow = mem_range(2, 4).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == "22334455"
    assert len(flow.accesses.memory) == 1
    assert flow.accesses.memory[0].offset == 2
    assert flow.accesses.memory[0].value == _test_group("22334455")
    assert flow.accesses.memory[0].value.depends_on_instruction_indexes() == {1234}


def test_mem_range_stack_args():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_group("4"))
    env.stack.push(_test_group("2"))
    env.memory.set(0, _test_group("00112233445566778899", 1234), -1)

    flow = mem_range(stack_arg(0), stack_arg(1)).compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring() == "22334455"
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_stack_push_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = 1234

    flow = stack_push("123456").compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_pushes[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_push_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    input = _test_node(_test_group("123456", 1234))

    flow = stack_push(input).compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_pushes[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_set_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = 1234

    flow = stack_set(3, "123456").compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_sets[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_set_node():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    input = _test_node(_test_group("123456", 1234))

    flow = stack_set(_test_node("3"), input).compute(env, dummy_output_oracle)

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_sets[0].value.depends_on_instruction_indexes() == {1234}


def test_mem_write_const():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = 1234

    flow = mem_write(2, "22334455").compute(env, dummy_output_oracle)

    assert not flow.accesses.memory
    assert len(flow.writes.memory) == 1
    assert flow.writes.memory[0].offset == 2
    assert flow.writes.memory[0].value.get_hexstring() == "22334455"
    assert flow.writes.memory[0].value.depends_on_instruction_indexes() == {1234}


def test_to_size_noop():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    input = _test_node(_test_group("11223344", 1234))

    flow = to_size(input, 4).compute(env, dummy_output_oracle)

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_to_size_increase():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = 2
    input = _test_node(_test_group("1122", 1))

    flow = to_size(input, 4).compute(env, dummy_output_oracle)

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1, 2}


def test_to_size_decrease():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = 2
    input = _test_node(_test_group("112233445566", 1))

    flow = to_size(input, 4).compute(env, dummy_output_oracle)

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1}


def test_return_data_range_noop():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_call_context.return_data = _test_group("1234", 1)

    flow = return_data_range(_test_node("2"), _test_node("0")).compute(env, dummy_output_oracle)

    assert len(flow.result) == 0
    assert flow.accesses.return_data == None


def test_return_data_range_if_not_set():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_call_context.return_data = _test_group("")

    flow = return_data_range(_test_node("2"), _test_node("4")).compute(env, dummy_output_oracle)

    assert len(flow.result) == 0
    assert flow.accesses.return_data == ReturnDataAccess(2, 4, _test_group(""))
    assert len(flow.accesses.return_data.value.depends_on_instruction_indexes()) == 0


def test_return_data_range():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_call_context.return_data = _test_group("11223344556677889900", 1234)

    flow = return_data_range(_test_node("2"), _test_node("4")).compute(env, dummy_output_oracle)

    assert len(flow.result) == 4
    assert flow.result == _test_group("33445566")
    assert flow.accesses.return_data == ReturnDataAccess(2, 4, _test_group("33445566"))
    assert flow.accesses.return_data.value.depends_on_instruction_indexes() == {1234}


def test_return_data_write():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    input = _test_node(_test_group("11223344", 1234))

    flow = return_data_write(input).compute(env, dummy_output_oracle)

    assert flow.writes.return_data.value.get_hexstring() == "11223344"
    assert flow.writes.return_data.value.depends_on_instruction_indexes() == {1234}


def test_return_data_size():
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_call_context.return_data = _test_group("11" * 40, 1234)

    flow = return_data_size().compute(env, dummy_output_oracle)

    assert flow.result.get_hexstring().as_int() == 40
    assert flow.accesses.return_data.offset == 0
    assert flow.accesses.return_data.size == 40
    assert flow.accesses.return_data.value.get_hexstring() == HexString("11" * 40)
    assert flow.accesses.return_data.value.depends_on_instruction_indexes() == {1234}
