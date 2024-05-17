from typing import TYPE_CHECKING, Sequence

from networkx import DiGraph, MultiDiGraph

from traces_analyzer.parser.information_flow.constant_step_indexes import PRESTATE
from traces_analyzer.parser.instructions.instruction import Instruction

if TYPE_CHECKING:
    InformationFlowGraph = MultiDiGraph[int]
else:
    InformationFlowGraph = DiGraph


def build_information_flow_graph(
    instructions: Sequence[Instruction],
) -> InformationFlowGraph:
    graph: InformationFlowGraph = MultiDiGraph()

    graph.add_node(PRESTATE, instruction=None)

    for instruction in instructions:
        graph.add_node(instruction.step_index, instruction=instruction)

        for (
            step_index,
            access,
            storage_byte_group,
        ) in instruction.get_accesses().get_dependencies():
            graph.add_edge(
                step_index,
                instruction.step_index,
                access=access,
                storage_byte_group=storage_byte_group,
            )

    return graph
