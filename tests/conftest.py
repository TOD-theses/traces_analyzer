from typing import Sequence
from pytest import FixtureRequest, fixture
from pathlib import Path
import pytest
import sys

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions.instructions import JUMPDEST, get_instruction_class
from traces_analyzer.parser.environment.parsing_environment import ParsingEnvironment
from traces_analyzer.parser.storage.storage import HexStringStorageValue, HexStringStorageValue
from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.mnemonics import opcode_to_name


@fixture
def root_dir(request: FixtureRequest) -> Path:
    return request.config.rootpath


@fixture
def sample_traces_path(root_dir: Path) -> Path:
    sample_traces_path = root_dir / "sample_traces"

    if not sample_traces_path.is_dir():
        pytest.skip("This test requires traces from sample_traces")

    return sample_traces_path


# each test runs on cwd to its temp dir
@fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))
    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


TEST_ROOT_CALLCONTEXT = CallContext(
    None, HexString(""), 1, HexString("0"), HexString("0"), HexString("0"), None, None, False, None
)


def make_instruction(
    type: type[Instruction] = JUMPDEST,
    pc=1,
    step_index=0,
    stack=[],
    memory="",
    stack_after=[],
    memory_after="",
    call_context=TEST_ROOT_CALLCONTEXT,
):
    # TODO: directly create instruction instead of parsing inputs/outputs from stack
    assert (
        len(memory) % 64 == 0 and len(memory_after) % 64 == 0
    ), f"Memory must be a multiple of 64: {memory} / {memory_after}"
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = step_index
    env.stack.push_all([HexStringStorageValue(HexString(value)) for value in reversed(stack)])
    env.current_call_context = call_context
    env.memory.set(0, HexStringStorageValue(HexString(memory)))
    stack_after = [HexString(val) for val in stack_after]
    memory_after = HexString(memory_after)

    return _parse_instruction(env, type.opcode, pc, stack_after, memory_after)


def _parse_instruction(
    env: ParsingEnvironment,
    opcode: int,
    program_counter: int,
    next_stack: Sequence[HexString],
    next_memory: HexString | None,
) -> Instruction:
    name = opcode_to_name(opcode) or "UNKNOWN"

    cls = get_instruction_class(opcode) or Instruction
    spec = cls.io_specification

    io = parse_instruction_io(
        spec,
        env.stack.current_stack(),
        env.memory,
        next_stack,
        next_memory,
    )
    return cls(
        opcode,
        name,
        program_counter,
        env.current_step_index,
        env.current_call_context,
        io.inputs_stack,
        io.outputs_stack,
        io.input_memory,
        io.output_memory,
    )
