from datetime import datetime, timezone

from indexing import SiteIndexer


def test_chunking_overlap(tmp_path):
    indexer = SiteIndexer(tmp_path, chunk_size=4, chunk_overlap=1, embedding_dim=32)
    text = " ".join([f"token{i}" for i in range(10)])
    chunks = indexer.chunk_content(text)

    assert len(chunks) == 3
    first_tokens = chunks[0].split()
    second_tokens = chunks[1].split()
    third_tokens = chunks[2].split()

    assert first_tokens[-1] == second_tokens[0]
    assert second_tokens[-1] == third_tokens[0]


def test_index_persistence_and_metadata(tmp_path):
    index_dir = tmp_path / "index"
    indexer = SiteIndexer(index_dir, chunk_size=3, chunk_overlap=1, embedding_dim=32)

    indexer.index_page(
        "https://example.com/a",
        "alpha beta gamma delta epsilon",
        metadata={"source": "unit-test"},
    )

    assert indexer.embeddings.shape[0] == len(indexer.metadata) > 0
    assert indexer.metadata[0]["source"] == "unit-test"

    reloaded = SiteIndexer(index_dir, chunk_size=3, chunk_overlap=1, embedding_dim=32)

    assert reloaded.embeddings.shape == indexer.embeddings.shape
    assert reloaded.metadata[0]["url"] == "https://example.com/a"


def test_semantic_query_with_filters(tmp_path):
    indexer = SiteIndexer(tmp_path, chunk_size=20, chunk_overlap=5, embedding_dim=64)

    ts_old = datetime(2023, 1, 1, tzinfo=timezone.utc)
    ts_new = datetime(2024, 6, 1, tzinfo=timezone.utc)

    indexer.index_page(
        "https://code.example.com/python",
        "Python is a programming language used for data science and automation.",
        timestamp=ts_old,
    )
    indexer.index_page(
        "https://garden.io/guide",
        "Gardening tips for planting roses and caring for soil and plants.",
        timestamp=ts_new,
    )

    results = indexer.query("python programming language", top_k=2)
    assert results
    assert results[0].url.endswith("/python")

    domain_results = indexer.query("gardening soil", domain="garden.io")
    assert domain_results
    assert all("garden.io" in item.domain for item in domain_results if item.domain)

    filtered_recent = indexer.query("gardening", start_date="2024-01-01")
    assert filtered_recent
    assert filtered_recent[0].url == "https://garden.io/guide"

    filtered_past = indexer.query("python", end_date="2023-12-31")
    assert filtered_past
    assert filtered_past[0].url.endswith("/python")
