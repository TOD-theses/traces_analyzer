from pytest import FixtureRequest, fixture
from pathlib import Path
import pytest
import sys

from tests.test_utils.test_utils import _test_group, _test_mem, _test_stack
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions.instructions import JUMPDEST, get_instruction_class
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
    None, HexString(""), 1, HexString("0"), HexString("0"), HexString("0"), None, _test_group(""), False, None
)


def make_instruction(
    type: type[Instruction] = JUMPDEST,
    pc=1,
    step_index=0,
    stack=_test_stack([]),
    memory=_test_mem(""),
    stack_after=[],
    memory_after="",
    call_context=TEST_ROOT_CALLCONTEXT,
):
    # TODO: directly create instruction instead of parsing inputs/outputs from stack
    stack_after = [HexString(val) for val in stack_after]
    memory_after = HexString(memory_after)

    name = opcode_to_name(type.opcode) or "UNKNOWN"

    cls = get_instruction_class(type.opcode) or Instruction
    io_spec = cls.io_specification

    io = parse_instruction_io(
        io_spec,  # type: ignore
        stack,
        memory,
        stack_after,
        memory_after,
    )
    return cls(
        type.opcode,
        name,
        pc,
        step_index,
        call_context,
        io.inputs_stack,
        io.outputs_stack,
        io.input_memory,
        io.output_memory,
    )
