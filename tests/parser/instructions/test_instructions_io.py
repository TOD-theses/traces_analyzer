from tests.test_utils.test_utils import _test_mem, _test_stack
from traces_analyzer.parser.instructions.instruction_io import InstructionIOSpec, parse_instruction_io
from traces_analyzer.utils.hexstring import HexString


def test_parse_instructions_io_empty():
    io_spec = InstructionIOSpec()

    io = parse_instruction_io(io_spec, _test_stack([]), _test_mem(""), [], "")

    assert io.inputs_stack == ()
    assert io.outputs_stack == ()
    assert io.input_memory == None
    assert io.output_memory == None


def test_parse_instructions_io_stack():
    io_spec = InstructionIOSpec(stack_input_count=2, stack_output_count=1)

    io = parse_instruction_io(io_spec, _test_stack(["0x1", "0x2", "0x3"]), _test_mem(""), ["0x11", "0x22", "0x33"], "")

    assert io.inputs_stack == (HexString("0x1").as_size(32), HexString("0x2").as_size(32))
    assert io.outputs_stack == ("0x11",)
    assert io.input_memory == None
    assert io.output_memory == None


def test_parse_instructions_io_memory_via_args():
    io_spec = InstructionIOSpec(
        stack_input_count=4,
        memory_input_offset_arg=0,
        memory_input_size_arg=1,
        memory_output_offset_arg=2,
        memory_output_size_arg=3,
    )
    input_stack = [hex(26), hex(4), hex(24), hex(6)]
    input_memory = HexString("0000000000000000000000000000000000000000000000000000111122223333").as_size(32)
    output_memory = HexString("0000000000000000000000000000000000000000000000004444555566667777").as_size(32)

    io = parse_instruction_io(io_spec, _test_stack(input_stack), _test_mem(input_memory), [], output_memory)

    assert io.input_memory == "11112222"
    assert io.output_memory == "444455556666"
