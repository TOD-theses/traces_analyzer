from typing import Callable
import pytest
from traces_analyzer.parser.call_context import CallContext, HaltType
from traces_analyzer.parser.call_context_manager import (
    CallContextManager,
    ExpectedDepthChange,
    UnexpectedDepthChange,
)
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instructions import (
    ADD,
    CALL,
    CALLCODE,
    CREATE,
    CREATE2,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
)

get_root = lambda: CallContext(None, "", 1, "0xsender", "0xcode", "0xstorage")
get_child_of: Callable[[CallContext, str], CallContext] = lambda parent, address: CallContext(
    parent, "", parent.depth + 1, parent.code_address, address, address
)
get_child = lambda: get_child_of(get_root(), "0xchild")
get_grandchild = lambda: get_child_of(get_child(), "0xgrandchild")
get_manager: Callable[[CallContext], CallContextManager] = lambda call_context: CallContextManager(call_context)

get_add: Callable[[CallContext], Instruction] = lambda call_context: ADD(
    ADD.opcode, "ADD", 1, call_context, (1, 2), (3), None, None
)
get_call: Callable[[CallContext, str], Instruction] = lambda call_context, address: CALL(
    CALL.opcode,
    "CALL",
    1,
    call_context,
    ("0x1234", address, "0x1", "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
)
get_staticcall: Callable[[CallContext, str], Instruction] = lambda call_context, address: STATICCALL(
    STATICCALL.opcode,
    "STATICCALL",
    1,
    call_context,
    ("0x1234", address, "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
)
get_delegate_call: Callable[[CallContext, str], Instruction] = lambda call_context, address: DELEGATECALL(
    DELEGATECALL.opcode,
    "DELEGATECALL",
    1,
    call_context,
    ("0x1234", address, "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
)
get_callcode: Callable[[CallContext, str], Instruction] = lambda call_context, address: CALLCODE(
    CALLCODE.opcode,
    "CALLCODE",
    1,
    call_context,
    ("0x1234", address, "0x1", "0x0", "0x4", "0x0", "0x0"),
    (),
    "11111111",
    None,
)
get_create: Callable[[CallContext], Instruction] = lambda call_context: CREATE(
    CREATE.opcode, "CREATE", 1, call_context, ("0x0", "0x0", "0x4"), (), "11111111", None
)
get_create2: Callable[[CallContext], Instruction] = lambda call_context: CREATE(
    CREATE2.opcode, "CREATE2", 1, call_context, ("0x0", "0x0", "0x4", "0x0"), (), "11111111", None
)
get_stop: Callable[[CallContext], Instruction] = lambda call_context: STOP(
    STOP.opcode, "STOP", 1, call_context, (), (), None, None
)
get_return: Callable[[CallContext], Instruction] = lambda call_context: RETURN(
    RETURN.opcode, "RETURN", 1, call_context, ("0x0", "0x0"), (), "", ""
)
get_revert: Callable[[CallContext], Instruction] = lambda call_context: REVERT(
    REVERT.opcode, "REVERT", 1, call_context, ("0x0", "0x0"), (), "", ""
)
get_selfdestruct: Callable[[CallContext], Instruction] = lambda call_context: SELFDESTRUCT(
    SELFDESTRUCT.opcode, "SELFDESTRUCT", 1, call_context, ("0x0"), (), "", ""
)


def test_call_context_manager_uses_root():
    root = get_root()
    manager = get_manager(root)

    assert manager.get_current_call_context() == root


def test_call_context_manager_does_not_update_on_add():
    root = get_root()
    manager = get_manager(root)
    add = get_add(root)

    manager.on_step(add, root.depth)

    assert manager.get_current_call_context() == root
    assert not root.reverted


def test_call_context_managers_does_not_enter_without_depth_change():
    """For instance when the call only sends ether, we don't want to dont enter a new call context"""
    root = get_root()
    manager = get_manager(root)
    call = get_call(root, "0xtarget")

    manager.on_step(call, root.depth)

    assert manager.get_current_call_context() == root


# TODO: are there other instructions that create a new call context? eg CREATE?
@pytest.mark.parametrize("call", [get_call(get_root(), "0xtarget"), get_staticcall(get_root(), "0xtarget")])
def test_call_context_manager_enters_with_code_and_storage(call):
    root = get_root()
    manager = get_manager(root)

    manager.on_step(call, root.depth + 1)

    current_call_context = manager.get_current_call_context()
    assert current_call_context.depth == 2
    assert current_call_context.msg_sender == root.code_address
    assert current_call_context.code_address == "0xtarget"
    assert current_call_context.storage_address == "0xtarget"
    assert current_call_context.calldata == "11111111"
    assert not current_call_context.is_contract_initialization


@pytest.mark.parametrize("call", [get_delegate_call(get_root(), "0xtarget"), get_callcode(get_root(), "0xtarget")])
def test_call_context_manager_enters_only_with_code_address(call):
    root = get_root()
    manager = get_manager(root)

    manager.on_step(call, root.depth + 1)

    current_call_context = manager.get_current_call_context()
    assert current_call_context.depth == 2
    assert current_call_context.msg_sender == root.code_address
    assert current_call_context.code_address == "0xtarget"
    assert current_call_context.storage_address == root.storage_address
    assert current_call_context.calldata == "11111111"
    assert not current_call_context.is_contract_initialization


@pytest.mark.parametrize("create", [get_create(get_root()), get_create2(get_root())])
def test_call_context_manager_enters_on_contract_creation(create):
    root = get_root()
    manager = get_manager(root)

    manager.on_step(create, root.depth + 1)

    current_call_context = manager.get_current_call_context()
    assert current_call_context.depth == 2
    assert current_call_context.msg_sender == root.code_address
    # NOTE: the manager DOES NOT compute the correct addresses for the created contracts
    # TODO: should we bother to compute the correct addresses (also depending on CREATE/CREATE2)?
    assert current_call_context.code_address == "0x812ae3f62c368435ee7783a18a29b0c91ae375c302bbf9d73cac"
    assert current_call_context.storage_address == "0x812ae3f62c368435ee7783a18a29b0c91ae375c302bbf9d73cac"
    assert current_call_context.calldata == "11111111"
    assert current_call_context.is_contract_initialization


def test_call_context_manager_throws_on_stop_without_depth_change():
    child = get_child()
    manager = get_manager(child)
    stop = get_stop(child)

    with pytest.raises(ExpectedDepthChange):
        manager.on_step(stop, child.depth)


def test_call_context_manager_throws_on_too_large_depth_change():
    grandchild = get_grandchild()
    manager = get_manager(grandchild)
    stop = get_stop(grandchild)

    with pytest.raises(UnexpectedDepthChange):
        manager.on_step(stop, grandchild.depth - 2)


def test_call_context_manager_throws_on_stop_at_root():
    root = get_root()
    manager = get_manager(root)
    stop = get_stop(root)

    with pytest.raises(UnexpectedDepthChange):
        manager.on_step(stop, root.depth - 1)


@pytest.mark.parametrize("ret", [get_stop(get_child()), get_return(get_child()), get_selfdestruct(get_child())])
def test_call_context_manager_returns_normal(ret):
    root = get_root()
    child = get_child()
    manager = get_manager(child)

    manager.on_step(ret, child.depth - 1)

    assert manager.get_current_call_context() == root
    assert not child.reverted
    assert child.halt_type == HaltType.NORMAL


def test_call_context_manager_reverts():
    root = get_root()
    child = get_child()
    manager = get_manager(child)

    manager.on_step(get_revert(get_child()), child.depth - 1)

    assert manager.get_current_call_context() == root
    assert child.reverted
    assert child.halt_type == HaltType.NORMAL


def test_call_context_manager_makes_exceptional_halt():
    root = get_root()
    child = get_child()
    manager = get_manager(child)
    add = get_add(child)

    manager.on_step(add, child.depth - 1)

    assert manager.get_current_call_context() == root
    assert child.reverted
    assert child.halt_type == HaltType.EXCEPTIONAL


def test_call_context_manager_tree_base():
    root = get_root()
    manager = get_manager(root)

    tree = manager.get_call_tree()

    assert tree.call_context == root
    assert tree.children == []


def test_call_context_manager_tree_order():
    """
    root
    - first
    - - first_nested
    - second
    - third
    """
    root = get_root()
    manager = get_manager(root)

    def stop():
        return get_stop(manager.get_current_call_context())

    manager.on_step(get_call(root, "0xfirst"), 2)
    manager.on_step(get_call(manager.get_current_call_context(), "0xfirst_nested"), 3)
    manager.on_step(stop(), 2)
    manager.on_step(stop(), 1)
    manager.on_step(get_call(root, "0xsecond"), 2)
    manager.on_step(stop(), 1)
    manager.on_step(get_call(root, "0xthird"), 2)
    manager.on_step(stop(), 1)
    tree = manager.get_call_tree()

    # correct structure
    assert tree.call_context == root
    assert len(tree.children) == 3
    first, second, third = tree.children
    assert len(first.children) == 1
    first_nested = first.children[0]

    # correct addresses
    assert first.call_context.code_address == "0xfirst"
    assert first_nested.call_context.code_address == "0xfirst_nested"
    assert second.call_context.code_address == "0xsecond"
    assert third.call_context.code_address == "0xthird"
