import re
from typing import Dict, List, Any, Optional

class QuestionSegmenter:
    """
    Parses full OCR text and partitions it into individual question answers.
    Supports diverse handwritten & printed formats:
    - Q1, Q2, Q3, Q1(a), Q1(b), Q.1, Q.2, Q - 1, Question 1, Question 1:
    - Ans 1:, Ans 2:, Answer 1, Ans: 1, A1:
    - 1., 2., 3., (1), (2), 1), 1 -, 1 :
    - Handles OCR artifacts like 'Question _', 'Q.', 'Part 1'
    """

    PATTERNS = [
        r'(?i)(?:^|\n)\s*(?:Q(?:uestion|\.)?\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9\.]*))[\s\:\.\-_]+)',
        r'(?i)(?:^|\n)\s*(?:Ans(?:wer|\.)?\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9\.]*))[\s\:\.\-_]+)',
        r'(?:^|\n)\s*([0-9]+(?:\([a-z0-9]+\)|[a-z0-9]*))\s*[\.\:\-\)]\s+',
        r'(?i)(?:^|\n)\s*(?:Q(?:uestion|\.)?\s*[\:\.\-_]+)',  # Generic "Question:" or "Question _"
        r'(?i)(?:^|\n)\s*(?:Ans(?:wer|\.)?\s*[\:\.\-_]+)'
    ]

    def segment_answers(self, ocr_text: str, defined_question_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        cleaned_ocr = ocr_text.strip()
        
        for q_num in defined_question_numbers:
            results[str(q_num).strip().lower()] = {
                "text": "",
                "confidence": 0.0,
                "attempted": False
            }

        if not cleaned_ocr:
            return results

        matches = []
        for p_idx, pattern in enumerate(self.PATTERNS):
            for m in re.finditer(pattern, cleaned_ocr):
                group_val = m.group(1) if m.lastindex and m.lastindex >= 1 else None
                q_id_raw = group_val.strip().lower().replace("(", "").replace(")", "").replace(".", "") if group_val else None
                matches.append({
                    "raw_q": q_id_raw,
                    "pattern_idx": p_idx,
                    "start": m.start(),
                    "end": m.end()
                })

        matches.sort(key=lambda x: x["start"])

        # Deduplicate overlapping matches
        dedup_matches = []
        for m in matches:
            if not dedup_matches or m["start"] >= dedup_matches[-1]["end"]:
                dedup_matches.append(m)

        # If no explicit question markers found
        if not dedup_matches:
            if len(defined_question_numbers) == 1:
                q_key = str(defined_question_numbers[0]).strip().lower()
                results[q_key] = {
                    "text": cleaned_ocr,
                    "confidence": 0.88,
                    "attempted": len(cleaned_ocr) > 0
                }
            elif len(defined_question_numbers) > 1:
                # Divide paragraphs across questions in sequence
                paras = [p.strip() for p in cleaned_ocr.split("\n\n") if p.strip()]
                if not paras:
                    paras = [p.strip() for p in cleaned_ocr.splitlines() if p.strip()]

                for idx, q_num in enumerate(defined_question_numbers):
                    q_key = str(q_num).strip().lower()
                    if idx < len(paras):
                        results[q_key] = {
                            "text": paras[idx],
                            "confidence": 0.75,
                            "attempted": True
                        }
                    else:
                        # Assign full remaining text or blank
                        results[q_key] = {
                            "text": cleaned_ocr if idx == 0 else "",
                            "confidence": 0.70 if idx == 0 else 0.0,
                            "attempted": idx == 0
                        }
            return results

        # Process found question markers
        for idx, current in enumerate(dedup_matches):
            raw_q = current["raw_q"]
            content_start = current["end"]
            content_end = dedup_matches[idx + 1]["start"] if idx + 1 < len(dedup_matches) else len(cleaned_ocr)
            extracted_text = cleaned_ocr[content_start:content_end].strip()

            matched_q_num = None
            if raw_q:
                for defined_q in defined_question_numbers:
                    norm_defined = str(defined_q).strip().lower().replace("(", "").replace(")", "").replace(".", "")
                    if norm_defined == raw_q or norm_defined in raw_q or raw_q in norm_defined:
                        matched_q_num = str(defined_q).strip().lower()
                        break

            # If marker didn't specify a question number (e.g. "Question:"), match to idx-th question
            if not matched_q_num and idx < len(defined_question_numbers):
                matched_q_num = str(defined_question_numbers[idx]).strip().lower()

            target_key = matched_q_num or raw_q or f"q_{idx+1}"
            results[target_key] = {
                "text": extracted_text,
                "confidence": 0.90 if extracted_text else 0.40,
                "attempted": len(extracted_text) > 0
            }

        return results

segmenter = QuestionSegmenter()

