"""Build the knowledge-base indexes.

Pipeline: load -> clean -> PII-mask -> chunk -> embed -> persist.

Outputs two co-indexed stores over the *same* chunks:
  * a persistent ChromaDB collection (dense semantic vectors), and
  * a pickled BM25 index + chunk metadata (sparse keyword search).

Run with:  ``python3 -m backend.ingest.build_index``
"""
from __future__ import annotations

import pickle
import re

from .. import config
from ..nlp import embed
from .chunk import Chunk, chunk_document
from .clean import normalize
from .loaders import load_raw_docs
from .pii import mask_pii

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _collect_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in load_raw_docs():
        doc.text = mask_pii(normalize(doc.text), mask_names=config.MASK_NAMES)
        chunks.extend(chunk_document(doc))
    return chunks


def _build_chroma(chunks: list[Chunk]) -> None:
    import chromadb

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    # rebuild from scratch for reproducibility
    try:
        client.delete_collection(config.CHROMA_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        config.CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    ids = [c.chunk_id for c in chunks]
    embeddings = embed.encode_documents([c.text for c in chunks])
    metadatas = [
        {
            "doc_id": c.doc_id,
            "source": c.source,
            "category": c.category,
            "company": c.company or "",  # Chroma metadata can't be None
        }
        for c in chunks
    ]
    documents = [c.text for c in chunks]

    # add in batches to stay well under Chroma's max batch size
    B = 128
    for i in range(0, len(ids), B):
        collection.add(
            ids=ids[i : i + B],
            embeddings=embeddings[i : i + B],
            documents=documents[i : i + B],
            metadatas=metadatas[i : i + B],
        )


def _build_bm25(chunks: list[Chunk]) -> None:
    from rank_bm25 import BM25Okapi

    tokenized = [_tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    payload = {
        "bm25": bm25,
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "source": c.source,
                "category": c.category,
                "company": c.company or "",
                "text": c.text,
            }
            for c in chunks
        ],
    }
    with config.BM25_PATH.open("wb") as fh:
        pickle.dump(payload, fh)


def build() -> int:
    chunks = _collect_chunks()
    if not chunks:
        print(f"No documents found under {config.RAW_DIR}. Add files and re-run.")
        return 0
    print(f"Collected {len(chunks)} chunks from raw documents.")
    _build_chroma(chunks)
    print(f"Chroma collection '{config.CHROMA_COLLECTION}' built at {config.CHROMA_DIR}.")
    _build_bm25(chunks)
    print(f"BM25 index written to {config.BM25_PATH}.")
    return len(chunks)


if __name__ == "__main__":
    build()
