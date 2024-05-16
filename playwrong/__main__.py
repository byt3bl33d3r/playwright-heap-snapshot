import asyncio
import logging
import json
import pydantic
import typer
from rich import print as pprint
from rich.progress import Progress
from typing import Any, Dict, List, Annotated, Optional
from .models import HeapSnapshot
from .snapshot import find_node_ids_with_properties
from .build_object import build_object_from_node_id
from playwright.async_api import async_playwright

log = logging.getLogger('heapsnapshot')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
log.addHandler(handler)

HEAP_SNAPSHOT_TIMEOUT: int = 30000
HEAP_SNAPSHOT_SIZE: int  = 0
HEAP_SNAPSHOT_CHUNKS: List[str] = []

HEAP_SNAPSHOT: HeapSnapshot = None

app = typer.Typer()

async def find_objects_with_properties(heap_snapshot: HeapSnapshot, properties: List[str], ignore_properties: List[str] = []):
    log.debug(f"finding objects {properties=} {ignore_properties=}")
    node_ids = await find_node_ids_with_properties(heap_snapshot, properties)
    log.debug(f"{len(node_ids)} node(s) found, compiling object(s) {node_ids}")

    if len(node_ids) > 5:
        log.warning("more than 5 nodes found, this may be slow - to improve performance, increase the specifity of your query or ignore unwanted properties on the target object")

    return await asyncio.gather(*[
        build_object_from_node_id(heap_snapshot, node_id, lambda prop: prop not in ignore_properties)
        for node_id in node_ids
    ])

async def add_snapshot_chunk_cb(chunk: Dict[Any, Any]) -> None:
    global HEAP_SNAPSHOT_SIZE, HEAP_SNAPSHOT_CHUNKS
    chunk = chunk['chunk']

    HEAP_SNAPSHOT_SIZE += len(chunk)
    HEAP_SNAPSHOT_CHUNKS.append(chunk)

    #log.debug(f"heap snapshot chunk: size {len(chunk)}, total {HEAP_SNAPSHOT_SIZE}")

async def report_snapshot_progess_cb(progress: Dict[Any, Any]) -> None:
    done = progress['done']
    total = progress['total']
    finished = progress.get('finished')

    log.info(f'heap snapshot progress: {done}/{total}{f" finished: {finished}" if finished else ""}')

async def afetch(url: str, properties: List[str], output_file: typer.FileTextWrite = None, ignore_properties: List[str] = []):
    global HEAP_SNAPSHOT, HEAP_SNAPSHOT_CHUNKS

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        #context = await browser.new_context() #ignore_https_errors=True)

        page = await browser.new_page()
        await page.goto(url)

        with Progress() as progress_bar:
            snapshot_task = progress_bar.add_task("heap snapshot progress")

            cdp_session = await page.context.new_cdp_session(page)
            cdp_session.on("HeapProfiler.addHeapSnapshotChunk",  add_snapshot_chunk_cb)
            cdp_session.on("HeapProfiler.reportHeapSnapshotProgress",  lambda progress: progress_bar.update(snapshot_task, total=progress['total'], completed=progress['done']))
            cdp_session.on("error", lambda e: log.error(f"Error when capturing heap snapshot: {e}"))
            cdp_session.on("close", lambda: log.error("CDP session closed prematurely"))

            await cdp_session.send("HeapProfiler.takeHeapSnapshot", {'reportProgress': True, 'captureNumericValue': True})

        try:
            json_snapshot = ''.join(HEAP_SNAPSHOT_CHUNKS)
            HEAP_SNAPSHOT = HeapSnapshot.model_validate_json(json_snapshot)
            if output_file:
                json.dump(json_snapshot, output_file)

        except json.JSONDecodeError:
            log.error("Error decoding heap snapshot")
        except pydantic.ValidationError:
            log.error("Error parsing heap snapshot")
        else:
            pprint(await find_objects_with_properties(HEAP_SNAPSHOT, properties, ignore_properties))

        #await cdp_session.detach()

async def aquery(snapshot_file: typer.FileText, properties: List[str], ignore_properties: List[str] = []):
    global HEAP_SNAPSHOT

    HEAP_SNAPSHOT = HeapSnapshot.model_validate_json(snapshot_file.read())
    pprint(await find_objects_with_properties(HEAP_SNAPSHOT, properties, ignore_properties))

@app.command()
def fetch(
    url: Annotated[str, typer.Option("--url", "-u", help="URL to dump")],
    properties: Annotated[str, typer.Option("--properties", "-p", help="Comma seperated properties to search for")],
    output_file: Annotated[Optional[typer.FileTextWrite], typer.Option("-o", "--output", help="Output filepath")] = None,
    ignore_properties: Annotated[Optional[str], typer.Option("--ignore-properties", "-i", help="Comma seperated properties of properties to ignore on object")] = None
):
    """
    fetch a heap snapshot for a URL and/or write to a file then output the matching objects in JSON
    """
    asyncio.run(
        afetch(
            url=url,
            output_file=output_file,
            properties=properties.split(','),
            ignore_properties=ignore_properties.split(',') if ignore_properties else []
        )
    )

@app.command()
def query(
    file: Annotated[typer.FileText, typer.Option("--file", "-f", help="Snapshot file path")],
    properties: Annotated[str, typer.Option("--properties", "-p", help="Comma seperated properties to search for")],
    ignore_properties: Annotated[Optional[str], typer.Option("--ignore-properties", "-i", help="Comma seperated properties of properties to ignore on object")] = None
):
    """
    read a heap snapshot and output the matching objects in JSON
    """
    asyncio.run(
        aquery(
            snapshot_file=file,
            properties=properties.split(','),
            ignore_properties=ignore_properties.split(',') if ignore_properties else []
        )
    )

if __name__ == '__main__':
    app()
