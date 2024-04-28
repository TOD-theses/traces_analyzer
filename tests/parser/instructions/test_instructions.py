from typing import TypeVar, cast
from tests.conftest import TEST_ROOT_CALLCONTEXT
from tests.test_utils.test_utils import _test_group
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import *
from traces_analyzer.parser.instructions_parser import InstructionMetadata, parse_instruction
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import MemoryAccess
from traces_analyzer.utils.hexstring import HexString


_opcodes_to_instruction = [
    (0x00, STOP),
    (0x01, ADD),
    (0x02, MUL),
    (0x03, SUB),
    (0x04, DIV),
    (0x05, SDIV),
    (0x06, MOD),
    (0x07, SMOD),
    (0x08, ADDMOD),
    (0x09, MULMOD),
    (0x0A, EXP),
    (0x0B, SIGNEXTEND),
    (0x10, LT),
    (0x11, GT),
    (0x12, SLT),
    (0x13, SGT),
    (0x14, EQ),
    (0x15, ISZERO),
    (0x16, AND),
    (0x17, OR),
    (0x18, XOR),
    (0x19, NOT),
    (0x1A, BYTE),
    (0x1B, SHL),
    (0x1C, SHR),
    (0x1D, SAR),
    (0x20, KECCAK256),
    (0x30, ADDRESS),
    (0x31, BALANCE),
    (0x32, ORIGIN),
    (0x33, CALLER),
    (0x34, CALLVALUE),
    (0x35, CALLDATALOAD),
    (0x36, CALLDATASIZE),
    (0x37, CALLDATACOPY),
    (0x38, CODESIZE),
    (0x39, CODECOPY),
    (0x3A, GASPRICE),
    (0x3B, EXTCODESIZE),
    (0x3C, EXTCODECOPY),
    (0x3D, RETURNDATASIZE),
    (0x3E, RETURNDATACOPY),
    (0x3F, EXTCODEHASH),
    (0x40, BLOCKHASH),
    (0x41, COINBASE),
    (0x42, TIMESTAMP),
    (0x43, NUMBER),
    (0x44, PREVRANDAO),
    (0x45, GASLIMIT),
    (0x46, CHAINID),
    (0x47, SELFBALANCE),
    (0x48, BASEFEE),
    (0x49, BLOBHASH),
    (0x4A, BLOBBASEFEE),
    (0x50, POP),
    (0x51, MLOAD),
    (0x52, MSTORE),
    (0x53, MSTORE8),
    (0x54, SLOAD),
    (0x55, SSTORE),
    (0x56, JUMP),
    (0x57, JUMPI),
    (0x58, PC),
    (0x59, MSIZE),
    (0x5A, GAS),
    (0x5B, JUMPDEST),
    (0x5C, TLOAD),
    (0x5D, TSTORE),
    (0x5E, MCOPY),
    (0x5F, PUSH0),
    (0x60, PUSH1),
    (0x61, PUSH2),
    (0x62, PUSH3),
    (0x63, PUSH4),
    (0x64, PUSH5),
    (0x65, PUSH6),
    (0x66, PUSH7),
    (0x67, PUSH8),
    (0x68, PUSH9),
    (0x69, PUSH10),
    (0x6A, PUSH11),
    (0x6B, PUSH12),
    (0x6C, PUSH13),
    (0x6D, PUSH14),
    (0x6E, PUSH15),
    (0x6F, PUSH16),
    (0x70, PUSH17),
    (0x71, PUSH18),
    (0x72, PUSH19),
    (0x73, PUSH20),
    (0x74, PUSH21),
    (0x75, PUSH22),
    (0x76, PUSH23),
    (0x77, PUSH24),
    (0x78, PUSH25),
    (0x79, PUSH26),
    (0x7A, PUSH27),
    (0x7B, PUSH28),
    (0x7C, PUSH29),
    (0x7D, PUSH30),
    (0x7E, PUSH31),
    (0x7F, PUSH32),
    (0x80, DUP1),
    (0x81, DUP2),
    (0x82, DUP3),
    (0x83, DUP4),
    (0x84, DUP5),
    (0x85, DUP6),
    (0x86, DUP7),
    (0x87, DUP8),
    (0x88, DUP9),
    (0x89, DUP10),
    (0x8A, DUP11),
    (0x8B, DUP12),
    (0x8C, DUP13),
    (0x8D, DUP14),
    (0x8E, DUP15),
    (0x8F, DUP16),
    (0x90, SWAP1),
    (0x91, SWAP2),
    (0x92, SWAP3),
    (0x93, SWAP4),
    (0x94, SWAP5),
    (0x95, SWAP6),
    (0x96, SWAP7),
    (0x97, SWAP8),
    (0x98, SWAP9),
    (0x99, SWAP10),
    (0x9A, SWAP11),
    (0x9B, SWAP12),
    (0x9C, SWAP13),
    (0x9D, SWAP14),
    (0x9E, SWAP15),
    (0x9F, SWAP16),
    (0xA0, LOG0),
    (0xA1, LOG1),
    (0xA2, LOG2),
    (0xA3, LOG3),
    (0xA4, LOG4),
    (0xF0, CREATE),
    (0xF1, CALL),
    (0xF2, CALLCODE),
    (0xF3, RETURN),
    (0xF4, DELEGATECALL),
    (0xF5, CREATE2),
    (0xFA, STATICCALL),
    (0xFD, REVERT),
    (0xFE, INVALID),
    (0xFF, SELFDESTRUCT),
]


def test_instruction_opcode_matches_class():
    # not using parametrized test for performance
    for opcode, cls in _opcodes_to_instruction:
        assert get_instruction_class(opcode) == cls
        assert cls.opcode == opcode


_instruction_stack_io_counts = [
    (STOP, 0, 0),
    (ADD, 2, 1),
    (MUL, 2, 1),
    (SUB, 2, 1),
    (DIV, 2, 1),
    (SDIV, 2, 1),
    (MOD, 2, 1),
    (SMOD, 2, 1),
    (ADDMOD, 3, 1),
    (MULMOD, 3, 1),
    (EXP, 2, 1),
    (SIGNEXTEND, 2, 1),
    (LT, 2, 1),
    (GT, 2, 1),
    (SLT, 2, 1),
    (SGT, 2, 1),
    (EQ, 2, 1),
    (ISZERO, 1, 1),
    (AND, 2, 1),
    (OR, 2, 1),
    (XOR, 2, 1),
    (NOT, 1, 1),
    (BYTE, 2, 1),
    (SHL, 2, 1),
    (SHR, 2, 1),
    (SAR, 2, 1),
    (KECCAK256, 2, 1),
    (ADDRESS, 0, 1),
    (BALANCE, 1, 1),
    (ORIGIN, 0, 1),
    (CALLER, 0, 1),
    (CALLVALUE, 0, 1),
    (CALLDATALOAD, 1, 1),
    (CALLDATASIZE, 0, 1),
    (CALLDATACOPY, 3, 0),
    (CODESIZE, 0, 1),
    (CODECOPY, 3, 0),
    (GASPRICE, 0, 1),
    (EXTCODESIZE, 1, 1),
    (EXTCODECOPY, 4, 0),
    #  (RETURNDATASIZE, 0, 1),
    #  (RETURNDATACOPY, 3, 0),
    (EXTCODEHASH, 1, 1),
    (BLOCKHASH, 1, 1),
    (COINBASE, 0, 1),
    (TIMESTAMP, 0, 1),
    (NUMBER, 0, 1),
    (PREVRANDAO, 0, 1),
    (GASLIMIT, 0, 1),
    (CHAINID, 0, 1),
    (SELFBALANCE, 0, 1),
    (BASEFEE, 0, 1),
    (BLOBHASH, 1, 1),
    (BLOBBASEFEE, 0, 1),
    (POP, 1, 0),
    # (MLOAD, 1, 1),
    # (MSTORE, 2, 0),
    # (MSTORE8, 2, 0),
    (SLOAD, 1, 1),
    (SSTORE, 2, 0),
    (JUMP, 1, 0),
    (JUMPI, 2, 0),
    (PC, 0, 1),
    (MSIZE, 0, 1),
    (GAS, 0, 1),
    (JUMPDEST, 0, 0),
    (TLOAD, 1, 1),
    (TSTORE, 2, 0),
    # (MCOPY, 3, 0),
    (PUSH1, 0, 1),
    (PUSH2, 0, 1),
    (PUSH3, 0, 1),
    (PUSH4, 0, 1),
    (PUSH5, 0, 1),
    (PUSH6, 0, 1),
    (PUSH7, 0, 1),
    (PUSH8, 0, 1),
    (PUSH9, 0, 1),
    (PUSH10, 0, 1),
    (PUSH11, 0, 1),
    (PUSH12, 0, 1),
    (PUSH13, 0, 1),
    (PUSH14, 0, 1),
    (PUSH15, 0, 1),
    (PUSH16, 0, 1),
    (DUP1, 1, 1),
    (DUP2, 2, 1),
    (DUP3, 3, 1),
    (DUP4, 4, 1),
    (DUP5, 5, 1),
    (DUP6, 6, 1),
    (DUP7, 7, 1),
    (DUP8, 8, 1),
    (DUP9, 9, 1),
    (DUP10, 10, 1),
    (DUP11, 11, 1),
    (DUP12, 12, 1),
    (DUP13, 13, 1),
    (DUP14, 14, 1),
    (DUP15, 15, 1),
    (DUP16, 16, 1),
    (SWAP1, 2, 2),
    (SWAP2, 3, 3),
    (SWAP3, 4, 4),
    (SWAP4, 5, 5),
    (SWAP5, 6, 6),
    (SWAP6, 7, 7),
    (SWAP7, 8, 8),
    (SWAP8, 9, 9),
    (SWAP9, 10, 10),
    (SWAP10, 11, 11),
    (SWAP11, 12, 12),
    (SWAP12, 13, 13),
    (SWAP13, 14, 14),
    (SWAP14, 15, 15),
    (SWAP15, 16, 16),
    (SWAP16, 17, 17),
    (LOG0, 2, 0),
    (LOG1, 3, 0),
    (LOG2, 4, 0),
    (LOG3, 5, 0),
    (LOG4, 6, 0),
    (CREATE, 3, 1),
    (CALL, 7, 0),
    (CALLCODE, 7, 0),
    # (RETURN, 2, 0),
    (DELEGATECALL, 6, 0),
    (CREATE2, 4, 1),
    (STATICCALL, 6, 0),
    # (REVERT, 2, 0),
    (INVALID, 0, 0),
    (SELFDESTRUCT, 1, 0),
]


def test_stack_io():
    for instruction, stack_inputs, stack_outputs in _instruction_stack_io_counts:
        assert instruction.io_specification.stack_input_count == stack_inputs
        assert instruction.io_specification.stack_output_count == stack_outputs


_instruction_memory_args = [
    (KECCAK256, 0, 1, None, None),
    (CALLDATACOPY, None, None, 0, 2),
    (CODECOPY, None, None, 0, 2),
    (EXTCODECOPY, None, None, 1, 3),
    # (RETURNDATACOPY, None, None, 0, 2),
    # (MLOAD, 0, None, None, None),
    # (MSTORE, None, None, 0, None),
    # (MSTORE8, None, None, 0, None),
    # (MCOPY, 1, 2, 0, 2),
    *[(log, 0, 1, None, None) for log in [LOG0, LOG1, LOG2, LOG3, LOG4]],
    (CREATE, 1, 2, None, None),
    (CALL, 3, 4, None, None),
    (CALLCODE, 3, 4, None, None),
    # (RETURN, 0, 1, None, None),
    (DELEGATECALL, 2, 3, None, None),
    (CREATE2, 1, 2, None, None),
    (STATICCALL, 2, 3, None, None),
    # (REVERT, 0, 1, None, None),
]


def test_memory_inputs():
    for instruction, input_offset_arg, input_size_arg, output_offset_arg, output_size_arg in _instruction_memory_args:
        assert instruction.io_specification.memory_input_offset_arg == input_offset_arg
        assert instruction.io_specification.memory_input_size_arg == input_size_arg
        assert instruction.io_specification.memory_output_offset_arg == output_offset_arg
        assert instruction.io_specification.memory_output_size_arg == output_size_arg


InstructionType = TypeVar("InstructionType", bound=Instruction)


def _test_parse_instruction(
    instr: type[InstructionType], env: ParsingEnvironment, output_oracle: InstructionOutputOracle
) -> InstructionType:
    return cast(InstructionType, parse_instruction(env, InstructionMetadata(instr.opcode, 0), output_oracle))


dummy_output_oracle = InstructionOutputOracle([], HexString(""), None)


def test_mload() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push(_test_group("4"))
    env.memory.set(0x4, _test_group("11223344"), -1)

    mload = _test_parse_instruction(MLOAD, env, dummy_output_oracle)

    padded_value = "11223344" + (28) * 2 * "0"
    accesses = mload.get_accesses()
    assert accesses.memory == [MemoryAccess(offset=0x4, value=_test_group(padded_value))]
    assert mload.stack_outputs == (padded_value,)


def test_mstore() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all(
        [
            _test_group("4"),
            _test_group("11223344"),
        ]
    )

    mstore = _test_parse_instruction(MSTORE, env, dummy_output_oracle)

    padded_value = 28 * 2 * "0" + "11223344"
    writes = mstore.get_writes()
    assert writes.memory == [MemoryWrite(offset=0x4, value=_test_group(padded_value))]


def test_mstore8() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([_test_group("4"), _test_group("1")])

    mstore8 = _test_parse_instruction(MSTORE8, env, dummy_output_oracle)

    writes = mstore8.get_writes()
    assert writes.memory == [MemoryWrite(offset=0x4, value=_test_group(HexString("01").as_size(8)))]


def test_mcopy() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([_test_group("20"), _test_group("3"), _test_group("4")])
    env.memory.set(0x4, _test_group("11223344"), -1)

    mcopy = _test_parse_instruction(MCOPY, env, dummy_output_oracle)

    accesses = mcopy.get_accesses()
    assert accesses.memory == [MemoryAccess(offset=0x3, value=_test_group("00112233"))]

    writes = mcopy.get_writes()
    assert writes.memory == [MemoryWrite(offset=0x20, value=_test_group("00112233"))]


def test_return() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([_test_group("2"), _test_group("4")])
    env.memory.set(0, _test_group("1122334455667788"), 1)

    return_instr = _test_parse_instruction(RETURN, env, dummy_output_oracle)

    accesses = return_instr.get_accesses()
    assert len(accesses.memory) == 1
    assert accesses.memory[0].offset == 2
    assert accesses.memory[0].value == _test_group("33445566")

    writes = return_instr.get_writes()
    assert writes.return_data
    assert writes.return_data.value == _test_group("33445566")


def test_revert() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([_test_group("2"), _test_group("4")])
    env.memory.set(0, _test_group("1122334455667788"), 1)

    revert = _test_parse_instruction(REVERT, env, dummy_output_oracle)

    accesses = revert.get_accesses()
    assert len(accesses.memory) == 1
    assert accesses.memory[0].offset == 2
    assert accesses.memory[0].value == _test_group("33445566")

    writes = revert.get_writes()
    assert writes.return_data
    assert writes.return_data.value == _test_group("33445566")


def test_returndatasize() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_call_context.return_data = _test_group("112233445566")

    returndatasize = _test_parse_instruction(RETURNDATASIZE, env, dummy_output_oracle)

    accesses = returndatasize.get_accesses()
    assert accesses.return_data
    assert accesses.return_data.offset == 0
    assert accesses.return_data.size == 6
    assert accesses.return_data.value == _test_group("112233445566")

    writes = returndatasize.get_writes()
    assert len(writes.stack_pushes) == 1
    assert writes.stack_pushes[0].value.get_hexstring().as_int() == 6


def test_returndatacopy() -> None:
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([_test_group("123"), _test_group("2"), _test_group("4")])
    env.current_call_context.return_data = _test_group("1122334455667788")

    returndatasize = _test_parse_instruction(RETURNDATACOPY, env, dummy_output_oracle)

    accesses = returndatasize.get_accesses()
    assert accesses.return_data
    assert accesses.return_data.offset == 2
    assert accesses.return_data.size == 4
    assert accesses.return_data.value == _test_group("33445566")

    writes = returndatasize.get_writes()
    assert len(writes.memory) == 1
    assert writes.memory[0].offset == 0x123
    assert writes.memory[0].value == _test_group("33445566")
