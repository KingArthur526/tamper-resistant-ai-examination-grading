import re
from typing import Dict, List, Any, Optional

class QuestionSegmenter:
    """
    Parses full OCR text and partitions it into individual question answers.
    Supports formats:
    - Q1, Q2, Q3, Q1(a), Q1(b), Q.1, Q.2
    - Question 1:, Question 2
    - 1., 2., 3., (1), (2)
    - Ans 1:, Ans 2:, Answer 1
    """

    PATTERNS = [
        r'(?i)(?:^|\n)\s*(?:Q(?:uestion|\.)?\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9\.]*))[\s\:\.\-]+)',
        r'(?i)(?:^|\n)\s*(?:Ans(?:wer|\.)?\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9\.]*))[\s\:\.\-]+)',
        r'(?:^|\n)\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9]*))\s*[\.\:\-\)]\s+'
    ]

    def segment_answers(self, ocr_text: str, defined_question_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        
        for q_num in defined_question_numbers:
            results[str(q_num).strip().lower()] = {
                "text": "",
                "confidence": 0.0,
                "attempted": False
            }

        matches = []
        for pattern in self.PATTERNS:
            for m in re.finditer(pattern, ocr_text):
                q_id_raw = m.group(1).strip().lower().replace("(", "").replace(")", "").replace(".", "")
                matches.append({
                    "raw_q": q_id_raw,
                    "start": m.start(),
                    "end": m.end()
                })

        matches.sort(key=lambda x: x["start"])

        dedup_matches = []
        for m in matches:
            if not dedup_matches or m["start"] >= dedup_matches[-1]["end"]:
                dedup_matches.append(m)

        if not dedup_matches:
            if len(defined_question_numbers) == 1:
                q_key = str(defined_question_numbers[0]).strip().lower()
                results[q_key] = {
                    "text": ocr_text.strip(),
                    "confidence": 0.85,
                    "attempted": len(ocr_text.strip()) > 0
                }
            return results

        for idx, current in enumerate(dedup_matches):
            q_key = current["raw_q"]
            content_start = current["end"]
            content_end = dedup_matches[idx + 1]["start"] if idx + 1 < len(dedup_matches) else len(ocr_text)
            extracted_text = ocr_text[content_start:content_end].strip()

            matched_q_num = None
            for defined_q in defined_question_numbers:
                norm_defined = str(defined_q).strip().lower().replace("(", "").replace(")", "").replace(".", "")
                if norm_defined == q_key or norm_defined in q_key or q_key in norm_defined:
                    matched_q_num = str(defined_q).strip().lower()
                    break

            if matched_q_num:
                results[matched_q_num] = {
                    "text": extracted_text,
                    "confidence": 0.92,
                    "attempted": len(extracted_text) > 0
                }
            else:
                results[q_key] = {
                    "text": extracted_text,
                    "confidence": 0.75,
                    "attempted": len(extracted_text) > 0
                }

        return results

segmenter = QuestionSegmenter()
