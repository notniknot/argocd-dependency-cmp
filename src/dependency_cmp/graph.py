import logging
import sys
from graphlib import TopologicalSorter

from .models import DEPENDS_ON_ANNOTATION, SYNC_WAVE_ANNOTATION, get_resource_key

logger = logging.getLogger("dependency_cmp")


def process_dag(manifests):
    """Builds DAG and calculates sync waves."""
    graph = {}
    resource_map = {}  # Map ID -> Doc
    keys_list = []  # List of ResourceKey objects for searching

    # 1. Index Resources
    for doc in manifests:
        if not doc:
            continue

        rkey = get_resource_key(doc)

        resource_map[rkey.id] = doc
        keys_list.append(rkey)

        if rkey.id not in graph:
            graph[rkey.id] = set()

    # 2. Build Edges (Resolve Dependencies)
    for rkey in keys_list:
        doc = resource_map[rkey.id]
        metadata = doc.get("metadata") or {}
        annotations = metadata.get("annotations") or {}

        if DEPENDS_ON_ANNOTATION in annotations:
            deps_str = annotations[DEPENDS_ON_ANNOTATION]
            if deps_str:
                # Split comma separated dependencies
                raw_deps = [d.strip() for d in deps_str.split(",") if d.strip()]

                for raw_dep in raw_deps:
                    # Resolve matches
                    matches = [k for k in keys_list if k.matches(raw_dep)]

                    if len(matches) == 1:
                        target_id = matches[0].id
                        graph[rkey.id].add(target_id)
                    elif len(matches) > 1:
                        logger.error(
                            f"Ambiguous dependency '{raw_dep}' in '{rkey.id}'. Matches: {[m.id for m in matches]}"
                        )
                        sys.exit(1)
                    else:
                        logger.warning(
                            f"Resource '{rkey.id}' depends on '{raw_dep}', but it was not found."
                        )

    # 3. Calculate Waves
    sorter = TopologicalSorter(graph)
    try:
        sorter.prepare()
    except ValueError as e:
        logger.error(f"Cycle detected in dependencies: {e}")
        sys.exit(1)

    waves = {}
    current_wave = 0
    while sorter.is_active():
        ready = sorter.get_ready()
        for node in ready:
            waves[node] = current_wave
        sorter.done(*ready)
        current_wave += 1

    # 4. Inject Annotations
    for key_id, wave in waves.items():
        doc = resource_map[key_id]
        if doc.get("metadata") is None:
            doc["metadata"] = {}
        if doc["metadata"].get("annotations") is None:
            doc["metadata"]["annotations"] = {}

        doc["metadata"]["annotations"][SYNC_WAVE_ANNOTATION] = str(wave)
        if wave > 0:
            logger.info(f"Assigned Wave {wave} to {key_id}")

    return manifests
