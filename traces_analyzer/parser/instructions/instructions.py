from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from typing import Mapping, TypedDict

from typing_extensions import override

from traces_analyzer.parser.environment.call_context import CallContext
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
    stack_push,
    to_size,
)
from traces_analyzer.parser.information_flow.information_flow_spec import FlowSpec
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instruction_io import InstructionIO, InstructionIOSpec
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import MemoryWrite, StorageWrites
from traces_analyzer.utils.hexstring import HexString

CallDataNew = TypedDict(
    "CallDataNew",
    {
        "address": HexString,
        "input": HexString,
    },
)


class CallInstruction(Instruction, ABC):
    @abstractmethod
    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        pass

    @abstractmethod
    def get_immediate_return_writes(self, output_oracle: InstructionOutputOracle) -> StorageWrites:
        pass


@dataclass(frozen=True, repr=False, eq=False)
class CALL(CallInstruction):
    io_specification = InstructionIOSpec(
        stack_input_count=7,
        memory_input_offset_arg=3,
        memory_input_size_arg=4,
    )

    @override
    def get_data(self) -> CallDataNew:
        assert self.memory_input is not None, f"Tried to get CALL data but contains no memory: {self}"
        return {"address": self.stack_inputs[1], "input": self.memory_input}

    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        offset = self.stack_inputs[5].as_int()
        size = self.stack_inputs[6].as_int()
        return_data = child_call_context.return_data
        # TODO: we should probably add an assert here for return_data is not None
        if size == 0:
            return StorageWrites()
        return_data_slice = return_data[:size]
        return StorageWrites(memory=[MemoryWrite(offset, return_data_slice)])

    def get_immediate_return_writes(self, output_oracle: InstructionOutputOracle) -> StorageWrites:
        """Writes that occur on a call to a precompiled contract or an EOA"""
        offset = self.stack_inputs[5].as_int()
        size = self.stack_inputs[6].as_int()
        return_data = output_oracle.memory[offset * 2 : (offset + size) * 2]
        return_data_slice = return_data[: size * 2]
        return StorageWrites(
            memory=[MemoryWrite(offset, StorageByteGroup.deprecated_from_hexstring(return_data_slice))]
        )


@dataclass(frozen=True, repr=False, eq=False)
class STATICCALL(CallInstruction):
    io_specification = InstructionIOSpec(
        stack_input_count=6,
        memory_input_offset_arg=2,
        memory_input_size_arg=3,
    )

    @override
    def get_data(self) -> CallDataNew:
        assert self.memory_input is not None, f"Tried to get STATICCALL data but contains no memory: {self}"
        return {"address": self.stack_inputs[1], "input": self.memory_input}

    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        offset = self.stack_inputs[4].as_int()
        size = self.stack_inputs[5].as_int()
        return_data = child_call_context.return_data
        if size == 0:
            return StorageWrites()
        return_data_slice = return_data[:size]
        return StorageWrites(memory=[MemoryWrite(offset, return_data_slice)])

    def get_immediate_return_writes(self, output_oracle: InstructionOutputOracle) -> StorageWrites:
        offset = self.stack_inputs[4].as_int()
        size = self.stack_inputs[5].as_int()
        return_data = output_oracle.memory[offset * 2 : (offset + size) * 2]
        return_data_slice = return_data[: size * 2]
        return StorageWrites(
            memory=[MemoryWrite(offset, StorageByteGroup.deprecated_from_hexstring(return_data_slice))]
        )


@dataclass(frozen=True, repr=False, eq=False)
class DELEGATECALL(CallInstruction):
    io_specification = InstructionIOSpec(
        stack_input_count=6,
        memory_input_offset_arg=2,
        memory_input_size_arg=3,
    )

    @override
    def get_data(self) -> CallDataNew:
        assert self.memory_input is not None, f"Tried to get DELEGATECALL data but contains no memory: {self}"
        return {"address": self.stack_inputs[1], "input": self.memory_input}

    @override
    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        offset = self.stack_inputs[4].as_int()
        size = self.stack_inputs[5].as_int()
        return_data = child_call_context.return_data
        if size == 0:
            return StorageWrites()
        return_data_slice = return_data[: size * 2]
        return StorageWrites(memory=[MemoryWrite(offset, return_data_slice)])

    @override
    def get_immediate_return_writes(self, output_oracle: InstructionOutputOracle) -> StorageWrites:
        offset = self.stack_inputs[4].as_int()
        size = self.stack_inputs[5].as_int()
        return_data = output_oracle.memory[offset * 2 : (offset + size) * 2]
        return_data_slice = return_data[: size * 2]
        return StorageWrites(
            memory=[MemoryWrite(offset, StorageByteGroup.deprecated_from_hexstring(return_data_slice))]
        )


@dataclass(frozen=True, repr=False, eq=False)
class CALLCODE(CallInstruction):
    io_specification = InstructionIOSpec(
        stack_input_count=7,
        memory_input_offset_arg=3,
        memory_input_size_arg=4,
    )

    @override
    def get_data(self) -> CallDataNew:
        assert self.memory_input is not None, f"Tried to get CALLCODE data but contains no memory: {self}"
        return {"address": self.stack_inputs[1], "input": self.memory_input}

    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        offset = self.stack_inputs[5].as_int()
        size = self.stack_inputs[6].as_int()
        return_data = child_call_context.return_data
        if size == 0:
            return StorageWrites()
        return_data_slice = return_data[:size]
        return StorageWrites(memory=[MemoryWrite(offset, return_data_slice)])

    @override
    def get_immediate_return_writes(self, output_oracle: InstructionOutputOracle) -> StorageWrites:
        offset = self.stack_inputs[5].as_int()
        size = self.stack_inputs[6].as_int()
        return_data = output_oracle.memory[offset * 2 : (offset + size) * 2]
        return_data_slice = return_data[: size * 2]
        return StorageWrites(
            memory=[MemoryWrite(offset, StorageByteGroup.deprecated_from_hexstring(return_data_slice))]
        )


def _make_simple(io_spec: InstructionIOSpec = InstructionIOSpec()):
    """
    TODO:
    - pass list of InstructionIOFlow
    """

    @dataclass(frozen=True, repr=False, eq=False)
    class SimpleInstruction(Instruction):
        io_specification = io_spec

    return SimpleInstruction


def _make_flow(io_flow_spec: FlowSpec = noop()):
    @dataclass(frozen=True, repr=False, eq=False)
    class FlowInstruction(Instruction):
        flow_spec = io_flow_spec

    return FlowInstruction


STOP = _make_simple()

ADD = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
MUL = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SUB = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
DIV = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SDIV = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))

MOD = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SMOD = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
ADDMOD = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1), stack_arg(2)))
MULMOD = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1), stack_arg(2)))
EXP = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SIGNEXTEND = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
LT = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
GT = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SLT = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SGT = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
EQ = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
ISZERO = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0)))
AND = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
OR = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
XOR = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
NOT = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0)))
BYTE = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SHL = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SHR = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))
SAR = _make_flow(combine(stack_push(oracle_stack_peek(0)), stack_arg(0), stack_arg(1)))

# flow([stack_range(2), mem_range_from_stack(0, 1)] -> stack_index(0))
KECCAK256 = _make_simple(
    InstructionIOSpec(stack_input_count=2, stack_output_count=1, memory_input_offset_arg=0, memory_input_size_arg=1)
)
# flow([] -> stack_index(0))
ADDRESS = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
# flow([stack_range(1), balance_from_stack(0)] -> stack_index(0))
# _from_flows([stack.push(balance.at(stack.arg(0)))])
BALANCE = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
ORIGIN = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
# flow([msg_sender] -> [stack_index(0)])
CALLER = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
# flow([call_value] -> [stack_index(0)])
CALLVALUE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
# flow([stack_range(1), call_data_from_stack(0)] -> [stack_index(0)])
# _from_flows([stack.push(calldata.slice(stack.arg(0), const(1)))])
CALLDATALOAD = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
# flow([call_data] -> [stack_index(0)])
CALLDATASIZE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))


@dataclass(frozen=True, repr=False, eq=False)
class CALLDATACOPY(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=3, memory_output_offset_arg=0, memory_output_size_arg=2)

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InstructionIO:
        io = super().parse_io(env, output_oracle)
        offset = io.inputs_stack[0].as_int()
        size = io.inputs_stack[2].as_int()

        return replace(io, output_memory=output_oracle.memory[offset * 2 : (offset + size) * 2])

    @override
    def get_writes(self) -> StorageWrites:
        offset = self.stack_inputs[0].as_int()
        assert self.memory_output is not None, f"CALLDATACOPY with None memory output: {self}"
        return StorageWrites(
            memory=[MemoryWrite(offset, StorageByteGroup.deprecated_from_hexstring(self.memory_output))]
        )


CODESIZE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))


@dataclass(frozen=True, repr=False, eq=False)
class CODECOPY(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=3, memory_output_offset_arg=0, memory_output_size_arg=2)

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InstructionIO:
        io = super().parse_io(env, output_oracle)
        offset = io.inputs_stack[0].as_int()
        size = io.inputs_stack[2].as_int()

        return replace(io, output_memory=output_oracle.memory[offset * 2 : (offset + size) * 2])

    @override
    def get_writes(self) -> StorageWrites:
        assert self.memory_output is not None, f"Tried to CODECOPY but no memory output: {self}"
        return StorageWrites(
            memory=[
                MemoryWrite(
                    self.stack_inputs[0].as_int(), StorageByteGroup.deprecated_from_hexstring(self.memory_output)
                )
            ]
        )


@dataclass(frozen=True, repr=False, eq=False)
class EXTCODECOPY(Instruction):
    io_specification = InstructionIOSpec(stack_input_count=4, memory_output_offset_arg=1, memory_output_size_arg=3)

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InstructionIO:
        io = super().parse_io(env, output_oracle)
        offset = io.inputs_stack[1].as_int()
        size = io.inputs_stack[3].as_int()

        return replace(io, output_memory=output_oracle.memory[offset * 2 : (offset + size) * 2])

    @override
    def get_writes(self) -> StorageWrites:
        assert self.memory_output is not None, f"Tried to EXTCODECOPY but no memory output: {self}"
        return StorageWrites(
            memory=[
                MemoryWrite(
                    self.stack_inputs[1].as_int(), StorageByteGroup.deprecated_from_hexstring(self.memory_output)
                )
            ]
        )


GASPRICE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
EXTCODESIZE = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))

RETURNDATASIZE = _make_flow(stack_push(return_data_size()))
RETURNDATACOPY = _make_flow(mem_write(stack_arg(0), return_data_range(stack_arg(1), stack_arg(2))))


EXTCODEHASH = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
BLOCKHASH = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
COINBASE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
TIMESTAMP = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
NUMBER = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PREVRANDAO = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
GASLIMIT = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
CHAINID = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
SELFBALANCE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
BASEFEE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
BLOBHASH = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
BLOBBASEFEE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
POP = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=0))


MLOAD = _make_flow(stack_push(mem_range(stack_arg(0), 32)))
MSTORE = _make_flow(mem_write(stack_arg(0), stack_arg(1)))
MSTORE8 = _make_flow(mem_write(stack_arg(0), to_size(stack_arg(1), 1)))


SLOAD = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
SSTORE = _make_simple(InstructionIOSpec(stack_input_count=2))
JUMP = _make_simple(InstructionIOSpec(stack_input_count=1))
JUMPI = _make_simple(InstructionIOSpec(stack_input_count=2))
PC = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
MSIZE = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
GAS = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
JUMPDEST = _make_simple()
TLOAD = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
TSTORE = _make_simple(InstructionIOSpec(stack_input_count=2))

MCOPY = _make_flow(mem_write(stack_arg(0), mem_range(stack_arg(1), stack_arg(2))))

PUSH0 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH1 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH2 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH3 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH4 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH5 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH6 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH7 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH8 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH9 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH10 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH11 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH12 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH13 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH14 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH15 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH16 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH17 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH18 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH19 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH20 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH21 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH22 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH23 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH24 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH25 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH26 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH27 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH28 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH29 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH30 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH31 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
PUSH32 = _make_simple(InstructionIOSpec(stack_input_count=0, stack_output_count=1))
DUP1 = _make_simple(InstructionIOSpec(stack_input_count=1, stack_output_count=1))
DUP2 = _make_simple(InstructionIOSpec(stack_input_count=2, stack_output_count=1))
DUP3 = _make_simple(InstructionIOSpec(stack_input_count=3, stack_output_count=1))
DUP4 = _make_simple(InstructionIOSpec(stack_input_count=4, stack_output_count=1))
DUP5 = _make_simple(InstructionIOSpec(stack_input_count=5, stack_output_count=1))
DUP6 = _make_simple(InstructionIOSpec(stack_input_count=6, stack_output_count=1))
DUP7 = _make_simple(InstructionIOSpec(stack_input_count=7, stack_output_count=1))
DUP8 = _make_simple(InstructionIOSpec(stack_input_count=8, stack_output_count=1))
DUP9 = _make_simple(InstructionIOSpec(stack_input_count=9, stack_output_count=1))
DUP10 = _make_simple(InstructionIOSpec(stack_input_count=10, stack_output_count=1))
DUP11 = _make_simple(InstructionIOSpec(stack_input_count=11, stack_output_count=1))
DUP12 = _make_simple(InstructionIOSpec(stack_input_count=12, stack_output_count=1))
DUP13 = _make_simple(InstructionIOSpec(stack_input_count=13, stack_output_count=1))
DUP14 = _make_simple(InstructionIOSpec(stack_input_count=14, stack_output_count=1))
DUP15 = _make_simple(InstructionIOSpec(stack_input_count=15, stack_output_count=1))
DUP16 = _make_simple(InstructionIOSpec(stack_input_count=16, stack_output_count=1))
SWAP1 = _make_simple(InstructionIOSpec(stack_input_count=2, stack_output_count=2))
SWAP2 = _make_simple(InstructionIOSpec(stack_input_count=3, stack_output_count=3))
SWAP3 = _make_simple(InstructionIOSpec(stack_input_count=4, stack_output_count=4))
SWAP4 = _make_simple(InstructionIOSpec(stack_input_count=5, stack_output_count=5))
SWAP5 = _make_simple(InstructionIOSpec(stack_input_count=6, stack_output_count=6))
SWAP6 = _make_simple(InstructionIOSpec(stack_input_count=7, stack_output_count=7))
SWAP7 = _make_simple(InstructionIOSpec(stack_input_count=8, stack_output_count=8))
SWAP8 = _make_simple(InstructionIOSpec(stack_input_count=9, stack_output_count=9))
SWAP9 = _make_simple(InstructionIOSpec(stack_input_count=10, stack_output_count=10))
SWAP10 = _make_simple(InstructionIOSpec(stack_input_count=11, stack_output_count=11))
SWAP11 = _make_simple(InstructionIOSpec(stack_input_count=12, stack_output_count=12))
SWAP12 = _make_simple(InstructionIOSpec(stack_input_count=13, stack_output_count=13))
SWAP13 = _make_simple(InstructionIOSpec(stack_input_count=14, stack_output_count=14))
SWAP14 = _make_simple(InstructionIOSpec(stack_input_count=15, stack_output_count=15))
SWAP15 = _make_simple(InstructionIOSpec(stack_input_count=16, stack_output_count=16))
SWAP16 = _make_simple(InstructionIOSpec(stack_input_count=17, stack_output_count=17))
LOG0 = _make_simple(InstructionIOSpec(stack_input_count=2, memory_input_offset_arg=0, memory_input_size_arg=1))
LOG1 = _make_simple(InstructionIOSpec(stack_input_count=3, memory_input_offset_arg=0, memory_input_size_arg=1))
LOG2 = _make_simple(InstructionIOSpec(stack_input_count=4, memory_input_offset_arg=0, memory_input_size_arg=1))
LOG3 = _make_simple(InstructionIOSpec(stack_input_count=5, memory_input_offset_arg=0, memory_input_size_arg=1))
LOG4 = _make_simple(InstructionIOSpec(stack_input_count=6, memory_input_offset_arg=0, memory_input_size_arg=1))


@dataclass(frozen=True, repr=False, eq=False)
class CREATE(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=3, stack_output_count=1, memory_input_offset_arg=1, memory_input_size_arg=2
    )

    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        return StorageWrites()


@dataclass(frozen=True, repr=False, eq=False)
class CREATE2(Instruction):
    io_specification = InstructionIOSpec(
        stack_input_count=4, stack_output_count=1, memory_input_offset_arg=1, memory_input_size_arg=2
    )

    def get_return_writes(self, child_call_context: CallContext) -> StorageWrites:
        return StorageWrites()


RETURN = _make_flow(return_data_write(mem_range(stack_arg(0), stack_arg(1))))
REVERT = _make_flow(return_data_write(mem_range(stack_arg(0), stack_arg(1))))

INVALID = _make_simple()
SELFDESTRUCT = _make_simple(InstructionIOSpec(stack_input_count=1))

_INSTRUCTIONS: Mapping[int, type[Instruction]] = {
    0x00: STOP,
    0x01: ADD,
    0x02: MUL,
    0x03: SUB,
    0x04: DIV,
    0x05: SDIV,
    0x06: MOD,
    0x07: SMOD,
    0x08: ADDMOD,
    0x09: MULMOD,
    0x0A: EXP,
    0x0B: SIGNEXTEND,
    0x10: LT,
    0x11: GT,
    0x12: SLT,
    0x13: SGT,
    0x14: EQ,
    0x15: ISZERO,
    0x16: AND,
    0x17: OR,
    0x18: XOR,
    0x19: NOT,
    0x1A: BYTE,
    0x1B: SHL,
    0x1C: SHR,
    0x1D: SAR,
    0x20: KECCAK256,
    0x30: ADDRESS,
    0x31: BALANCE,
    0x32: ORIGIN,
    0x33: CALLER,
    0x34: CALLVALUE,
    0x35: CALLDATALOAD,
    0x36: CALLDATASIZE,
    0x37: CALLDATACOPY,
    0x38: CODESIZE,
    0x39: CODECOPY,
    0x3A: GASPRICE,
    0x3B: EXTCODESIZE,
    0x3C: EXTCODECOPY,
    0x3D: RETURNDATASIZE,
    0x3E: RETURNDATACOPY,
    0x3F: EXTCODEHASH,
    0x40: BLOCKHASH,
    0x41: COINBASE,
    0x42: TIMESTAMP,
    0x43: NUMBER,
    0x44: PREVRANDAO,
    0x45: GASLIMIT,
    0x46: CHAINID,
    0x47: SELFBALANCE,
    0x48: BASEFEE,
    0x49: BLOBHASH,
    0x4A: BLOBBASEFEE,
    0x50: POP,
    0x51: MLOAD,
    0x52: MSTORE,
    0x53: MSTORE8,
    0x54: SLOAD,
    0x55: SSTORE,
    0x56: JUMP,
    0x57: JUMPI,
    0x58: PC,
    0x59: MSIZE,
    0x5A: GAS,
    0x5B: JUMPDEST,
    0x5C: TLOAD,
    0x5D: TSTORE,
    0x5E: MCOPY,
    0x5F: PUSH0,
    0x60: PUSH1,
    0x61: PUSH2,
    0x62: PUSH3,
    0x63: PUSH4,
    0x64: PUSH5,
    0x65: PUSH6,
    0x66: PUSH7,
    0x67: PUSH8,
    0x68: PUSH9,
    0x69: PUSH10,
    0x6A: PUSH11,
    0x6B: PUSH12,
    0x6C: PUSH13,
    0x6D: PUSH14,
    0x6E: PUSH15,
    0x6F: PUSH16,
    0x70: PUSH17,
    0x71: PUSH18,
    0x72: PUSH19,
    0x73: PUSH20,
    0x74: PUSH21,
    0x75: PUSH22,
    0x76: PUSH23,
    0x77: PUSH24,
    0x78: PUSH25,
    0x79: PUSH26,
    0x7A: PUSH27,
    0x7B: PUSH28,
    0x7C: PUSH29,
    0x7D: PUSH30,
    0x7E: PUSH31,
    0x7F: PUSH32,
    0x80: DUP1,
    0x81: DUP2,
    0x82: DUP3,
    0x83: DUP4,
    0x84: DUP5,
    0x85: DUP6,
    0x86: DUP7,
    0x87: DUP8,
    0x88: DUP9,
    0x89: DUP10,
    0x8A: DUP11,
    0x8B: DUP12,
    0x8C: DUP13,
    0x8D: DUP14,
    0x8E: DUP15,
    0x8F: DUP16,
    0x90: SWAP1,
    0x91: SWAP2,
    0x92: SWAP3,
    0x93: SWAP4,
    0x94: SWAP5,
    0x95: SWAP6,
    0x96: SWAP7,
    0x97: SWAP8,
    0x98: SWAP9,
    0x99: SWAP10,
    0x9A: SWAP11,
    0x9B: SWAP12,
    0x9C: SWAP13,
    0x9D: SWAP14,
    0x9E: SWAP15,
    0x9F: SWAP16,
    0xA0: LOG0,
    0xA1: LOG1,
    0xA2: LOG2,
    0xA3: LOG3,
    0xA4: LOG4,
    0xF0: CREATE,
    0xF1: CALL,
    0xF2: CALLCODE,
    0xF3: RETURN,
    0xF4: DELEGATECALL,
    0xF5: CREATE2,
    0xFA: STATICCALL,
    0xFD: REVERT,
    0xFE: INVALID,
    0xFF: SELFDESTRUCT,
}

# set the opcodes so we can access eg CALL.opcode
for opcode, instruction_class in _INSTRUCTIONS.items():
    instruction_class.opcode = opcode


def get_instruction_class(opcode: int) -> type[Instruction] | None:
    return _INSTRUCTIONS.get(opcode)