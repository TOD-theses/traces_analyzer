from abc import abstractmethod
from dataclasses import dataclass

from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.storage import HexStringStorageValue, MemoryRange, StackIndex, StorageValue
from traces_analyzer.parser.storage.storage_writes import (
    MemoryAccess,
    MemoryWrite,
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
    result: StorageValue


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
        for access in accesses:
            memory_accesss.extend(access.memory)
            stack_accesses.extend(access.stack)

        return StorageAccesses(
            stack=stack_accesses,
            memory=memory_accesss,
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
            result=HexStringStorageValue(self.hexstring),
        )


@dataclass
class StackArgNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        index = args[0].result.get_hexstring().as_int()
        result = env.stack.get(StackIndex(index))

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
        # TODO: storage value conversion
        # TODO: remove 0x for all stack values everywhere and use common class
        hex_value = "0x" + args[0].result.get_hexstring()
        value = HexStringStorageValue(hex_value)
        return StorageWrites(stack_pushes=[StackPush(value)])


@dataclass
class StackSetNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        # TODO: storage value conversion
        # TODO: remove 0x for all stack values everywhere and use common class
        index = args[0].result.get_hexstring().as_int()
        hex_value = "0x" + args[1].result.get_hexstring()
        value = HexStringStorageValue(hex_value)
        return StorageWrites(
            stack_sets=[StackSet(index, value)],
        )


@dataclass
class MemRangeNode(FlowNodeWithResult):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_result(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> FlowWithResult:
        offset = args[0].result.get_hexstring().as_int()
        size = args[1].result.get_hexstring().as_int()
        result = env.memory.get(MemoryRange(offset, size))
        mem_access = MemoryAccess(offset, result)

        return FlowWithResult(
            accesses=StorageAccesses(memory=[mem_access]),
            writes=StorageWrites(),
            result=result,
        )


@dataclass
class MemWriteNode(WritingFlowNode):
    arguments: tuple[FlowNodeWithResult, FlowNodeWithResult]

    def _get_writes(
        self, args: tuple[FlowWithResult, ...], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> StorageWrites:
        offset = args[0].result.get_hexstring().as_int()
        # TODO: how should we convert the storage types?
        # Or should we unify it so we don't need conversion?
        value = HexStringStorageValue(args[1].result.get_hexstring())

        return StorageWrites(memory=(MemoryWrite(offset, value),))


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


def noop() -> FlowSpec:
    return NoopNode(arguments=())
