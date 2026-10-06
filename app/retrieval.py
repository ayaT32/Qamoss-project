"""
Core retrieval + verification logic.

Hard safety rule (enforced here, not just in a prompt):
if nothing relevant is retrieved, the LLM is never called and the
function returns "not_found" directly. The LLM only ever classifies
the difference between two texts that retrieval already found —
it never produces a standalone claim.
"""
from dataclasses import dataclass

from rapidfuzz import fuzz

from app.build_index import build_index
from app.normalize import normalize_arabic
from app.llm import classify_difference

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        _collection = build_index()
    return _collection


@dataclass
class SearchResult:
    text: str
    source: str
    reference: str
    narrator: str
    grade: str
    url: str
    score: float


def _metadatas_to_results(metadatas: list[dict], distances: list[float]) -> list[SearchResult]:
    results = []
    for m, d in zip(metadatas, distances):
        results.append(SearchResult(
            text=m.get("text", ""),
            source=m.get("source", ""),
            reference=m.get("reference", ""),
            narrator=m.get("narrator", ""),
            grade=m.get("grade", ""),
            url=m.get("url", ""),
            score=1 - d,  # convert distance to a rough similarity score
        ))
    return results


def search(query: str, k: int = 5) -> list[SearchResult]:
    """باحث المصادر: returns relevant sourced chunks, no generated answer."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    norm_query = normalize_arabic(query)
    res = collection.query(query_texts=[norm_query], n_results=min(k, collection.count()))
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]
    return _metadatas_to_results(metadatas, distances)


def verify_quote(user_text: str) -> dict:
    """مدقق الاقتباسات: classify a user-submitted quote against the nearest
    indexed source. Never fabricates a reference — if nothing is retrieved,
    returns not_found without calling the LLM.
    """
    collection = get_collection()
    if collection.count() == 0:
        return {"status": "not_found", "reason": "القاعدة المرجعية فارغة"}

    norm_text = normalize_arabic(user_text)
    res = collection.query(query_texts=[norm_text], n_results=1)
    metadatas = res.get("metadatas", [[]])[0]
    if not metadatas:
        return {"status": "not_found"}

    best = metadatas[0]
    original_text = best.get("text", "")
    similarity = fuzz.ratio(norm_text, normalize_arabic(original_text))

    source_info = {
        "text": original_text,
        "source": best.get("source", ""),
        "reference": best.get("reference", ""),
        "narrator": best.get("narrator", ""),
        "grade": best.get("grade", ""),
        "url": best.get("url", ""),
    }

    if similarity >= 98:
        return {"status": "exact_match", "similarity": similarity, "source": source_info}

    if similarity >= 85:
        # Only here is the LLM invoked — to classify a difference between
        # two texts retrieval already found, never to generate new content.
        try:
            difference_type = classify_difference(user_text, original_text)
        except RuntimeError as e:
            # No Groq key configured — degrade gracefully instead of crashing
            difference_type = f"(تعذر التصنيف الآلي: {e})"
        return {
            "status": "minor_difference",
            "difference_type": difference_type,
            "similarity": similarity,
            "source": source_info,
        }

    if similarity >= 60:
        return {"status": "mismatch", "similarity": similarity, "source": source_info}

    return {"status": "not_found", "similarity": similarity}
