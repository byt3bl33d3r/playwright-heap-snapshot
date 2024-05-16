from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any

HeapSnapshotNode = List[int]
HeapSnapshotEdge = List[int]
MetaValue = Union[str, List[str]]

class HeapSnapshotStructuredEdge(BaseModel):
    id: int
    type: str
    name: Optional[str] = None
    index: Optional[int] = None
    nodeId: int

class HeapSnapshotStructuredNode(BaseModel):
    id: int
    nodeIndex: int
    type: str
    name: str
    size: int
    edgeCount: int
    traceNodeId: int
    detachness: int
    edgeIds: List[int]

class HeapSnapshotStructuredGraph(BaseModel):
    node: HeapSnapshotStructuredNode
    edges: List[Dict[str, Union[bool, HeapSnapshotStructuredEdge, Optional['HeapSnapshotStructuredGraph']]]]

class SnapshotMeta(BaseModel):
    node_fields: List[MetaValue]
    node_types: List[MetaValue]
    edge_fields: List[MetaValue]
    edge_types: List[MetaValue]
    trace_function_info_fields: List[MetaValue]
    trace_node_fields: List[MetaValue]
    sample_fields: List[MetaValue]
    location_fields: List[MetaValue]

class Snapshot(BaseModel):
    node_count: int
    edge_count: int
    trace_function_count: int
    meta: SnapshotMeta

class HeapSnapshot(BaseModel):
    snapshot: Snapshot
    nodes: List[int]
    edges: List[int]
    strings: List[str]
    trace_function_infos: List[int]
    samples: List[int]
    trace_tree: List[int]
    locations: List[int]

BuiltHeapValue = Union[
    None,
    str,
    int,
    float,
    bool,
    List[Any],
    Dict[str, Any]
]
