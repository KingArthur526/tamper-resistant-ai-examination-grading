import pytest
from types import SimpleNamespace
from app.ml.grading.scoring_engine import scoring_engine

def test_or_group_selection_best_attempted():
    group = SimpleNamespace(id="grp-1", name="Group 3", group_type="OR", max_selectable_marks=10.0)
    
    eval_3a = {"id": "e1", "group_id": "grp-1", "question_number": "3A", "ai_score": 8.5, "is_or_group_selected": False}
    eval_3b = {"id": "e2", "group_id": "grp-1", "question_number": "3B", "ai_score": 5.0, "is_or_group_selected": False}

    evals = [eval_3a, eval_3b]
    resolved = scoring_engine.resolve_or_question_groups(evals, [group], policy="best_attempted")

    assert eval_3a["is_or_group_selected"] is True
    assert eval_3b["is_or_group_selected"] is False
