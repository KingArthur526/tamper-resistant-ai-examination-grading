import pytest
from app.services.exam_service import exam_service
from app.schemas.schemas import RubricConceptCreate

def test_rubric_sum_validation_success():
    concepts = [
        RubricConceptCreate(concept_code="C1", name="Concept 1", reference_text="Ref 1", max_marks=4.0),
        RubricConceptCreate(concept_code="C2", name="Concept 2", reference_text="Ref 2", max_marks=6.0)
    ]
    val = exam_service.validate_rubric(10.0, concepts)
    assert val["is_valid"] is True
    assert val["difference"] == 0.0

def test_rubric_sum_validation_mismatch():
    concepts = [
        RubricConceptCreate(concept_code="C1", name="Concept 1", reference_text="Ref 1", max_marks=3.0),
        RubricConceptCreate(concept_code="C2", name="Concept 2", reference_text="Ref 2", max_marks=4.0)
    ]
    val = exam_service.validate_rubric(10.0, concepts)
    assert val["is_valid"] is False
    assert val["concepts_total_marks"] == 7.0
    assert val["difference"] == 3.0
