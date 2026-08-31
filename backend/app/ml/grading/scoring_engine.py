from typing import List, Dict, Any, Optional
from app.ml.similarity.matcher import similarity_matcher
from app.ml.embeddings.sbert_engine import embedding_engine

from app.ml.grading.spelling_engine import spelling_engine

class DeterministicScoringEngine:
    """
    Applies deterministic scoring rules to convert semantic similarity evidence into marks.
    Enforces strict mathematical bounds, rubric sum invariants, spelling checks, and OR-question logic.
    """

    def evaluate_concept(
        self,
        concept: Any,
        student_text: str,
        full_match_threshold: float = 0.78,
        partial_match_threshold: float = 0.52
    ) -> Dict[str, Any]:
        """
        Evaluates a single concept for a student answer.
        Returns structured concept score and evidence.
        """
        match_res = similarity_matcher.match_concept(
            student_text=student_text,
            concept_reference_text=concept.reference_text,
            concept_name=concept.name,
            keywords=concept.keywords if hasattr(concept, "keywords") else [],
            negative_indicators=concept.negative_indicators if hasattr(concept, "negative_indicators") else []
        )

        sim = match_res["similarity_score"]
        max_marks = float(concept.max_marks)

        # Apply configurable threshold rules
        if sim >= full_match_threshold:
            status = "FULL_MATCH"
            awarded = max_marks
        elif sim >= partial_match_threshold:
            status = "PARTIAL_MATCH"
            # Deterministic proportional partial marks rounded to 0.5 step or 2 decimals
            ratio = (sim - partial_match_threshold) / (full_match_threshold - partial_match_threshold)
            partial_score = max_marks * (0.5 + 0.45 * ratio)
            awarded = round(min(max_marks, max(0.5, partial_score)), 2)
        else:
            status = "MISSING"
            awarded = 0.0

        # Misconception penalty if detected
        if match_res.get("is_misconception"):
            awarded = max(0.0, awarded - round(max_marks * 0.5, 2))

        # Confidence calculation
        confidence = 0.95 if status == "FULL_MATCH" else (0.85 if status == "PARTIAL_MATCH" else 0.90)
        if 0.50 <= sim <= 0.55 or 0.75 <= sim <= 0.80:
            confidence = 0.72 # Borderline similarity

        return {
            "rubric_concept_id": concept.id,
            "concept_code": concept.concept_code,
            "concept_name": concept.name,
            "concept_description": concept.description,
            "reference_text": concept.reference_text,
            "similarity_score": sim,
            "semantic_status": status,
            "awarded_marks": awarded,
            "max_marks": max_marks,
            "matched_evidence": match_res["matched_evidence"],
            "matched_span_indices": match_res["matched_span_indices"],
            "missing_evidence": match_res["missing_evidence"],
            "confidence_score": confidence,
            "model_name": embedding_engine.active_engine_name,
            "scoring_policy": f"Thresholds(Full>={full_match_threshold}, Partial>={partial_match_threshold})"
        }

    def evaluate_question(
        self,
        question: Any,
        student_text: str,
        ocr_confidence: float = 0.95,
        full_match_threshold: float = 0.78,
        partial_match_threshold: float = 0.52,
        enable_spelling: bool = True,
        spelling_deduction_per_error: float = 0.25,
        spelling_max_penalty: float = 1.0
    ) -> Dict[str, Any]:
        """
        Evaluates all concepts for a question, analyzes spelling accuracy, and sums marks.
        """
        concept_results = []
        total_awarded = 0.0
        total_max = float(question.max_marks)

        # Collect keywords across all concepts to whitelist valid technical terms
        domain_keywords = []
        for concept in question.rubric_concepts:
            if hasattr(concept, "keywords") and concept.keywords:
                domain_keywords.extend(concept.keywords)

        for concept in question.rubric_concepts:
            c_res = self.evaluate_concept(
                concept=concept,
                student_text=student_text,
                full_match_threshold=full_match_threshold,
                partial_match_threshold=partial_match_threshold
            )
            concept_results.append(c_res)
            total_awarded += c_res["awarded_marks"]

        raw_concept_score = round(min(total_max, max(0.0, total_awarded)), 2)

        # Spelling Evaluation
        spelling_res = spelling_engine.analyze_spelling(
            text=student_text,
            domain_keywords=domain_keywords,
            deduction_per_error=spelling_deduction_per_error,
            max_penalty=spelling_max_penalty
        ) if enable_spelling else {
            "total_words": 0,
            "error_count": 0,
            "accuracy_percentage": 100.0,
            "penalty_deducted": 0.0,
            "errors": []
        }

        spelling_penalty = spelling_res["penalty_deducted"]
        final_question_score = round(max(0.0, raw_concept_score - spelling_penalty), 2)

        # Determine overall evaluation confidence
        min_concept_conf = min([c["confidence_score"] for c in concept_results]) if concept_results else 1.0
        needs_review = False
        review_reasons = []

        if ocr_confidence < 0.70:
            needs_review = True
            review_reasons.append(f"Low OCR confidence ({ocr_confidence*100:.1f}%)")
        if min_concept_conf < 0.75:
            needs_review = True
            review_reasons.append("Borderline semantic match score")

        confidence_level = "MANUAL_REVIEW_REQUIRED" if needs_review else (
            "HIGH" if min_concept_conf >= 0.85 else "MEDIUM"
        )

        # Build calculation trace
        sum_components = [f"{c['awarded_marks']}" for c in concept_results]
        if spelling_penalty > 0:
            sum_formula = " + ".join(sum_components) + f" - {spelling_penalty:.2f} (Spelling Penalty) = {final_question_score} / {total_max}"
        else:
            sum_formula = " + ".join(sum_components) + f" = {final_question_score} / {total_max}"

        return {
            "question_id": question.id,
            "question_number": question.question_number,
            "question_text": question.question_text,
            "max_marks": total_max,
            "ai_score": final_question_score,
            "teacher_final_score": final_question_score,
            "raw_concept_score": raw_concept_score,
            "spelling_score": spelling_res["accuracy_percentage"],
            "spelling_penalty_deducted": spelling_penalty,
            "spelling_errors": spelling_res["errors"],
            "concept_evaluations": concept_results,
            "confidence_level": confidence_level,
            "needs_review": needs_review,
            "review_reasons": review_reasons,
            "calculation_trace": {
                "sum_formula": sum_formula,
                "concept_scores": [c["awarded_marks"] for c in concept_results],
                "concept_maxes": [c["max_marks"] for c in concept_results],
                "spelling_penalty": spelling_penalty,
                "spelling_accuracy": spelling_res["accuracy_percentage"],
                "total_max": total_max,
                "final_score": final_question_score
            }
        }

    def resolve_or_question_groups(
        self,
        question_evaluations: List[Dict[str, Any]],
        question_groups: List[Any],
        policy: str = "best_attempted"
    ) -> List[Dict[str, Any]]:
        """
        Applies OR-group selection logic.
        Ensures that if multiple options in an OR-group are answered, only the selected option
        contributes to the exam score according to the configured policy.
        """
        group_map = {g.id: g for g in question_groups}
        
        # Group evaluations by group_id
        grouped_evals: Dict[str, List[Dict[str, Any]]] = {}
        for qe in question_evaluations:
            gid = getattr(qe.get("question"), "group_id", None) or qe.get("group_id")
            if gid and gid in group_map:
                grouped_evals.setdefault(gid, []).append(qe)

        # Apply selection policy per group
        for gid, evals in grouped_evals.items():
            grp = group_map[gid]
            if len(evals) <= 1:
                if evals:
                    evals[0]["is_or_group_selected"] = True
                continue

            if policy == "first_attempted":
                # Select first option attempted
                for idx, e in enumerate(evals):
                    e["is_or_group_selected"] = (idx == 0)
            else: # "best_attempted"
                # Select the highest scoring option
                best_eval = max(evals, key=lambda x: x["ai_score"])
                for e in evals:
                    e["is_or_group_selected"] = (e == best_eval)

        return question_evaluations

scoring_engine = DeterministicScoringEngine()
