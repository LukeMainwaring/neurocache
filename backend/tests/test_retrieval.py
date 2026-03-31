"""Tests for retrieval functions: Reciprocal Rank Fusion and content type boosting."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from neurocache.services.knowledge_source.retrieval import (
    CONTENT_TYPE_BOOSTS,
    RRF_K,
    apply_content_type_boost,
    reciprocal_rank_fusion,
)


def _make_chunk(chunk_id: int, content_type: str | None = None) -> Any:
    """Create a mock DocumentChunk with the given id and content type."""
    chunk = MagicMock()
    chunk.id = chunk_id
    if content_type is not None:
        chunk.document = SimpleNamespace(content_type=content_type)
    else:
        chunk.document = None
    return chunk


class TestReciprocalRankFusion:
    def test_single_list_produces_rrf_scores(self) -> None:
        c1 = _make_chunk(1)
        c2 = _make_chunk(2)
        semantic: list[tuple[Any, float]] = [(c1, 0.95), (c2, 0.80)]

        result = reciprocal_rank_fusion(semantic, [])

        assert len(result) == 2
        # Rank 1 gets 1/(60+1), rank 2 gets 1/(60+2)
        assert result[0][0].id == 1
        assert result[0][1] == pytest.approx(1 / (RRF_K + 1))
        assert result[1][1] == pytest.approx(1 / (RRF_K + 2))

    def test_overlapping_chunks_get_summed_scores(self) -> None:
        shared = _make_chunk(1)
        semantic_only = _make_chunk(2)
        keyword_only = _make_chunk(3)

        semantic: list[tuple[Any, float]] = [(shared, 0.9), (semantic_only, 0.8)]
        keyword: list[tuple[Any, float]] = [(shared, 5.0), (keyword_only, 3.0)]

        result = reciprocal_rank_fusion(semantic, keyword)
        scores = {r[0].id: r[1] for r in result}

        # Shared chunk appears in both lists at rank 1 -> summed score
        expected_shared = 1 / (RRF_K + 1) + 1 / (RRF_K + 1)
        assert scores[1] == pytest.approx(expected_shared)
        # Non-overlapping chunks get single-list scores
        assert scores[2] == pytest.approx(1 / (RRF_K + 2))
        assert scores[3] == pytest.approx(1 / (RRF_K + 2))
        # Shared chunk ranks highest
        assert result[0][0].id == 1

    def test_empty_inputs_return_empty(self) -> None:
        assert reciprocal_rank_fusion([], []) == []

    def test_original_scores_are_ignored(self) -> None:
        """RRF uses rank position, not the original similarity/relevance scores."""
        c1 = _make_chunk(1)
        c2 = _make_chunk(2)

        # c2 has higher original score but lower rank
        result_a: list[tuple[Any, float]] = reciprocal_rank_fusion([(c1, 0.99), (c2, 0.01)], [])
        result_b: list[tuple[Any, float]] = reciprocal_rank_fusion([(c1, 0.01), (c2, 0.99)], [])

        # Same rank order -> same RRF scores regardless of original scores
        assert result_a[0][0].id == result_b[0][0].id == 1


class TestApplyContentTypeBoost:
    def test_personal_notes_rank_above_book_sources(self) -> None:
        book_chunk = _make_chunk(1, "book_source")
        note_chunk = _make_chunk(2, "personal_note")

        # Both start with same similarity, but note gets boosted above book
        chunks: list[tuple[Any, float]] = [(book_chunk, 0.85), (note_chunk, 0.85)]
        result = apply_content_type_boost(chunks)

        assert result[0][0].id == 2  # personal note ranks first
        assert result[0][1] == pytest.approx(0.85 * CONTENT_TYPE_BOOSTS["personal_note"])
        assert result[1][1] == pytest.approx(0.85 * CONTENT_TYPE_BOOSTS["book_source"])

    def test_scores_capped_at_one(self) -> None:
        chunk = _make_chunk(1, "personal_note")
        result: list[tuple[Any, float]] = apply_content_type_boost([(chunk, 0.99)])

        # 0.99 * 1.04 = 1.0296 -> capped at 1.0
        assert result[0][1] == 1.0

    def test_missing_document_gets_no_boost(self) -> None:
        chunk = _make_chunk(1, content_type=None)
        result: list[tuple[Any, float]] = apply_content_type_boost([(chunk, 0.80)])

        assert result[0][1] == pytest.approx(0.80)
