from app.services.vector_store import ChromaVectorStore, InMemoryVectorStore


def test_inmemory_vector_store_search():
    store = InMemoryVectorStore()
    store.bulk_load([("doc-1", "hello world"), ("doc-2", "world report")])

    results = store.search("world", top_k=2)

    assert len(results) == 2
    assert results[0].doc_id in {"doc-1", "doc-2"}


def test_chroma_vector_store_roundtrip(tmp_path):
    store = ChromaVectorStore(persist_directory=str(tmp_path))
    store.bulk_load([("doc-1", "financial report"), ("doc-2", "security incident")])

    results = store.search("financial", top_k=1)

    assert len(results) == 1
    assert results[0].doc_id == "doc-1"
