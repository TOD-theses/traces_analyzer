from typing import TYPE_CHECKING, Sequence

from networkx import DiGraph, MultiDiGraph

from traces_analyzer.parser.instructions.instruction import Instruction

PRESTATE = -1

if TYPE_CHECKING:
    graph_type = MultiDiGraph[int]
else:
    graph_type = DiGraph


def build_information_flow_graph(instructions: Sequence[Instruction]) -> graph_type:
    graph: graph_type = MultiDiGraph()

    graph.add_node(PRESTATE, instruction=None)

    for instruction in instructions:
        graph.add_node(instruction.step_index, instruction=instruction)

        for step_index, access, storage_byte_group in instruction.get_accesses().get_dependencies():
            graph.add_edge(step_index, instruction.step_index, access=access, storage_byte_group=storage_byte_group)

        if 2 in graph.nodes:
            print(instruction)
            print(sorted(graph.in_edges(2)))
            print(sorted(graph.out_edges(2)))

    return graph
