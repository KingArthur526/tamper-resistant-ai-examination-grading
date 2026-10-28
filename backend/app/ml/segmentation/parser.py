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

    # Question "header" lines such as "5) Explain recursion with an example." Handwritten
    # question numbers are often misread by OCR ("3)" -> "32"), so the verb is the anchor and
    # the number is only a hint that gets repaired using the expected question sequence.
    # The verb is followed by (?![a-z]) rather than \\b because OCR turns spaces into "_".
    HEADER_VERBS = (
        "explain|what|define|describe|write|differentiate|discuss|list|state|compare|derive|"
        "prove|give|draw|why|how|distinguish|illustrate|evaluate|find|solve|calculate|show|"
        "outline|justify|mention|enumerate|elaborate|identify|summari[sz]e|trace|implement"
    )
    HEADER_PATTERN = re.compile(
        r"(?im)^[ \t]*(?P<num>[^\sA-Za-z]{0,4}|[A-Za-z0-9]{1,3})[ \t]*[\.\:\)\-]?[ \t]*"
        r"(?=(?:" + HEADER_VERBS + r")(?![a-z]))"
    )

    @staticmethod
    def _norm(q) -> str:
        return str(q).strip().lower().replace("(", "").replace(")", "").replace(".", "")

    def _find_headers(self, text: str):
        out = []
        for m in self.HEADER_PATTERN.finditer(text):
            line_end = text.find("\n", m.end())
            line_end = len(text) if line_end == -1 else line_end
            digits = re.sub(r"\D", "", m.group("num") or "")
            out.append({
                "raw_q": digits or None,
                "pattern_idx": -1,
                "start": m.start(),
                "end": line_end,            # skip the question line itself, keep the answer
                "header": True,
            })
        return out

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

        # Prefer question-header lines when the sheet clearly has them. Plain "1." / "2)" markers
        # are then ignored, because they are usually sub-list items inside an answer
        # ("1. Primitive", "1. Preorder") and would overwrite the real question boundaries.
        headers = self._find_headers(cleaned_ocr)
        header_mode = len(headers) >= max(2, (len(defined_question_numbers) + 1) // 2)
        if header_mode:
            matches = headers + [m for m in matches if m["pattern_idx"] == 0]
        else:
            # Sheets where students write only "Q1.", "Q2." and then the answer (no question text):
            # when enough explicit Q-markers exist, ignore plain "1." / "2)" markers, which are
            # sub-list items inside an answer ("1. Atomicity", "2. Consistency") and would
            # otherwise overwrite the real question boundaries.
            q_marks = [m for m in matches if m["pattern_idx"] == 0 and m["raw_q"]]
            if len(q_marks) >= max(2, (len(defined_question_numbers) + 1) // 2):
                matches = q_marks

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
        defined_norm = [self._norm(q) for q in defined_question_numbers]
        assigned: set = set()
        last_idx = -1
        for idx, current in enumerate(dedup_matches):
            raw_q = current["raw_q"]
            content_start = current["end"]
            content_end = dedup_matches[idx + 1]["start"] if idx + 1 < len(dedup_matches) else len(cleaned_ocr)
            extracted_text = cleaned_ocr[content_start:content_end].strip()
            if header_mode:
                # drop a leading "Ans", "Ans:", "Ans =" label
                extracted_text = re.sub(r"(?i)^\s*ans(?:wer)?\s*[:=\-\.]*\s*", "", extracted_text)

            matched_idx = None
            if raw_q:
                # exact match first (so "1" never matches "10")
                if raw_q in defined_norm:
                    matched_idx = defined_norm.index(raw_q)
                else:
                    for di, nd in enumerate(defined_norm):
                        if raw_q.isdigit() and nd.isdigit():
                            continue
                        if nd in raw_q or raw_q in nd:
                            matched_idx = di
                            break

            if header_mode:
                # Sequence repair: a number that is unknown, repeated or out of order was most
                # likely misread, so use the next question that has not been seen yet.
                if matched_idx is None or matched_idx in assigned or matched_idx < last_idx:
                    nxt = next((i for i in range(last_idx + 1, len(defined_norm)) if i not in assigned), None)
                    matched_idx = nxt
            elif matched_idx is None and idx < len(defined_question_numbers):
                # marker without a number (e.g. "Question:") -> idx-th question
                matched_idx = idx

            if matched_idx is not None:
                assigned.add(matched_idx)
                last_idx = max(last_idx, matched_idx)
                target_key = defined_norm[matched_idx]
            else:
                target_key = raw_q or f"q_{idx+1}"

            results[target_key] = {
                "text": extracted_text,
                "confidence": 0.90 if extracted_text else 0.40,
                "attempted": len(extracted_text) > 0
            }

        return results

segmenter = QuestionSegmenter()

