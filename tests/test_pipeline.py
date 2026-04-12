from pathlib import Path

from app.categorization.pipeline import build_multi_queries, reciprocal_rank_fusion
from app.categorization.taxonomy_loader import load_taxonomy
from app.models import RetrievalCandidate


def _taxonomy():
    repo_root = Path(__file__).resolve().parents[1]
    return load_taxonomy(repo_root / "taxonomy" / "Content_Taxonomy_3.1_2.tsv")


def test_build_multi_queries_matches_reference_shape() -> None:
    queries = build_multi_queries(
        title="Best hotels in Las Vegas",
        content="Hotels, casinos, attractions, restaurants, and nightlife for visitors.",
    )
    assert len(queries) == 1
    assert queries[0].startswith("title:")
    assert " || content:" in queries[0]


def test_reciprocal_rank_fusion_merges_by_unique_id() -> None:
    per_query_results = [
        [
            RetrievalCandidate(
                unique_id=150,
                parent_id=None,
                tier1="Attractions",
                tier2="",
                tier3="",
                tier4="",
                path="Attractions",
                description="travel sights",
                faiss_score=0.9,
            ),
            RetrievalCandidate(
                unique_id=151,
                parent_id=150,
                tier1="Attractions",
                tier2="Amusement and Theme Parks",
                tier3="",
                tier4="",
                path="Attractions > Amusement and Theme Parks",
                description="theme parks",
                faiss_score=0.8,
            ),
        ],
        [
            RetrievalCandidate(
                unique_id=150,
                parent_id=None,
                tier1="Attractions",
                tier2="",
                tier3="",
                tier4="",
                path="Attractions",
                description="travel sights",
                faiss_score=0.85,
            ),
        ],
    ]

    fused = reciprocal_rank_fusion(per_query_results, final_top_k=5)
    assert fused[0].unique_id == 150
    assert fused[0].fused_score > 0


def test_retrieval_candidate_scores_remain_raw() -> None:
    candidate = RetrievalCandidate(
        unique_id=150,
        parent_id=None,
        tier1="Attractions",
        tier2="",
        tier3="",
        tier4="",
        path="Attractions",
        description="travel sights",
        rerank_score=-1.23456789,
    )
    assert round(candidate.rerank_score, 6) == -1.234568


def test_load_taxonomy_reads_real_tsv() -> None:
    entries = _taxonomy()
    assert entries
    assert entries[0].unique_id == 150
    assert entries[0].path == "Attractions"
    assert entries[1].parent_id == 150
