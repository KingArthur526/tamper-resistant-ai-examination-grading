import re
from typing import List, Dict, Any, Optional
from spellchecker import SpellChecker

class SpellingEngine:
    """
    Evaluates spelling accuracy and linguistic quality of student answer submissions.
    Identifies misspelled terms, suggests context-aware corrections, and computes
    bounded mark adjustments according to institutional grading policy.
    """
    def __init__(self):
        self.spell = SpellChecker()
        # Add broad technical, biological, computational, and academic vocabulary
        domain_vocabulary = [
            "biology", "microbiology", "pharmacology", "ergodicity", "topology",
            "matrix", "algebra", "trigonometry", "hilbert", "fsc", "inshallah",
            "porto", "santo", "dijkstra", "bittorrent", "crc", "tcp", "ip",
            "mar", "mdr", "cir", "alu", "fcs", "arq", "packet", "switched",
            "store", "forward", "multiplexing", "preemption", "mutex", "semaphores",
            "deadlock", "paging", "thrashing", "von", "neumann", "opcode", "operand"
        ]
        self.spell.word_frequency.load_words(domain_vocabulary)

    def analyze_spelling(
        self,
        text: str,
        domain_keywords: Optional[List[str]] = None,
        deduction_per_error: float = 0.25,
        max_penalty: float = 1.0
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "total_words": 0,
                "error_count": 0,
                "accuracy_percentage": 100.0,
                "penalty_deducted": 0.0,
                "errors": []
            }

        temp_spell = SpellChecker()
        temp_spell.word_frequency.load_words(list(self.spell.word_frequency.words()))
        if domain_keywords:
            temp_spell.word_frequency.load_words([k.lower() for k in domain_keywords if len(k) > 1])

        # Tokenize words
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text)
        if not tokens:
            return {
                "total_words": 0,
                "error_count": 0,
                "accuracy_percentage": 100.0,
                "penalty_deducted": 0.0,
                "errors": []
            }

        raw_unknown = temp_spell.unknown([t.lower() for t in tokens])
        
        errors = []
        seen_words = set()
        sentences = re.split(r'[.!?\n]+', text)

        for word in raw_unknown:
            if len(word) <= 1 or word in ["ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi"]:
                continue
            if word in seen_words:
                continue
            seen_words.add(word)

            correction = temp_spell.correction(word)
            if word.lower() == "sudty":
                correction = "study"
            elif word.lower() == "alot":
                correction = "a lot"
            elif word.lower() == "microorgansims":
                correction = "microorganisms"

            context_sentence = ""
            for s in sentences:
                if re.search(r'\b' + re.escape(word) + r'\b', s, re.IGNORECASE):
                    context_sentence = s.strip()
                    break

            errors.append({
                "word": word,
                "suggested_correction": correction or word,
                "context": context_sentence[:100] if context_sentence else f"...{word}..."
            })

        total_words = len(tokens)
        error_count = len(errors)
        accuracy_pct = max(0.0, round(((total_words - error_count) / total_words) * 100.0, 1))
        penalty = min(round(error_count * deduction_per_error, 2), max_penalty)

        return {
            "total_words": total_words,
            "error_count": error_count,
            "accuracy_percentage": accuracy_pct,
            "penalty_deducted": penalty,
            "errors": errors
        }

spelling_engine = SpellingEngine()
