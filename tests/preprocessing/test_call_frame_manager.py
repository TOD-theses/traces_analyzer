from typing import Callable
import pytest
from traces_analyzer.preprocessing.call_frame import CallFrame, HaltType
from traces_analyzer.preprocessing.call_frame_manager import (
    CallFrameManager,
    ExpectedDepthChange,
    UnexpectedDepthChange,
)
from traces_analyzer.preprocessing.instruction import Instruction
from traces_analyzer.preprocessing.instructions import (
    ADD,
    CALL,
    CALLCODE,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
    op_from_class,
)

get_root = lambda: CallFrame(None, 1, "0xsender", "0xcode", "0xstorage")
get_child = lambda: CallFrame(get_root(), 2, get_root().code_address, "0xchildcode", "0xchildstorage")
get_grandchild = lambda: CallFrame(get_child(), 3, get_child().code_address, "0xgrandchildcode", "0xgrandchildstorage")
get_manager: Callable[[CallFrame], CallFrameManager] = lambda call_frame: CallFrameManager(call_frame)

get_add: Callable[[CallFrame], Instruction] = lambda call_frame: ADD(
    op_from_class(ADD), "ADD", 1, call_frame, (1, 2), (3), None, None, {}
)
get_call: Callable[[CallFrame, str], Instruction] = lambda call_frame, address: CALL(
    op_from_class(CALL),
    "CALL",
    1,
    call_frame,
    ("0x1234", address, "0x1", "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
    {},  # type: ignore
)
get_staticcall: Callable[[CallFrame, str], Instruction] = lambda call_frame, address: STATICCALL(
    op_from_class(STATICCALL),
    "STATICCALL",
    1,
    call_frame,
    ("0x1234", address, "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
    {},  # type: ignore
)
get_delegate_call: Callable[[CallFrame, str], Instruction] = lambda call_frame, address: DELEGATECALL(
    op_from_class(DELEGATECALL),
    "DELEGATECALL",
    1,
    call_frame,
    ("0x1234", address, "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
    {},  # type: ignore
)
get_callcode: Callable[[CallFrame, str], Instruction] = lambda call_frame, address: CALLCODE(
    op_from_class(CALLCODE),
    "CALLCODE",
    1,
    call_frame,
    ("0x1234", address, "0x1", "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
    {},  # type: ignore
)
get_stop: Callable[[CallFrame], Instruction] = lambda call_frame: STOP(
    op_from_class(STOP), "STOP", 1, call_frame, (), (), None, None, {}
)
get_return: Callable[[CallFrame], Instruction] = lambda call_frame: RETURN(
    op_from_class(RETURN), "RETURN", 1, call_frame, ("0x0", "0x0"), (), "", "", {}
)
get_revert: Callable[[CallFrame], Instruction] = lambda call_frame: REVERT(
    op_from_class(REVERT), "REVERT", 1, call_frame, ("0x0", "0x0"), (), "", "", {}
)
get_selfdestruct: Callable[[CallFrame], Instruction] = lambda call_frame: SELFDESTRUCT(
    op_from_class(SELFDESTRUCT), "SELFDESTRUCT", 1, call_frame, ("0x0"), (), "", "", {}
)


def test_call_frame_manager_uses_root():
    root = get_root()
    manager = get_manager(root)

    assert manager.get_current_call_frame() == root


def test_call_frame_manager_does_not_update_on_add():
    root = get_root()
    manager = get_manager(root)
    add = get_add(root)

    manager.on_step(add, root.depth)

    assert manager.get_current_call_frame() == root
    assert not root.reverted


def test_call_frame_managers_does_not_enter_without_depth_change():
    """For instance when the call only sends ether, we don't want to dont enter a new call frame"""
    root = get_root()
    manager = get_manager(root)
    call = get_call(root, "0xtarget")

    manager.on_step(call, root.depth)

    assert manager.get_current_call_frame() == root


@pytest.mark.parametrize("call", [get_call(get_root(), "0xtarget"), get_staticcall(get_root(), "0xtarget")])
def test_call_frame_manager_enters_with_code_and_storage(call):
    root = get_root()
    manager = get_manager(root)

    manager.on_step(call, root.depth + 1)

    current_call_frame = manager.get_current_call_frame()
    assert current_call_frame.depth == 2
    assert current_call_frame.msg_sender == root.code_address
    assert current_call_frame.code_address == "0xtarget"
    assert current_call_frame.storage_address == "0xtarget"


@pytest.mark.parametrize("call", [get_delegate_call(get_root(), "0xtarget"), get_callcode(get_root(), "0xtarget")])
def test_call_frame_manager_enters_only_with_code_address(call):
    root = get_root()
    manager = get_manager(root)

    manager.on_step(call, root.depth + 1)

    current_call_frame = manager.get_current_call_frame()
    assert current_call_frame.depth == 2
    assert current_call_frame.msg_sender == root.code_address
    assert current_call_frame.code_address == "0xtarget"
    assert current_call_frame.storage_address == root.storage_address


def test_call_frame_manager_throws_on_stop_without_depth_change():
    child = get_child()
    manager = get_manager(child)
    stop = get_stop(child)

    with pytest.raises(ExpectedDepthChange):
        manager.on_step(stop, child.depth)


def test_call_frame_manager_throws_on_too_large_depth_change():
    grandchild = get_grandchild()
    manager = get_manager(grandchild)
    stop = get_stop(grandchild)

    with pytest.raises(UnexpectedDepthChange):
        manager.on_step(stop, grandchild.depth - 2)


def test_call_frame_manager_throws_on_stop_at_root():
    root = get_root()
    manager = get_manager(root)
    stop = get_stop(root)

    with pytest.raises(UnexpectedDepthChange):
        manager.on_step(stop, root.depth - 1)


@pytest.mark.parametrize(
    "ret", [get_stop(get_child()), get_return(get_child()), get_revert(get_child()), get_selfdestruct(get_child())]
)
def test_call_frame_manager_returns_normal(ret):
    root = get_root()
    child = get_child()
    manager = get_manager(child)

    manager.on_step(ret, child.depth - 1)

    assert manager.get_current_call_frame() == root
    assert child.reverted
    assert child.halt_type == HaltType.NORMAL


def test_call_frame_manager_makes_exceptional_halt():
    root = get_root()
    child = get_child()
    manager = get_manager(child)
    add = get_add(child)

    manager.on_step(add, child.depth - 1)

    assert manager.get_current_call_frame() == root
    assert child.reverted
    assert child.halt_type == HaltType.EXCEPTIONAL
