import os, re, glob
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import config

_model = None
def embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


class VectorIndex:
    def __init__(self, items):
        self.items = items
        vecs = embedder().encode([i["text"] for i in items], normalize_embeddings=True).astype("float32")
        self.index = faiss.IndexFlatIP(vecs.shape[1])
        self.index.add(vecs)

    def search(self, query, k=config.TOP_K):
        v = embedder().encode([query], normalize_embeddings=True).astype("float32")
        scores, ids = self.index.search(v, min(k, len(self.items)))
        return [dict(self.items[i], score=float(s)) for s, i in zip(scores[0], ids[0]) if i >= 0]


def load_code_chunks(folder):
    items = []
    for path in sorted(glob.glob(os.path.join(folder, "**", "*.[ch]"), recursive=True)):
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
        name = os.path.relpath(path, folder)
        s = 0
        while s < len(lines):
            part = lines[s:s + config.CHUNK_LINES]
            items.append({"text": "\n".join(part), "file": name, "start": s + 1, "end": s + len(part)})
            if s + config.CHUNK_LINES >= len(lines):
                break
            s += config.CHUNK_STRIDE
    return items


def load_rules(path):
    txt = open(path, encoding="utf-8").read()
    items = []
    for block in re.split(r"\n\s*\n", txt):
        m = re.search(r"RULE\s+([A-Z]+-\d+)", block)
        if m:
            items.append({"text": block.strip(), "rule_id": m.group(1), "file": "coding_rules.txt"})
    return items
