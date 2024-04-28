from abc import abstractmethod
from dataclasses import dataclass

from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import (
    MemoryAccess,
    MemoryWrite,
    ReturnDataAccess,
    ReturnWrite,
    StackAccess,
    StackPop,
    StackPush,
    StackSet,
    StorageAccesses,
    StorageWrites,
)
from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True)
class Flow:
    accesses: StorageAccesses
    writes: StorageWrites


@dataclass(frozen=True)
class FlowWithResult(Flow):
    result: StorageByteGroup


@dataclass
class FlowSpec:
    @abstractmethod
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        """Compute the output of an information flow for a specific environment"""
        pass


@dataclass
class NoopNode(FlowSpec):
    arguments: tuple[()]

    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        return Flow(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
        )


@dataclass
class FlowNode(FlowSpec):
    arguments: tuple["FlowNodeWithResult", ...]

    @abstractmethod
    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        pass

    @staticmethod
    def _merge_accesses(accesses: list[StorageAccesses]) -> StorageAccesses:
        memory_accesss: list[MemoryAccess] = []
        stack_accesses: list[StackAccess] = []
        return_data_access: ReturnDataAccess | None = None
        for access in accesses:
            memory_accesss.extend(access.memory)
            stack_accesses.extend(access.stack)
            return_data_access = return_data_access or access.return_data

        return StorageAccesses(
            stack=stack_accesses,
            memory=memory_accesss,
            return_data=return_data_access,
        )

    @staticmethod
    def _merge_writes(writes: list[StorageWrites]) -> StorageWrites:
        mem_writes: list[MemoryWrite] = []
        return_data_write: ReturnWrite | None = None
        stack_sets: list[StackSet] = []
        stack_pops: list[StackPop] = []
        stack_pushes: list[StackPush] = []

        for write in writes:
            stack_sets.extend(write.stack_sets)
            stack_pops.extend(write.stack_pops)
            stack_pushes.extend(write.stack_pushes)
            mem_writes.extend(write.memory)
            return_data_write = return_data_write or write.return_data

        return StorageWrites(
            stack_sets=stack_sets,
            stack_pops=stack_pops,
            stack_pushes=stack_pushes,
            memory=mem_writes,
            return_data=return_data_write,
        )


@dataclass
class FlowNodeWithResult(FlowNode):

    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> FlowWithResult:
        args = tuple(arg.compute(env, output_oracle) for arg in self.arguments)

        flow_step = self._get_result(args, env, output_oracle)

        accesses = [arg.accesses for arg in args] + [flow_step.accesses]
        writes = [arg.writes for arg in args] + [flow_step.writes]

        return FlowWithResult(
            accesses=self._merge_accesses(accesses),
            writes=self._merge_writes(writes),
            result=flow_step.result,
        )

    @abstractmethod
    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        pass


@dataclass
class WritingFlowNode(FlowNode):

    def compute(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> Flow:
        args = tuple(arg.compute(env, output_oracle) for arg in self.arguments)

        flow_writes = self._get_writes(args, env, output_oracle)

        accesses = [arg.accesses for arg in args]
        writes = [arg.writes for arg in args] + [flow_writes]

        return Flow(
            accesses=self._merge_accesses(accesses),
            writes=self._merge_writes(writes),
        )

    @abstractmethod
    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        pass


@dataclass
class ConstNode(FlowNodeWithResult):
    hexstring: HexString

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return FlowWithResult(
            accesses=StorageAccesses(),
            writes=StorageWrites(),
            result=StorageByteGroup.from_hexstring(self.hexstring, env.current_step_index),
        )


@dataclass
class StackArgNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        index = args[0].result.get_hexstring().as_int()
        result = env.stack.peek(index)

        return FlowWithResult(
            accesses=StorageAccesses(
                stack=[StackAccess(index, result)],
            ),
            writes=StorageWrites(stack_pops=[StackPop()]),
            result=result,
        )


@dataclass
class StackPushNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        return StorageWrites(stack_pushes=[StackPush(args[0].result)])


@dataclass
class StackSetNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        index = args[0].result.get_hexstring().as_int()
        return StorageWrites(
            stack_sets=[StackSet(index, args[1].result)],
        )


@dataclass
class MemRangeNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        offset = args[0].result.get_hexstring().as_int()
        size = args[1].result.get_hexstring().as_int()
        result = env.memory.get(offset, size, env.current_step_index)
        mem_access = MemoryAccess(offset, result)

        return FlowWithResult(
            accesses=StorageAccesses(memory=[mem_access]),
            writes=StorageWrites(),
            result=result,
        )


@dataclass
class SizeNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
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


@dataclass
class ReturnDataRangeNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        offset = args[0].result.get_hexstring().as_int()
        size = args[1].result.get_hexstring().as_int()
        if size == 0:
            return FlowWithResult(
                accesses=StorageAccesses(),
                writes=StorageWrites(),
                result=StorageByteGroup(),
            )
        return_data = env.current_call_context.return_data
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


@dataclass
class ReturnDataSizeNode(FlowNodeWithResult):
    arguments: tuple[()]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        return_data = env.current_call_context.return_data
        size = len(return_data)

        return FlowWithResult(
            accesses=StorageAccesses(return_data=ReturnDataAccess(0, size, return_data)),
            writes=StorageWrites(),
            result=StorageByteGroup.from_hexstring(HexString(hex(size)).as_size(32), env.current_step_index),
        )


@dataclass
class ReturnDataWriteNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        return StorageWrites(
            return_data=ReturnWrite(args[0].result),
        )


@dataclass
class MemWriteNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        offset = args[0].result.get_hexstring().as_int()
        return StorageWrites(memory=(MemoryWrite(offset, args[1].result),))


def as_node(node_or_value: FlowNodeWithResult | int | str) -> FlowNodeWithResult:
    if isinstance(node_or_value, FlowNodeWithResult):
        return node_or_value
    if isinstance(node_or_value, int):
        return ConstNode(arguments=(), hexstring=HexString.from_int(node_or_value))
    return ConstNode(arguments=(), hexstring=HexString(node_or_value))


def stack_arg(index: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return StackArgNode(arguments=(as_node(index),))


def stack_push(value: FlowNodeWithResult | str) -> WritingFlowNode:
    return StackPushNode(arguments=(as_node(value),))


def stack_set(index: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return StackSetNode(arguments=(as_node(index), as_node(value)))


def mem_range(offset: FlowNodeWithResult | int, size: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return MemRangeNode(arguments=(as_node(offset), as_node(size)))


def mem_write(offset: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return MemWriteNode(arguments=(as_node(offset), as_node(value)))


def to_size(value: FlowNodeWithResult, bytes_size: int) -> FlowNodeWithResult:
    return SizeNode(arguments=(value, as_node(bytes_size)))


def return_data_range(offset: FlowNodeWithResult, size: FlowNodeWithResult) -> FlowNodeWithResult:
    return ReturnDataRangeNode(arguments=(offset, size))


def return_data_write(value: FlowNodeWithResult) -> WritingFlowNode:
    return ReturnDataWriteNode(arguments=(value,))


def return_data_size() -> FlowNodeWithResult:
    return ReturnDataSizeNode(arguments=())


def noop() -> FlowSpec:
    return NoopNode(arguments=())
