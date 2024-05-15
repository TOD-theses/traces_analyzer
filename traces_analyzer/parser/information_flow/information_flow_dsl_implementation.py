from abc import abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Callable

from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_spec import Flow, FlowSpec
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import (
    BalanceAccess,
    BalanceTransferWrite,
    CalldataAccess,
    CalldataWrite,
    CallvalueAccess,
    MemoryAccess,
    MemoryWrite,
    ReturnDataAccess,
    ReturnWrite,
    SelfdestructWrite,
    StackAccess,
    StackPop,
    StackPush,
    StackSet,
    StorageAccesses,
    StorageWrites,
    TransientStorageAccess,
    TransientStorageWrite,
)
from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True)
class FlowWithResult(Flow):
    result: StorageByteGroup


class NoopNode(FlowSpec):
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        return Flow(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
        )


class FlowNode(FlowSpec):
    def __init__(self, arguments: tuple["FlowNodeWithResult", ...]) -> None:
        super().__init__()
        self.arguments = arguments

    @abstractmethod
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        pass


class FlowNodeWithResult(FlowNode):
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> FlowWithResult:
        args = tuple(arg.compute(env, output_oracle) for arg in self.arguments)

        flow_step = self._get_result(args, env, output_oracle)

        accesses = [arg.accesses for arg in args] + [flow_step.accesses]
        writes = [arg.writes for arg in args] + [flow_step.writes]

        return FlowWithResult(
            accesses=StorageAccesses.merge(accesses),
            writes=StorageWrites.merge(writes),
            result=flow_step.result,
        )

    @abstractmethod
    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        pass


class WritingFlowNode(FlowNode):
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        args = tuple(arg.compute(env, output_oracle) for arg in self.arguments)

        flow_writes = self._get_writes(args, env, output_oracle)

        accesses = [arg.accesses for arg in args]
        writes = [arg.writes for arg in args] + [flow_writes]

        return Flow(
            accesses=StorageAccesses.merge(accesses),
            writes=StorageWrites.merge(writes),
        )

    @abstractmethod
    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        pass


class ConstNode(FlowNodeWithResult):
    def __init__(self, hexstring: HexString) -> None:
        super().__init__(())
        self.hexstring = hexstring

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return FlowWithResult(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
            result=StorageByteGroup.from_hexstring(self.hexstring, env.current_step_index),
        )


class CombineNode(FlowSpec):
    def __init__(self, arguments: tuple[FlowNode, ...]) -> None:
        super().__init__()
        self.arguments = arguments

    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        args = tuple(arg.compute(env, output_oracle) for arg in self.arguments)

        return Flow(
            accesses=StorageAccesses.merge([arg.accesses for arg in args]),
            writes=StorageWrites.merge([arg.writes for arg in args]),
        )


class CallbackNodeWithResult(FlowNodeWithResult):
    def __init__(
        self,
        arguments: tuple[FlowNodeWithResult, ...],
        callback: Callable[[tuple[FlowWithResult, ...], ParsingEnvironment, InstructionOutputOracle], FlowWithResult],
    ) -> None:
        super().__init__(arguments)
        self.callback = callback

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return self.callback(args, env, output_oracle)


def node_with_results(
    callback: Callable[[tuple[FlowWithResult, ...], ParsingEnvironment, InstructionOutputOracle], FlowWithResult]
):
    @wraps(callback)
    def factory(*arguments: FlowNodeWithResult | str | int):
        node_arguments = tuple(as_node(arg) for arg in arguments)
        return CallbackNodeWithResult(node_arguments, callback)

    return factory


class CallbackNodeWithWrites(WritingFlowNode):
    def __init__(
        self,
        arguments: tuple[FlowNodeWithResult, ...],
        callback: Callable[[tuple[FlowWithResult, ...], ParsingEnvironment, InstructionOutputOracle], StorageWrites],
    ) -> None:
        super().__init__(arguments)
        self.callback = callback

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        return self.callback(args, env, output_oracle)


def node_with_writes(
    callback: Callable[[tuple[FlowWithResult, ...], ParsingEnvironment, InstructionOutputOracle], StorageWrites]
):
    @wraps(callback)
    def factory(*arguments: FlowNodeWithResult | str | int):
        node_arguments = tuple(as_node(arg) for arg in arguments)
        return CallbackNodeWithWrites(node_arguments, callback)

    return factory


def as_node(node_or_value: FlowNodeWithResult | int | str) -> FlowNodeWithResult:
    if isinstance(node_or_value, FlowNodeWithResult):
        return node_or_value
    if isinstance(node_or_value, int):
        return ConstNode(HexString.from_int(node_or_value))
    return ConstNode(HexString(node_or_value))


@node_with_results
def _stack_arg_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    index = args[0].result.get_hexstring().as_int()
    result = env.stack.peek(index)

    return FlowWithResult(
        accesses=StorageAccesses(
            stack=[StackAccess(index, result)],
        ),
        writes=StorageWrites(stack_pops=[StackPop()]),
        result=result,
    )


@node_with_results
def _stack_peek_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    index = args[0].result.get_hexstring().as_int()
    result = env.stack.peek(index)

    return FlowWithResult(
        accesses=StorageAccesses(
            stack=[StackAccess(index, result)],
        ),
        writes=StorageWrites(),
        result=result,
    )


@node_with_writes
def _stack_push_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    return StorageWrites(stack_pushes=[StackPush(args[0].result)])


@node_with_writes
def _stack_set_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    index = args[0].result.get_hexstring().as_int()
    return StorageWrites(
        stack_sets=[StackSet(index, args[1].result)],
    )


@node_with_results
def _oracle_stack_peek_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    index = args[0].result.get_hexstring().as_int()
    value = output_oracle.stack[index]
    if not len(value) == 64:
        value = value.as_size(32)
    result = StorageByteGroup.from_hexstring(value, env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(),
        writes=StorageWrites(),
        result=result,
    )


@node_with_results
def _oracle_mem_range_peek_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    offset = args[0].result.get_hexstring().as_int()
    size = args[1].result.get_hexstring().as_int()
    data = output_oracle.memory[offset * 2 : offset * 2 + size * 2]
    result = StorageByteGroup.from_hexstring(data, env.current_step_index)
    if len(result) < size:
        padding = HexString("00" * (size - len(result)))
        result += StorageByteGroup.from_hexstring(padding, env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(),
        writes=StorageWrites(),
        result=result,
    )


@node_with_results
def _mem_range_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    offset = args[0].result.get_hexstring().as_int()
    size = args[1].result.get_hexstring().as_int()
    result = env.memory.get(offset, size, env.current_step_index)
    mem_access = MemoryAccess(offset, result)

    return FlowWithResult(
        accesses=StorageAccesses(memory=[mem_access]),
        writes=StorageWrites(),
        result=result,
    )


@node_with_results
def _mem_size_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    size = env.memory.size()
    result = StorageByteGroup.from_hexstring(HexString.from_int(size).as_size(32), env.current_step_index)

    # it depends on the last 32 bytes, which are essential for the memory size
    if size == 0:
        offset = 0
        value = StorageByteGroup()
    else:
        offset = size - 32
        value = env.memory.get(offset, 32, -1)

    mem_access = MemoryAccess(offset, value)

    return FlowWithResult(
        accesses=StorageAccesses(memory=[mem_access]),
        writes=StorageWrites(),
        result=result,
    )


@node_with_writes
def _mem_write_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> StorageWrites:
    offset = args[0].result.get_hexstring().as_int()
    return StorageWrites(memory=(MemoryWrite(offset, args[1].result),))


@node_with_results
def _to_size_node(args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
    value = args[0].result
    size = args[1].result.get_hexstring().as_int()
    if len(value) > size:
        value = value[-size:]
    elif len(value) < size:
        missing_bytes = size - len(value)
        padding = StorageByteGroup.from_hexstring(HexString("00" * missing_bytes), env.current_step_index)
        value = padding + value

    return FlowWithResult(
        accesses=StorageAccesses(),
        writes=StorageWrites(),
        result=value,
    )


@node_with_results
def _transient_storage_get_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    key = args[0].result
    address = env.current_call_context.storage_address
    result = env.transient_storage.get(address, key.get_hexstring())

    return FlowWithResult(
        accesses=StorageAccesses(transient_storage=(TransientStorageAccess(address, key, result),)),
        writes=StorageWrites(),
        result=result,
    )


@node_with_writes
def _transient_storage_set_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    key = args[0].result
    value = args[1].result
    address = env.current_call_context.storage_address
    env.transient_storage.set(address, key.get_hexstring(), value)

    return StorageWrites(transient_storage=(TransientStorageWrite(address, key, value),))


@node_with_results
def _current_storage_address_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    address = StorageByteGroup.from_hexstring(env.current_call_context.storage_address, env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(),
        writes=StorageWrites(),
        result=address,
    )


@node_with_results
def _balance_of_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    addr = args[0].result[-20:]
    last_modified_at_step_index = env.balances.last_modified_at_step_index(addr.get_hexstring())

    return FlowWithResult(
        accesses=StorageAccesses(balance=(BalanceAccess(addr, last_modified_at_step_index),)),
        writes=StorageWrites(),
        result=StorageByteGroup(),
    )


@node_with_results
def _balance_transfer_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    from_addr = args[0].result[-20:]
    to_addr = args[1].result[-20:]
    value = args[2].result
    from_addr_last_modified = env.balances.last_modified_at_step_index(from_addr.get_hexstring())

    env.balances.modified_at_step_index(to_addr.get_hexstring(), env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(balance=(BalanceAccess(from_addr, from_addr_last_modified),)),
        writes=StorageWrites(balance_transfers=(BalanceTransferWrite(from_addr, to_addr, value),)),
        result=StorageByteGroup(),
    )


@node_with_results
def _selfdestruct_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    from_addr = args[0].result[-20:]
    to_addr = args[1].result[-20:]
    from_addr_last_modified = env.balances.last_modified_at_step_index(from_addr.get_hexstring())

    env.balances.modified_at_step_index(to_addr.get_hexstring(), env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(balance=(BalanceAccess(from_addr, from_addr_last_modified),)),
        writes=StorageWrites(selfdestruct=(SelfdestructWrite(from_addr, to_addr),)),
        result=StorageByteGroup(),
    )


@node_with_results
def _return_data_range_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    offset = args[0].result.get_hexstring().as_int()
    size = args[1].result.get_hexstring().as_int()
    if size == 0:
        return FlowWithResult(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
            result=StorageByteGroup(),
        )
    if not env.last_executed_sub_context:
        return_data = StorageByteGroup()
    else:
        return_data = env.last_executed_sub_context.return_data
    if len(return_data) < offset + size:
        # should revert
        result = StorageByteGroup()
    else:
        result = return_data[offset : offset + size]

    return FlowWithResult(
        accesses=StorageAccesses(return_data=ReturnDataAccess(offset, size, result)),
        writes=StorageWrites(),
        result=result,
    )


@node_with_results
def _calldata_range_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    offset = args[0].result.get_hexstring().as_int()
    size = args[1].result.get_hexstring().as_int()
    result = env.current_call_context.calldata[offset : offset + size]
    if len(result) < size:
        missing_hexstring = HexString("00" * (size - len(result)))
        result += StorageByteGroup.from_hexstring(missing_hexstring, env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(calldata=(CalldataAccess(offset, result),)),
        writes=StorageWrites(),
        result=result,
    )


@node_with_results
def _calldata_size_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
):
    calldata = env.current_call_context.calldata
    size = HexString.from_int(len(calldata)).as_size(32)
    result = StorageByteGroup.from_hexstring(size, env.current_step_index)

    return FlowWithResult(
        accesses=StorageAccesses(calldata=(CalldataAccess(0, calldata),)),
        writes=StorageWrites(),
        result=result,
    )


@node_with_writes
def _calldata_write_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> StorageWrites:
    return StorageWrites(
        calldata=CalldataWrite(args[0].result),
    )


@node_with_results
def _callvalue_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    value = env.current_call_context.value

    return FlowWithResult(
        accesses=StorageAccesses(callvalue=(CallvalueAccess(value),)),
        writes=StorageWrites(),
        result=value,
    )


@node_with_writes
def _return_data_write_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> StorageWrites:
    return StorageWrites(
        return_data=ReturnWrite(args[0].result),
    )


@node_with_results
def _return_data_size_node(
    args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> FlowWithResult:
    if not env.last_executed_sub_context:
        # Return 0 if called without a sub context (and thus no return data is available)
        return_data = StorageByteGroup.from_hexstring(HexString("0").as_size(32), env.current_step_index)
        size = 0
    else:
        return_data = env.last_executed_sub_context.return_data
        size = len(return_data)

    return FlowWithResult(
        accesses=StorageAccesses(return_data=ReturnDataAccess(0, size, return_data)),
        writes=StorageWrites(),
        result=StorageByteGroup.from_hexstring(HexString.from_int(size).as_size(32), env.current_step_index),
    )
