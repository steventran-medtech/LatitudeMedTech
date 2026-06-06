"""
Latitude MedTech — Knowledge Base Query
==========================================
Searches the local RAG knowledge base before making API calls.
Uses sklearn TF-IDF vectorizer + cosine similarity for ranked retrieval —
significantly better than term-frequency counting alone.

Falls back to manual scoring if sklearn is not installed.

Usage:
    from kb_query import KBQuery
    kb = KBQuery()
    chunks = kb.search("CAPA corrective action ISO 13485", top_k=4)
    context = kb.format_context(chunks)
"""

import json
import re
from typing import List, Dict

from pathconfig import KB_DIR

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


# Regulatory term boosts applied on top of cosine similarity score
_REG_BOOST_TERMS = {
    'fda', 'mdr', 'iso', 'capa', 'cdrh', 'qms', 'mdsap',
    '13485', '14971', '62304', 'pma', '510k', 'ivdr', 'eumdr',
    'imdrf', 'mdd', 'pmcf', 'udi', 'cer', 'dhf', 'dhr', 'dmr',
}


class KBQuery:
    def __init__(self):
        self._chunks  = []
        self._texts   = []   # parallel list — chunk texts for vectorizer
        self._vec     = None  # fitted TfidfVectorizer
        self._matrix  = None  # TF-IDF doc-term matrix
        self._loaded  = False

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load(self):
        if self._loaded:
            return
        self._chunks = []
        self._texts  = []
        if not KB_DIR.exists():
            self._loaded = True
            return
        for json_file in KB_DIR.rglob('*.json'):
            if json_file.name == 'index.json':
                continue
            try:
                data = json.loads(json_file.read_text(encoding='utf-8', errors='replace'))
                for chunk in data.get('chunks', []):
                    chunk['_category'] = data.get('category', 'General')
                    chunk['_doc_name'] = data.get('doc_name', '')
                    self._chunks.append(chunk)
                    self._texts.append(chunk.get('text', ''))
            except Exception:
                pass
        self._loaded = True
        self._build_index()

    def _build_index(self):
        """Fit TF-IDF vectorizer over all chunk texts (once per load)."""
        if not self._texts or not _HAS_SKLEARN:
            return
        self._vec = TfidfVectorizer(
            strip_accents='unicode',
            analyzer='word',
            token_pattern=r'\b\w+\b',
            ngram_range=(1, 2),   # unigrams + bigrams for phrase matching
            min_df=1,
            max_features=30_000,
            sublinear_tf=True,    # log(1+tf) dampens very frequent terms
        )
        self._matrix = self._vec.fit_transform(self._texts)

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score_sklearn(self, query: str, category: str = None) -> List[tuple]:
        """Return (score, chunk) pairs using cosine similarity."""
        q_vec  = self._vec.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        results = []
        for idx, score in enumerate(scores):
            if score == 0.0:
                continue
            chunk = self._chunks[idx]
            if category and chunk.get('_category', '') != category:
                continue
            # Regulatory domain boost (+0.05 per matching term)
            text_lower = chunk.get('text', '').lower()
            boost = sum(0.05 for t in _REG_BOOST_TERMS if t in text_lower)
            results.append((float(score) + boost, chunk))
        return results

    def _score_fallback(self, query: str, category: str = None) -> List[tuple]:
        """Manual TF scoring when sklearn is unavailable."""
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        results = []
        for chunk in self._chunks:
            if category and chunk.get('_category', '') != category:
                continue
            text  = chunk.get('text', '')
            words = re.findall(r'\b\w+\b', text.lower())
            if not words:
                continue
            score = 0.0
            for term in query_terms:
                tf = words.count(term) / len(words)
                if tf:
                    score += tf * 2
                if term in _REG_BOOST_TERMS:
                    score += tf * 3
            if score > 0:
                results.append((score, chunk))
        return results

    # ── Public API ────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 4,
               category: str = None) -> List[Dict]:
        """Return top_k most relevant KB chunks for query."""
        self._load()
        if not self._chunks:
            return []
        if _HAS_SKLEARN and self._vec is not None:
            scored = self._score_sklearn(query, category)
        else:
            scored = self._score_fallback(query, category)
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def format_context(self, chunks: List[Dict], max_chars: int = 3000) -> str:
        """Format chunks for injection into a Claude prompt."""
        if not chunks:
            return ""
        parts = []
        total = 0
        for chunk in chunks:
            doc   = chunk.get('_doc_name') or chunk.get('doc_name', 'Unknown source')
            cat   = chunk.get('_category', '')
            text  = chunk.get('text', '')
            entry = f"[{cat} — {doc}]\n{text}"
            if total + len(entry) > max_chars:
                break
            parts.append(entry)
            total += len(entry)
        if not parts:
            return ""
        return (
            "RELEVANT KNOWLEDGE BASE CONTEXT "
            "(use as grounding — cite source category where relevant):\n\n"
            + "\n\n---\n\n".join(parts)
        )

    def get_stats(self) -> Dict:
        self._load()
        categories = {}
        for chunk in self._chunks:
            cat = chunk.get('_category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_chunks":   len(self._chunks),
            "by_category":    categories,
            "sklearn_active": _HAS_SKLEARN and self._vec is not None,
        }

    def has_content(self) -> bool:
        self._load()
        return len(self._chunks) > 0

    def invalidate(self):
        """Force reload on next search — call after new chunks are ingested."""
        self._chunks = []
        self._texts  = []
        self._vec    = None
        self._matrix = None
        self._loaded = False
