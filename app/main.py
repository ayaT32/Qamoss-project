from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.retrieval import search, verify_quote

app = FastAPI(title="مرجع API", description="باحث مصادر ومدقق اقتباسات للمحتوى الإسلامي")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchQuery(BaseModel):
    query: str


class VerifyQuery(BaseModel):
    text: str


@app.post("/search")
def do_search(q: SearchQuery):
    results = search(q.query)
    return {"results": [r.__dict__ for r in results]}


@app.post("/verify")
def do_verify(q: VerifyQuery):
    return verify_quote(q.text)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve the frontend last so /search, /verify, /health take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
