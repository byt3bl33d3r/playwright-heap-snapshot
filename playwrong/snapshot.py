import logging
from .models import HeapSnapshot, HeapSnapshotNode, HeapSnapshotEdge

log = logging.getLogger("heapsnapshot.snapshot")

COMMON_PROPERTIES = ["name"]

async def get_string(heap_snapshot: HeapSnapshot, string_id: int) -> str:
    return heap_snapshot.strings[string_id]

async def get_node_edge_ids(heap_snapshot: HeapSnapshot, node_id: int) -> list[int]:
    node, node_index = await find_node_by_id(heap_snapshot, node_id)

    edge_offset = 0

    for i in range(int(node_index)):
        edge_offset += await get_node_edge_count(heap_snapshot, await get_node_at_index(heap_snapshot, i))

    edge_count = await get_node_edge_count(heap_snapshot, node)

    return [edge_offset + i for i in range(edge_count)]

async def find_edge_parent_node_id(heap_snapshot: HeapSnapshot, edge_id: int) -> int:
    edge_id_offset = 0

    for i in range(heap_snapshot.snapshot.node_count):
        edge_id_offset += await get_node_edge_count(heap_snapshot, await get_node_at_index(heap_snapshot, i))

        if edge_id_offset > edge_id:
            return await get_field_value(heap_snapshot, "node", "id", await get_node_at_index(heap_snapshot, i))

    raise ValueError(f"Unable to find parent node for edge '{edge_id}'")

async def get_node_edge_count(heap_snapshot: HeapSnapshot, node: HeapSnapshotNode) -> int:
    return await get_field_value(heap_snapshot, "node", "edge_count", node)

async def find_edge_by_id(heap_snapshot: HeapSnapshot, edge_id: int) -> dict:
    edge = await get_edge_at_index(heap_snapshot, edge_id)

    if not edge:
        raise ValueError(f"Unable to find edge with id '{edge_id}'")

    return edge, edge_id

async def get_edge_at_index(heap_snapshot: HeapSnapshot, edge_index: int) -> HeapSnapshotEdge:
    edge_size = len(heap_snapshot.snapshot.meta.edge_fields)
    edge_offset = edge_index * edge_size
    return heap_snapshot.edges[edge_offset:edge_offset + edge_size]

async def get_field_value(heap_snapshot: HeapSnapshot, field_source: str, field_name: str, value: list, string_or_number_is_string: bool = False) -> str | int:
    fields = getattr(heap_snapshot.snapshot.meta, f"{field_source}_fields")
    field_index = fields.index(field_name)

    if field_index == -1:
        raise ValueError(f"Unknown node field: {field_name}")

    field_types = getattr(heap_snapshot.snapshot.meta, f"{field_source}_types")
    field_type = field_types[field_index]
    field_raw_value = value[field_index]

    field_value = None

    if isinstance(field_type, list):
        field_value = field_type[field_raw_value]
    elif field_type == "string":
        field_value = await get_string(heap_snapshot, field_raw_value)
    elif field_type == "number":
        field_value = field_raw_value
    elif field_type == "string_or_number":
        field_value = await get_string(heap_snapshot, field_raw_value) if string_or_number_is_string else field_raw_value
    elif field_type == "node":
        field_value = field_raw_value
    else:
        raise ValueError(f"Unknown field type '{field_type}'")

    if field_value is None:
        raise ValueError(f"Undefined returned for field value with {{fieldName: {field_name}, fieldType: {field_type}, fieldRawValue: {field_raw_value}, fieldSource: {field_source}, fieldIndex: {field_index}, fields: {','.join(fields)}, value: {','.join(map(str, value))}}}")

    return field_value

async def iterate_edges(heap_snapshot: HeapSnapshot):
    for edge_id in range(heap_snapshot.snapshot.edge_count):
        value = await get_edge_at_index(heap_snapshot, edge_id)
        yield value, edge_id

async def iterate_nodes(heap_snapshot: HeapSnapshot):
    for node_index in range(heap_snapshot.snapshot.node_count):
        value = await get_node_at_index(heap_snapshot, node_index)
        yield value, node_index

async def filter_edge_ids(heap_snapshot: HeapSnapshot, iterator: callable) -> list[int]:
    edge_ids = []

    async for edge, edge_id in iterate_edges(heap_snapshot):
        if await iterator(edge, edge_id):
            edge_ids.append(edge_id)

    return edge_ids

async def find_node_by_id(heap_snapshot: HeapSnapshot, node_id: int) -> dict:
    node = None
    node_index = None

    async for current_node, current_node_index in iterate_nodes(heap_snapshot):
        if await get_field_value(heap_snapshot, "node", "id", current_node) == node_id:
            node = current_node
            node_index = current_node_index
            break

    if node:
        return node, node_index
    else:
        raise ValueError(f"Unable to find node with id '{node_id}'")

async def get_node_at_index(heap_snapshot: HeapSnapshot, index: int) -> HeapSnapshotNode:
    if index > heap_snapshot.snapshot.node_count:
        raise ValueError(f"Attempting index node that is out of bounds of snapshot (index: {index}, total node count: {heap_snapshot.snapshot.node_count})")

    node_size = len(heap_snapshot.snapshot.meta.node_fields)
    node_offset = index * node_size

    return heap_snapshot.nodes[int(node_offset):int(node_offset + node_size)]

async def find_node_ids_with_properties(heap_snapshot: HeapSnapshot, property_names: list[str]) -> list[int]:
    if not property_names:
        raise ValueError(f"Please specify at least one property to find node ids for")

    common_properties = None

    for property_name in property_names:
        if common_properties is None:
            common_properties = await find_node_ids_with_property(heap_snapshot, property_name)
        elif not common_properties:
            return []
        
        log.debug(f"{len(common_properties)} common nodes")
        common_properties = await intersection(common_properties, await find_node_ids_with_property(heap_snapshot, property_name))

    return common_properties

async def find_node_ids_with_property(heap_snapshot: HeapSnapshot, property_name: str) -> list[int]:
    if property_name in COMMON_PROPERTIES:
        log.debug(f"property '{property_name}' is part of many objects and may be slow")

    edge_ids = await find_property_edge_ids_for_string(heap_snapshot, property_name)
    log.debug(f"{len(edge_ids)} nodes found with property {property_name}")
    return [await find_edge_parent_node_id(heap_snapshot, edge_id) for edge_id in edge_ids]

async def find_property_edge_ids_for_string(heap_snapshot: HeapSnapshot, string: str) -> list[int]:
    log.debug(f"finding property edges for string {string}")

    async def edge_filter(edge, edge_id):
        edge_type = await get_field_value(heap_snapshot, "edge", "type", edge)
        if edge_type != "property":
            return False
        edge_name = await get_field_value(heap_snapshot, "edge", "name_or_index", edge, True)
        return edge_name == string

    return await filter_edge_ids(heap_snapshot, edge_filter)

async def intersection(a: list, b: list) -> list:
    return [v for v in a if v in b]
