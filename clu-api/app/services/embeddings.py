"""ChromaDB-backed semantic embedding and similarity search for extracted entities."""

import hashlib
import json
import logging

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> chromadb.HttpClient:
    """Get ChromaDB HTTP client."""
    return chromadb.HttpClient(
        host=settings.chromadb_host,
        port=settings.chromadb_port,
    )


def _entity_to_text(entity: dict, entity_type: str) -> str:
    """Convert an extracted entity to a searchable text string."""
    if entity_type == "decisions":
        return f"Decision: {entity.get('what', '')}. Decided by: {', '.join(entity.get('decidedBy', []))}."
    elif entity_type == "requirements":
        return f"Requirement ({entity.get('type', 'unknown')}): {entity.get('description', '')}."
    elif entity_type == "actionItems":
        return f"Action item: {entity.get('action', '')}. Owner: {entity.get('owner', '')}."
    elif entity_type == "risks":
        return f"Risk: {entity.get('risk', '')}. Severity: {entity.get('severity', '')}."
    elif entity_type == "openQuestions":
        return f"Open question: {entity.get('question', '')}."
    elif entity_type == "technicalConstraints":
        return f"Technical constraint: {entity.get('constraint', '')}."
    else:
        return json.dumps(entity)


def _entity_id(source_name: str, entity_type: str, entity: dict) -> str:
    """Generate a stable ID for an entity."""
    content = json.dumps(entity, sort_keys=True)
    hash_input = f"{source_name}:{entity_type}:{content}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def index_extraction(extraction_data: dict, project_id: str) -> int:
    """Index all entities from a single extraction into ChromaDB.

    Returns the number of entities indexed.
    """
    client = _get_client()
    collection = client.get_or_create_collection(
        name=f"clu_{project_id}",
        metadata={"hnsw:space": "cosine"},
    )

    source_name = extraction_data.get("source", {}).get("name", "unknown")
    entity_types = [
        "decisions", "requirements", "actionItems",
        "risks", "openQuestions", "technicalConstraints",
    ]

    documents = []
    metadatas = []
    ids = []

    for entity_type in entity_types:
        entities = extraction_data.get(entity_type, [])
        for entity in entities:
            doc_text = _entity_to_text(entity, entity_type)
            doc_id = _entity_id(source_name, entity_type, entity)

            documents.append(doc_text)
            metadatas.append({
                "source": source_name,
                "entity_type": entity_type,
                "entity_json": json.dumps(entity),
            })
            ids.append(doc_id)

    if documents:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Indexed %d entities from %s into project %s", len(documents), source_name, project_id)

    return len(documents)


def find_similar_entities(
    query_text: str,
    project_id: str,
    n_results: int = 10,
    entity_type: str | None = None,
) -> list[dict]:
    """Find semantically similar entities in the project's collection.

    Returns list of dicts with: document, metadata, distance.
    """
    client = _get_client()

    try:
        collection = client.get_collection(name=f"clu_{project_id}")
    except Exception:
        logger.warning("No collection found for project %s", project_id)
        return []

    where_filter = {"entity_type": entity_type} if entity_type else None

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_filter,
    )

    similar = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similar.append({
                "document": doc,
                "source": meta.get("source"),
                "entity_type": meta.get("entity_type"),
                "entity": json.loads(meta.get("entity_json", "{}")),
                "similarity": 1.0 - dist,  # cosine distance → similarity
            })

    return similar


def find_semantic_conflicts(project_id: str, threshold: float = 0.7) -> list[dict]:
    """Find potential conflicts by looking for semantically similar entities
    from different sources that might contradict each other.

    Focuses on decisions and requirements — the most conflict-prone entity types.
    """
    client = _get_client()

    try:
        collection = client.get_collection(name=f"clu_{project_id}")
    except Exception:
        return []

    # Get all decisions and requirements from the collection
    all_items = collection.get(
        where={"entity_type": {"$in": ["decisions", "requirements"]}},
        include=["documents", "metadatas"],
    )

    if not all_items["documents"]:
        return []

    conflicts = []
    seen_pairs = set()

    for i, (doc, meta) in enumerate(zip(all_items["documents"], all_items["metadatas"])):
        # Query for similar items
        results = collection.query(
            query_texts=[doc],
            n_results=5,
            where={"entity_type": {"$in": ["decisions", "requirements"]}},
        )

        if not results["documents"] or not results["documents"][0]:
            continue

        for j, (sim_doc, sim_meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            similarity = 1.0 - dist
            if similarity < threshold or similarity > 0.99:
                continue  # Skip low similarity and self-matches

            source_a = meta.get("source")
            source_b = sim_meta.get("source")

            if source_a == source_b:
                continue  # Same source — not a cross-transcript conflict

            pair_key = tuple(sorted([all_items["ids"][i], results["ids"][0][j]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            conflicts.append({
                "entity_a": {
                    "text": doc,
                    "source": source_a,
                    "entity": json.loads(meta.get("entity_json", "{}")),
                },
                "entity_b": {
                    "text": sim_doc,
                    "source": source_b,
                    "entity": json.loads(sim_meta.get("entity_json", "{}")),
                },
                "similarity": similarity,
                "entity_type": meta.get("entity_type"),
            })

    # Sort by similarity (highest first — most likely conflicts)
    conflicts.sort(key=lambda c: c["similarity"], reverse=True)
    return conflicts


def delete_project_collection(project_id: str) -> None:
    """Delete the ChromaDB collection for a project."""
    client = _get_client()
    try:
        client.delete_collection(name=f"clu_{project_id}")
        logger.info("Deleted collection for project %s", project_id)
    except Exception:
        pass  # Collection may not exist
