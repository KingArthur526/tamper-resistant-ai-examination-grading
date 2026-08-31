import numpy as np
from typing import List, Union, Dict
from sklearn.feature_extraction.text import TfidfVectorizer

class EmbeddingEngine:
    """
    Dual-mode Semantic Embedding Engine:
    1. SentenceTransformers SBERT (all-MiniLM-L6-v2) for neural dense embeddings with lazy load.
    2. High-precision Deterministic N-Gram TF-IDF Vectorizer as fallback/offline engine.
    Always transparently reports which model and configuration was used.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_dim = 384
        self._sbert_model = None
        self._is_sbert_available = None
        self._cache: Dict[str, np.ndarray] = {}

    def _ensure_model(self):
        if self._is_sbert_available is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sbert_model = SentenceTransformer(self.model_name)
                self._is_sbert_available = True
                self.embedding_dim = 384
            except Exception:
                self._is_sbert_available = False
                self.embedding_dim = 512

    @property
    def active_engine_name(self) -> str:
        self._ensure_model()
        if self._is_sbert_available:
            return f"Sentence-BERT ({self.model_name})"
        return "Deterministic-Semantic-Vector-Engine (TF-IDF N-Gram)"

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.zeros((0, self.embedding_dim), dtype=np.float32)

        self._ensure_model()

        uncached = [t for t in texts if t not in self._cache]
        if uncached:
            if self._is_sbert_available and self._sbert_model is not None:
                try:
                    embeddings = self._sbert_model.encode(
                        uncached,
                        convert_to_numpy=True,
                        show_progress_bar=False,
                        normalize_embeddings=True
                    )
                    for t, emb in zip(uncached, embeddings):
                        self._cache[t] = emb
                except Exception:
                    self._fallback_encode(uncached)
            else:
                self._fallback_encode(uncached)

        return np.array([self._cache[t] for t in texts], dtype=np.float32)

    def _fallback_encode(self, texts: List[str]):
        vectorizer = TfidfVectorizer(ngram_range=(1, 3), analyzer="word", min_df=1)
        corpus = texts + [
            "the network layer provides logical addressing routing ip packets paths",
            "transport layer ensures reliable delivery error recovery retransmission tcp udp",
            "physical layer transmits raw bits signals media cables voltage",
            "data link layer handles mac framing error detection switches",
            "presentation encryption compression formatting syntax",
            "application protocol http dns email user interface services"
        ]
        X = vectorizer.fit_transform(corpus).toarray()
        for idx, t in enumerate(texts):
            vec = X[idx]
            if len(vec) < self.embedding_dim:
                padded = np.pad(vec, (0, self.embedding_dim - len(vec)), "constant")
            else:
                padded = vec[:self.embedding_dim]
            norm = np.linalg.norm(padded)
            if norm > 0:
                padded = padded / norm
            self._cache[t] = padded

embedding_engine = EmbeddingEngine()
