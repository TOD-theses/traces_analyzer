from traces_analyzer.preprocessing.instruction_io import InstructionIOSpec, parse_instruction_io


def test_parse_instructions_io_empty():
    io_spec = InstructionIOSpec()

    io = parse_instruction_io(io_spec, [], "", [], "")

    assert io.inputs_stack == ()
    assert io.outputs_stack == ()
    assert io.input_memory == None
    assert io.output_memory == None


def test_parse_instructions_io_stack():
    io_spec = InstructionIOSpec(stack_input_count=2, stack_output_count=1)

    io = parse_instruction_io(io_spec, ["0x3", "0x2", "0x1"], "", ["0x33", "0x22", "0x11"], "")

    assert io.inputs_stack == ("0x1", "0x2")
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
    input_stack = list(reversed(["0x2", "0x4", "0x0", "0x6"]))
    input_memory = "0000111122223333"
    output_memory = "4444555566667777"

    io = parse_instruction_io(io_spec, input_stack, input_memory, [], output_memory)

    assert io.input_memory == "11112222"
    assert io.output_memory == "444455556666"
