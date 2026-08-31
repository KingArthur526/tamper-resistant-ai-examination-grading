import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.ml.embeddings.sbert_engine import embedding_engine

class SemanticSimilarityMatcher:
    """
    Computes dense cosine similarity between student answers and rubric concepts.
    Extracts verbatim evidence spans and identifies missing conceptual aspects.
    """

    def compute_cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.clip(dot / (norm_a * norm_b), 0.0, 1.0))

    def split_into_sentences_and_phrases(self, text: str) -> List[Dict[str, Any]]:
        units = []
        sentence_spans = []
        # Match sentences ending with punctuation or newline
        for m in re.finditer(r'[^.!?\n]+[.!?\n]?', text):
            span_text = m.group(0).strip()
            if len(span_text) > 4:
                sentence_spans.append({
                    "text": span_text,
                    "start": m.start(),
                    "end": m.end()
                })

        if not sentence_spans and text.strip():
            sentence_spans.append({
                "text": text.strip(),
                "start": 0,
                "end": len(text)
            })

        return sentence_spans

    def match_concept(
        self,
        student_text: str,
        concept_reference_text: str,
        concept_name: str,
        keywords: Optional[List[str]] = None,
        negative_indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not student_text.strip():
            return {
                "similarity_score": 0.0,
                "matched_evidence": None,
                "matched_span_indices": [0, 0],
                "missing_evidence": self._extract_key_aspects(concept_reference_text),
                "is_misconception": False
            }

        # 1. Overall similarity
        overall_emb = embedding_engine.encode([student_text, concept_reference_text])
        overall_sim = self.compute_cosine_similarity(overall_emb[0], overall_emb[1])

        # 2. Sentence-level granular alignment to locate best evidence
        units = self.split_into_sentences_and_phrases(student_text)
        unit_texts = [u["text"] for u in units]
        unit_embs = embedding_engine.encode(unit_texts)
        concept_emb = overall_emb[1]

        best_sim = 0.0
        best_evidence = None
        best_span = [0, 0]

        for u, u_emb in zip(units, unit_embs):
            sim = self.compute_cosine_similarity(u_emb, concept_emb)
            if sim > best_sim:
                best_sim = sim
                best_evidence = u["text"]
                best_span = [u["start"], u["end"]]

        effective_similarity = float(max(best_sim, overall_sim * 0.95))

        # Check for keyword matches / synonyms boost
        if keywords:
            keyword_hits = sum(1 for kw in keywords if kw.lower() in student_text.lower())
            if keyword_hits > 0:
                boost = min(0.08, keyword_hits * 0.03)
                effective_similarity = min(1.0, effective_similarity + boost)

        # Check for negative misconceptions / contradictory statements
        has_misconception = False
        if negative_indicators:
            for neg in negative_indicators:
                if neg.lower() in student_text.lower():
                    has_misconception = True
                    effective_similarity = max(0.0, effective_similarity - 0.25)
                    break

        effective_similarity = round(float(effective_similarity), 4)

        # Extract missing aspects if similarity is partial or missing
        missing_aspects = []
        if effective_similarity < 0.78:
            missing_aspects = self._detect_missing_aspects(concept_reference_text, student_text)

        return {
            "similarity_score": effective_similarity,
            "matched_evidence": best_evidence if effective_similarity >= 0.40 else None,
            "matched_span_indices": best_span if effective_similarity >= 0.40 else [0, 0],
            "missing_evidence": missing_aspects,
            "is_misconception": has_misconception
        }

    def _extract_key_aspects(self, reference_text: str) -> List[str]:
        parts = re.split(r'[,;]|\band\b', reference_text)
        clean_parts = [p.strip() for p in parts if len(p.strip().split()) >= 2]
        return clean_parts[:3] if clean_parts else [reference_text[:60]]

    def _detect_missing_aspects(self, reference_text: str, student_text: str) -> List[str]:
        aspects = self._extract_key_aspects(reference_text)
        missing = []
        for asp in aspects:
            asp_emb = embedding_engine.encode(asp)
            stud_emb = embedding_engine.encode(student_text)
            sim = self.compute_cosine_similarity(asp_emb[0], stud_emb[0])
            if sim < 0.60:
                missing.append(asp)
        return missing if missing else aspects[:1]

similarity_matcher = SemanticSimilarityMatcher()
