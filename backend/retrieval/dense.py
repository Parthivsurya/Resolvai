"""Dense semantic retrieval over the persisted Chroma collection."""
from __future__ import annotations

from functools import lru_cache

from .. import config
from ..nlp import embed


@lru_cache(maxsize=1)
def _collection():
    import chromadb

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(config.CHROMA_COLLECTION)


def search(query: str, top_k: int | None = None, category: str | None = None) -> list[dict]:
    """Return the top dense matches as dicts with a normalised ``score`` in [0, 1].

    If ``category`` is given, retrieval is filtered to that document category (intent-driven
    routing). Cosine distance from Chroma is converted to a similarity score.
    """
    top_k = top_k or config.TOP_K_DENSE
    where = {"category": category} if category else None
    res = _collection().query(
        query_embeddings=[embed.encode_query(query)],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    ids = res["ids"][0]
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    out: list[dict] = []
    for cid, text, meta, dist in zip(ids, docs, metas, dists):
        out.append(
            {
                "chunk_id": cid,
                "text": text,
                "source": meta.get("source"),
                "category": meta.get("category"),
                "doc_id": meta.get("doc_id"),
                "score": 1.0 - float(dist),  # cosine distance -> similarity
            }
        )
    return out
