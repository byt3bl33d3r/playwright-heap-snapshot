import asyncio
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator

# Import necessary functions and types from the appropriate modules
from .snapshot import (
    find_edge_by_id,
    find_node_by_id,
    get_field_value,
    get_node_at_index,
    get_node_edge_ids,
)
from .models import (
    HeapSnapshot,
    HeapSnapshotStructuredEdge,
    HeapSnapshotStructuredGraph,
    HeapSnapshotStructuredNode,
)

async def create_structured_graph(
    heap_snapshot: HeapSnapshot,
    node_id: int,
    max_depth: int = float('inf'),
    edge_filter: Callable[[HeapSnapshotStructuredEdge], bool] = lambda edge: True,
    node_id_stack: List[int] = []
) -> HeapSnapshotStructuredGraph:
    structured_node = await create_structured_node(heap_snapshot, node_id)
    structured_edges = [
        edge for edge in [
            await create_structured_edge(heap_snapshot, edge_id)
            for edge_id in structured_node['edgeIds']
        ] if edge_filter(edge)
    ]

    edges = []
    for structured_edge in structured_edges:
        is_circular = structured_edge['nodeId'] in node_id_stack
        graph = None
        if not is_circular and len(node_id_stack) < max_depth:
            graph = await create_structured_graph(
                heap_snapshot=heap_snapshot,
                node_id=structured_edge['nodeId'],
                max_depth=max_depth,
                edge_filter=edge_filter,
                node_id_stack=[*node_id_stack, node_id]
            )
        edges.append({
            'isCircular': is_circular,
            'edge': structured_edge,
            'graph': graph,
        })

    return {
        'node': structured_node,
        'edges': edges,
    }

async def create_structured_node(
    heap_snapshot: HeapSnapshot,
    node_id: int
) -> HeapSnapshotStructuredNode:
    node, node_index = await find_node_by_id(heap_snapshot, node_id)
    edge_ids = await get_node_edge_ids(heap_snapshot, node_id)

    return {
        'nodeIndex': node_index,
        'edgeIds': edge_ids,
        'edgeCount': await get_field_value(heap_snapshot, 'node', 'edge_count', node),
        'type': await get_field_value(heap_snapshot, 'node', 'type', node),
        'name': await get_field_value(heap_snapshot, 'node', 'name', node),
        'id': await get_field_value(heap_snapshot, 'node', 'id', node),
        'size': await get_field_value(heap_snapshot, 'node', 'self_size', node),
        'traceNodeId': await get_field_value(heap_snapshot, 'node', 'trace_node_id', node),
        'detachness': await get_field_value(heap_snapshot, 'node', 'detachedness', node),
    }

async def create_structured_edge(
    heap_snapshot: HeapSnapshot,
    edge_id: int
) -> HeapSnapshotStructuredEdge:
    edge,_ = await find_edge_by_id(heap_snapshot, edge_id)

    type_ = await get_field_value(heap_snapshot, 'edge', 'type', edge)
    node_index = (
        await get_field_value(heap_snapshot, 'edge', 'to_node', edge)
    ) / len(heap_snapshot.snapshot.meta.node_fields)
    node_id = await get_field_value(
        heap_snapshot,
        'node',
        'id',
        await get_node_at_index(heap_snapshot, node_index)
    )
    is_index = type_ in ['element', 'hidden']
    name_or_index = await get_field_value(
        heap_snapshot,
        'edge',
        'name_or_index',
        edge,
        not is_index
    )

    return {
        'id': edge_id,
        'type': type_,
        'nodeId': node_id,
        'name': None if is_index else name_or_index,
        'index': name_or_index if is_index else None,
    }

async def format_structured_graph(
    structured_graph: HeapSnapshotStructuredGraph,
    indent_size: int = 0
) -> str:
    lines = []
    indent = '   ' * indent_size
    node = structured_graph['node']
    edges = structured_graph['edges']

    lines.append(
        f"{indent}Node{{{node['id']}}} {node['name']} (type: {node['type']}, size: {node['size']})"
    )

    for edge in edges:
        edge_data = edge['edge']
        graph = edge['graph']
        is_circular = edge['isCircular']
        lines.append(
            f"{indent}-> Edge{{{edge_data['id']}}} {edge_data['name'] or edge_data['index']} ({edge_data['type']}) -> Node{{{edge_data['nodeId']}}}"
            + (" (circular)" if is_circular else "")
        )
        if graph:
            formatted_graph = await format_structured_graph(graph, indent_size + 1)
            lines.append(formatted_graph)

    return '\n'.join(lines)
