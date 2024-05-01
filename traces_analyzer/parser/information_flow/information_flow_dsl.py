from traces_analyzer.parser.information_flow.information_flow_dsl_implementation import (
    FlowNodeWithResult,
    FlowSpec,
    NoopNode,
    WritingFlowNode,
    _mem_range_node,
    _mem_write_node,
    _return_data_range_node,
    _return_data_size_node,
    _return_data_write_node,
    _stack_arg_node,
    _stack_push_node,
    _stack_set_node,
    _to_size_node,
)


def stack_arg(index: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return _stack_arg_node(index)


def stack_push(value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _stack_push_node(value)


def stack_set(index: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _stack_set_node(index, value)


def mem_range(offset: FlowNodeWithResult | int, size: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return _mem_range_node(offset, size)


def mem_write(offset: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _mem_write_node(offset, value)


def to_size(value: FlowNodeWithResult, bytes_size: int) -> FlowNodeWithResult:
    return _to_size_node(value, bytes_size)


def return_data_range(offset: FlowNodeWithResult, size: FlowNodeWithResult) -> FlowNodeWithResult:
    return _return_data_range_node(offset, size)


def return_data_write(value: FlowNodeWithResult) -> WritingFlowNode:
    return _return_data_write_node(value)


def return_data_size() -> FlowNodeWithResult:
    return _return_data_size_node()


def noop() -> FlowSpec:
    return NoopNode()
