"""
Build (or rebuild) the local Chroma vector index from the JSON data files.

Run this once before starting the API, and again any time data/*.json changes:

    python -m app.build_index

It is also safe to call build_index() at FastAPI startup (see main.py) —
Chroma's add() is idempotent on id, so re-running just upserts.
"""
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from app.normalize import normalize_arabic

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INDEX_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "marja_sources"
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-m3")


def load_chunks() -> list[dict]:
    chunks = []
    for filename in ("quran_sample.json", "hadith_sample.json"):
        path = DATA_DIR / filename
        if not path.exists():
            print(f"[build_index] WARNING: {path} not found, skipping.")
            continue
        with open(path, encoding="utf-8") as f:
            chunks.extend(json.load(f))
    return chunks


def build_index() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=ef)

    chunks = load_chunks()
    if not chunks:
        print("[build_index] No chunks found — index will be empty.")
        return collection

    ids, documents, metadatas = [], [], []
    for c in chunks:
        ids.append(c["id"])
        documents.append(normalize_arabic(c["text"]))
        # Chroma metadata values must be str/int/float/bool/None — flatten safely
        metadatas.append({
            "text": c["text"],
            "source": c.get("source", ""),
            "reference": c.get("reference", ""),
            "narrator": c.get("narrator") or "",
            "grade": c.get("grade") or "",
            "url": c.get("url", ""),
            "license": c.get("license", ""),
        })

    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )
    print(f"[build_index] Indexed {len(ids)} chunks into '{COLLECTION_NAME}'.")
    return collection


if __name__ == "__main__":
    build_index()
