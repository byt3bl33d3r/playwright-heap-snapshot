import re
import logging
from typing import Any, Dict, List, Callable, Optional

from .models import BuiltHeapValue, HeapSnapshot, HeapSnapshotStructuredGraph, HeapSnapshotStructuredEdge
from .structured_graph import create_structured_graph

log = logging.getLogger('heapsnapshot.build_object')

async def build_object_from_node_id(
    heap_snapshot: HeapSnapshot,
    node_id: int,
    property_filter: Callable[[str], bool] = lambda _: True
) -> BuiltHeapValue:
    log.debug(f"building node object for node {node_id}")

    graph = await create_structured_graph(
        heap_snapshot=heap_snapshot,
        node_id=node_id,
        edge_filter=lambda edge: (
            (edge['type'] == 'property' and edge['name'] != '__proto__' and property_filter(edge['name'])) or
            edge['type'] in ['element', 'hidden'] or
            edge['name'] == 'value'
        )
    )

    if graph['node']['type'] != 'object':
        raise ValueError(f"Node '{node_id}' is not object, cannot build object")

    log.debug(f"compiling graph node object {node_id}")
    return await compile_graph_node_object(graph)

async def compile_graph_node_object(graph: HeapSnapshotStructuredGraph) -> BuiltHeapValue:
    node = graph['node']
    node_type = node['type']
    node_name = node['name']

    edges = [edge for edge in graph['edges'] if await filter_edge(edge)]

    if node_type == 'array':
        return [await compile_graph_node_object(edge['graph']) for edge in edges]

    elif node_type == 'object':
        if node_name == 'Object':
            return {
                edge['edge']['name']: await compile_graph_node_object(edge['graph'])
                for edge in edges
            }
        elif node_name == 'Array':
            return await compile_graph_node_object({
                **graph,
                'node': {**graph['node'], 'type': 'array'}
            })
        else:
            raise ValueError(f"Unknown or unsupported object with type '{node_name}'")

    elif node_type == 'string':
        return node['name']

    elif node_type == 'regexp':
        return re.compile(node['name'])

    elif node_type == 'number':
        return float(next(edge for edge in edges if edge['edge']['name'] == 'value')['graph']['node']['name'])

    elif await is_boolean(graph):
        return next(edge for edge in edges if edge['graph']['node']['type'] == 'string')['graph']['node']['name'] == 'true'

    elif await is_null(graph):
        return None
    else:
        raise ValueError(f"Unknown graph node type '{node_type}', unable to compile graph object")

async def is_boolean(graph: HeapSnapshotStructuredGraph) -> bool:
    return (
        graph['node']['type'] == 'hidden' and
        any(edge['graph']['node']['name'] == 'boolean' for edge in graph['edges'])
    )

async def is_null(graph: HeapSnapshotStructuredGraph) -> bool:
    return (
        graph['node']['type'] == 'hidden' and
        any(edge['graph']['node']['name'] == 'object' for edge in graph['edges']) and
        any(edge['graph']['node']['name'] == 'null' for edge in graph['edges'])
    )

async def filter_edge(edge: Dict) -> bool:
    edge_node_type = edge.get('graph', {}).get('node', {}).get('type')

    if not edge_node_type:
        return False

    if edge_node_type == 'object':
        return edge['graph']['node']['name'] in ['Array', 'Object']
    else:
        return edge_node_type in ['array', 'string', 'number', 'regexp'] or await is_boolean(edge['graph']) or await is_null(edge['graph'])
