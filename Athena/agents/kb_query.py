"""
Latitude MedTech — Knowledge Base Query
==========================================
Searches the local RAG knowledge base before making API calls.
Reduces tokens by grounding Claude in pre-retrieved context.

Usage:
    from kb_query import KBQuery
    kb = KBQuery()

    # Get relevant chunks for a topic
    chunks = kb.search("CAPA corrective action ISO 13485", top_k=4)

    # Format for injection into a prompt
    context = kb.format_context(chunks)
"""

import json
import re
import math
from typing import List, Dict

from pathconfig import KB_DIR


class KBQuery:
    def __init__(self):
        self._chunks = []
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._chunks = []
        if not KB_DIR.exists():
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
            except Exception:
                pass
        self._loaded = True

    def _tfidf_score(self, query: str, text: str) -> float:
        """Simple TF-IDF-like relevance score."""
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        text_lower  = text.lower()
        text_words  = re.findall(r'\b\w+\b', text_lower)
        if not text_words:
            return 0.0

        score = 0.0
        for term in query_terms:
            tf = text_words.count(term) / len(text_words)
            # Boost exact phrase matches
            if term in text_lower:
                score += tf * 2
            # Boost regulatory-specific terms
            if term in ['fda', 'mdr', 'iso', 'capa', 'cdrh', 'qms', 'mdsap',
                        '13485', '14971', '62304', 'pma', '510k', 'ivdr']:
                score += tf * 3
        return score

    def search(self, query: str, top_k: int = 4,
               category: str = None) -> List[Dict]:
        """Search KB chunks by relevance to query."""
        self._load()
        if not self._chunks:
            return []

        scored = []
        for chunk in self._chunks:
            if category and chunk.get('_category', '') != category:
                continue
            text  = chunk.get('text', '')
            score = self._tfidf_score(query, text)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def format_context(self, chunks: List[Dict], max_chars: int = 3000) -> str:
        """Format chunks for injection into a Claude prompt."""
        if not chunks:
            return ""

        parts = []
        total = 0
        for chunk in chunks:
            doc  = chunk.get('_doc_name') or chunk.get('doc_name', 'Unknown source')
            cat  = chunk.get('_category', '')
            text = chunk.get('text', '')
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
            "total_chunks": len(self._chunks),
            "by_category":  categories,
        }

    def has_content(self) -> bool:
        self._load()
        return len(self._chunks) > 0
