from dataclasses import dataclass
from tests.test_utils.test_utils import (
    _test_group,
    _test_group32,
    _test_oracle,
    mock_env,
)
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_dsl import (
    combine,
    mem_range,
    mem_write,
    noop,
    oracle_stack_peek,
    return_data_range,
    return_data_size,
    return_data_write,
    stack_arg,
    stack_peek,
    stack_push,
    stack_set,
    to_size,
)
from traces_analyzer.parser.information_flow.information_flow_dsl_implementation import (
    FlowNode,
    FlowNodeWithResult,
    FlowWithResult,
)
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import ReturnDataAccess, StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString


class _TestFlowNode(FlowNodeWithResult):
    def __init__(self, value: StorageByteGroup) -> None:
        super().__init__(())
        self.value = value

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
        return _TestFlowNode(value=value)
    return _TestFlowNode(value=_test_group(value))


def test_noop():
    env = mock_env()

    flow = noop().compute(env, _test_oracle())

    assert flow.accesses == StorageAccesses()
    assert flow.writes == StorageWrites()


def test_combine():
    # TODO: test this
    env = mock_env()


def test_stack_arg():
    env = mock_env(stack_contents=[_test_group32("10", 1234)])

    flow = stack_arg(0).compute(env, _test_oracle())

    assert len(flow.accesses.stack) == 1
    assert flow.accesses.stack[0].index == 0
    assert flow.accesses.stack[0].value.get_hexstring() == "10".rjust(64, "0")
    assert flow.accesses.stack[0].value.depends_on_instruction_indexes() == {1234}

    assert len(flow.writes.stack_pops) == 1

    assert flow.result == flow.accesses.stack[0].value


def test_stack_peek():
    env = mock_env(stack_contents=[_test_group32("10", 1234)])

    flow = stack_peek(0).compute(env, _test_oracle())

    assert len(flow.accesses.stack) == 1
    assert flow.accesses.stack[0].index == 0
    assert flow.accesses.stack[0].value.get_hexstring() == "10".rjust(64, "0")
    assert flow.accesses.stack[0].value.depends_on_instruction_indexes() == {1234}

    assert len(flow.writes.stack_pops) == 0

    assert flow.result == flow.accesses.stack[0].value


def test_oracle_stack_peek():
    env = mock_env(step_index=1234)
    oracle = _test_oracle(stack=["10", "20"])

    flow = oracle_stack_peek(1).compute(env, oracle)

    assert flow.result.get_hexstring() == HexString("20").as_size(32)
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_mem_range_const():
    env = mock_env(memory_content=_test_group("00112233445566778899", 1234))

    flow = mem_range(2, 4).compute(env, _test_oracle())

    assert flow.result.get_hexstring() == "22334455"
    assert len(flow.accesses.memory) == 1
    assert flow.accesses.memory[0].offset == 2
    assert flow.accesses.memory[0].value == _test_group("22334455")
    assert flow.accesses.memory[0].value.depends_on_instruction_indexes() == {1234}


def test_mem_range_stack_args():
    env = mock_env(
        stack_contents=["2", "4"],
        memory_content=_test_group("00112233445566778899", 1234),
    )

    flow = mem_range(stack_arg(0), stack_arg(1)).compute(env, _test_oracle())

    assert flow.result.get_hexstring() == "22334455"
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_stack_push_const():
    env = mock_env(step_index=1234)

    flow = stack_push("123456").compute(env, _test_oracle())

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_pushes[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_push_node():
    env = mock_env()
    input = _test_node(_test_group("123456", 1234))

    flow = stack_push(input).compute(env, _test_oracle())

    assert len(flow.writes.stack_pushes) == 1
    assert flow.writes.stack_pushes[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_pushes[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_set_const():
    env = mock_env(step_index=1234)

    flow = stack_set(3, "123456").compute(env, _test_oracle())

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_sets[0].value.depends_on_instruction_indexes() == {1234}


def test_stack_set_node():
    env = mock_env()
    input = _test_node(_test_group("123456", 1234))

    flow = stack_set(_test_node("3"), input).compute(env, _test_oracle())

    assert len(flow.writes.stack_sets) == 1
    assert flow.writes.stack_sets[0].index == 3
    assert flow.writes.stack_sets[0].value.get_hexstring() == "123456"
    assert flow.writes.stack_sets[0].value.depends_on_instruction_indexes() == {1234}


def test_mem_write_const():
    env = mock_env(step_index=1234)

    flow = mem_write(2, "22334455").compute(env, _test_oracle())

    assert not flow.accesses.memory
    assert len(flow.writes.memory) == 1
    assert flow.writes.memory[0].offset == 2
    assert flow.writes.memory[0].value.get_hexstring() == "22334455"
    assert flow.writes.memory[0].value.depends_on_instruction_indexes() == {1234}


def test_to_size_noop():
    env = mock_env()
    input = _test_node(_test_group("11223344", 1234))

    flow = to_size(input, 4).compute(env, _test_oracle())

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1234}


def test_to_size_increase():
    env = mock_env(step_index=2)
    input = _test_node(_test_group("1122", 1))

    flow = to_size(input, 4).compute(env, _test_oracle())

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1, 2}


def test_to_size_decrease():
    env = mock_env(step_index=2)
    input = _test_node(_test_group("112233445566", 1))

    flow = to_size(input, 4).compute(env, _test_oracle())

    assert len(flow.result) == 4
    assert flow.result.depends_on_instruction_indexes() == {1}


def test_return_data_range_noop():
    env = mock_env()
    env.last_executed_sub_context.return_data = _test_group("1234", 1)

    flow = return_data_range(_test_node("2"), _test_node("0")).compute(env, _test_oracle())

    assert len(flow.result) == 0
    assert flow.accesses.return_data == None


def test_return_data_range_if_not_set():
    env = mock_env()
    env.last_executed_sub_context.return_data = _test_group("", 1234)

    flow = return_data_range(_test_node("2"), _test_node("4")).compute(env, _test_oracle())

    assert len(flow.result) == 0
    assert flow.accesses.return_data == ReturnDataAccess(2, 4, _test_group(""))
    assert len(flow.accesses.return_data.value.depends_on_instruction_indexes()) == 0


def test_return_data_range():
    env = mock_env()
    env.last_executed_sub_context.return_data = _test_group("11223344556677889900", 1234)

    flow = return_data_range(_test_node("2"), _test_node("4")).compute(env, _test_oracle())

    assert len(flow.result) == 4
    assert flow.result == _test_group("33445566")
    assert flow.accesses.return_data == ReturnDataAccess(2, 4, _test_group("33445566"))
    assert flow.accesses.return_data.value.depends_on_instruction_indexes() == {1234}


def test_return_data_write():
    env = mock_env()
    input = _test_node(_test_group("11223344", 1234))

    flow = return_data_write(input).compute(env, _test_oracle())

    assert flow.writes.return_data.value.get_hexstring() == "11223344"
    assert flow.writes.return_data.value.depends_on_instruction_indexes() == {1234}


def test_return_data_size():
    env = mock_env(step_index=1)
    env.last_executed_sub_context.return_data = _test_group("11" * 40, 1234)

    flow = return_data_size().compute(env, _test_oracle())

    assert flow.result.get_hexstring().as_int() == 40
    assert flow.accesses.return_data.offset == 0
    assert flow.accesses.return_data.size == 40
    assert flow.accesses.return_data.value.get_hexstring() == HexString("11" * 40)
    assert flow.accesses.return_data.value.depends_on_instruction_indexes() == {1234}
