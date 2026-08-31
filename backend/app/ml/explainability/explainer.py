from typing import Dict, Any, List

class GroundedExplanationGenerator:
    """
    Generates factual, traceable, grounded natural-language explanations for evaluation marks.
    Strictly derives explanations from the structured evaluation data, never fabricating claims.
    """

    def generate_concept_explanation(self, concept_eval: Dict[str, Any]) -> str:
        code = concept_eval.get("concept_code", "")
        name = concept_eval.get("concept_name", "")
        status = concept_eval.get("semantic_status", "")
        awarded = concept_eval.get("awarded_marks", 0.0)
        max_m = concept_eval.get("max_marks", 0.0)
        sim = concept_eval.get("similarity_score", 0.0)
        evidence = concept_eval.get("matched_evidence")
        missing = concept_eval.get("missing_evidence", [])

        if status == "FULL_MATCH":
            if evidence:
                return f"The response explicitly identifies and explains {name} with strong semantic alignment (similarity {sim:.2f}). Matched evidence: '{evidence}'. Full credit of {awarded}/{max_m} marks awarded."
            return f"The response demonstrates comprehensive understanding of {name} (similarity {sim:.2f}), satisfying all rubric requirements ({awarded}/{max_m} marks)."

        elif status == "PARTIAL_MATCH":
            missing_str = ", ".join([f"'{m}'" for m in missing]) if missing else "further technical elaboration"
            if evidence:
                return f"The answer partially covers {name} based on evidence '{evidence}' (similarity {sim:.2f}), but does not adequately explain {missing_str}. Partial credit of {awarded}/{max_m} marks awarded."
            return f"The student's answer references aspects of {name} but lacks required depth regarding {missing_str}. Partial credit of {awarded}/{max_m} marks awarded."

        else: # MISSING
            missing_str = ", ".join([f"'{m}'" for m in missing]) if missing else name
            return f"No sufficient evidence found in the student's submission addressing {name} (similarity {sim:.2f} < threshold). Expected concept regarding {missing_str}. 0/{max_m} marks awarded."

    def assemble_why_this_score(
        self,
        question_evaluation: Any,
        concepts_data: List[Dict[str, Any]],
        semantic_model: str,
        similarity_method: str,
        scoring_policy: str,
        ocr_confidence: float = 0.95
    ) -> Dict[str, Any]:
        breakdown = []
        sum_terms = []

        for c in concepts_data:
            expl = self.generate_concept_explanation(c)
            c["explanation"] = expl
            breakdown.append({
                "concept_code": c["concept_code"],
                "concept_name": c["concept_name"],
                "max_marks": c["max_marks"],
                "awarded_marks": c["awarded_marks"],
                "similarity_score": c["similarity_score"],
                "status": c["semantic_status"],
                "matched_evidence": c.get("matched_evidence"),
                "missing_evidence": c.get("missing_evidence", []),
                "explanation": expl
            })
            sum_terms.append(f"{c['awarded_marks']}")

        total_awarded = question_evaluation.ai_score
        total_max = question_evaluation.question.max_marks if hasattr(question_evaluation, "question") else 10.0
        
        spelling_penalty = getattr(question_evaluation, "spelling_penalty_deducted", 0.0) or 0.0
        spelling_score = getattr(question_evaluation, "spelling_score", 100.0) or 100.0
        spelling_errors = getattr(question_evaluation, "spelling_errors", []) or []

        if spelling_penalty > 0:
            formula = f"{' + '.join(sum_terms)} - {spelling_penalty:.2f} (Spelling Penalty) = {total_awarded} / {total_max}"
        else:
            formula = f"{' + '.join(sum_terms)} = {total_awarded} / {total_max}"

        return {
            "question_evaluation_id": question_evaluation.id,
            "question_number": question_evaluation.question.question_number if hasattr(question_evaluation, "question") else "1",
            "question_text": question_evaluation.question.question_text if hasattr(question_evaluation, "question") else "",
            "question_max_marks": float(total_max),
            "ai_score": float(question_evaluation.ai_score),
            "teacher_final_score": float(question_evaluation.teacher_final_score),
            "is_overridden": bool(question_evaluation.is_overridden),
            "confidence_level": question_evaluation.confidence_level,
            "ocr_confidence": float(ocr_confidence),
            "semantic_model": semantic_model,
            "similarity_method": similarity_method,
            "scoring_policy": scoring_policy,
            "spelling_score": float(spelling_score),
            "spelling_penalty_deducted": float(spelling_penalty),
            "spelling_errors": spelling_errors,
            "concepts": concepts_data,
            "calculation_formula": formula,
            "calculation_breakdown": breakdown,
            "evaluation_hash": question_evaluation.evaluation_hash,
            "timestamp": question_evaluation.evaluated_at
        }

explainer = GroundedExplanationGenerator()
