import pytest
from types import SimpleNamespace
from app.ml.grading.scoring_engine import scoring_engine

def test_concept_full_match_and_partial_match():
    concept = SimpleNamespace(
        id="c1",
        concept_code="C1",
        name="Network Layer Routing",
        description="Logical addressing and packet routing.",
        reference_text="The Network layer provides logical IP addressing and packet routing across networks.",
        max_marks=2.0,
        keywords=["IP address", "routing", "packets"],
        negative_indicators=[]
    )

    # 1. Full match student answer
    student_full = "The network layer is responsible for logical addressing using IP addresses and routing packets across networks."
    res_full = scoring_engine.evaluate_concept(concept, student_full, full_match_threshold=0.75, partial_match_threshold=0.50)
    assert res_full["semantic_status"] == "FULL_MATCH"
    assert res_full["awarded_marks"] == 2.0
    assert res_full["matched_evidence"] is not None

    # 2. Missing concept student answer
    student_missing = "The CPU executes assembly instructions in the arithmetic logic unit."
    res_missing = scoring_engine.evaluate_concept(concept, student_missing, full_match_threshold=0.75, partial_match_threshold=0.50)
    assert res_missing["semantic_status"] == "MISSING"
    assert res_missing["awarded_marks"] == 0.0
