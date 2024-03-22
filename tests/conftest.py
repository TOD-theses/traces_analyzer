from pytest import fixture
from pathlib import Path
import sys


@fixture
def root_dir(request) -> Path:
    return request.config.rootpath


@fixture
def sample_traces_path(root_dir) -> Path:
    return root_dir / "sample_traces"


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
