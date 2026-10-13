"""Verifiable extractive retrieval baseline for MD/TXT/PDF.

No LLM, embeddings, or vector store. Evidence is exact source text with
page/chunk identifiers, plus deterministic retrieval traces. This is NOT
production RAG, semantic search, or a security-screened document processor.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

WORD = re.compile(r"[^\W_]+", re.UNICODE)
STOP = set("a al an and are as at con de del el en es for from how in is la las lo los of on or para por que se the to un una unas unos y you your what why which where qué cuál cómo donde cuándo cuando cuánto cuantos cuántos".split())


def tokens(value: str) -> list[str]:
    return [word for word in (m.group(0).lower() for m in WORD.finditer(value)) if len(word) > 1 and word not in STOP]


@dataclass(frozen=True)
class Chunk:
    citation: str
    text: str
    heading: str = ""


def split_chunks(text: str, prefix: str, max_words: int = 180) -> list[Chunk]:
    if max_words < 1:
        raise ValueError("max_words must be positive")
    chunks: list[Chunk] = []
    section = ""
    paragraph: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        words = " ".join(paragraph).split()
        for start in range(0, len(words), max_words):
            snippet = " ".join(words[start:start + max_words])
            if snippet:
                chunks.append(Chunk(citation=f"{prefix}#C{len(chunks)+1:03}", text=snippet, heading=section))
        paragraph = []

    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^#{1,6}\s+", line):
            flush()
            section = re.sub(r"^#{1,6}\s+", "", line)
        elif not line:
            flush()
        else:
            paragraph.append(line)
    flush()
    return chunks


def load_chunks(path: str | Path) -> list[Chunk]:
    src = Path(path)
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.suffix.lower() in {".md", ".txt"}:
        chunks = split_chunks(src.read_text(encoding="utf-8"), src.name)
    elif src.suffix.lower() == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PDF support requires PyMuPDF: pip install pymupdf") from exc
        chunks = []
        with fitz.open(src) as pdf:
            for page_index, page in enumerate(pdf, 1):
                chunks.extend(split_chunks(page.get_text("text"), f"{src.name}:p{page_index}"))
    else:
        raise ValueError("Supported formats: .md, .txt, .pdf")
    if not chunks:
        raise ValueError("Document contains no extractable text (scanned PDFs require OCR)")
    return chunks


def rank(question: str, chunks: list[Chunk], top_k: int = 3) -> list[tuple[Chunk, float]]:
    terms = tokens(question)
    if not terms or top_k < 1 or not chunks:
        return []
    bags = [Counter(tokens(c.heading + " " + c.text)) for c in chunks]
    frequencies = Counter(token for bag in bags for token in bag)
    average_length = max(sum(sum(b.values()) for b in bags) / len(bags), 1)
    found: list[tuple[Chunk, float]] = []
    for chunk, bag in zip(chunks, bags):
        doc_length = sum(bag.values())
        score = 0.0
        for term in set(terms):
            count = bag.get(term, 0)
            if not count:
                continue
            idf = math.log(1 + (len(chunks) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
            score += idf * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * doc_length / average_length))
        if score > 0:
            found.append((chunk, round(score, 6)))
    return sorted(found, key=lambda pair: (-pair[1], pair[0].citation))[:top_k]


def answer(document: str | Path, question: str, top_k: int = 3) -> dict:
    chunks = load_chunks(document)
    matches = rank(question, chunks, top_k)
    evidence = [{"citation": c.citation, "heading": c.heading, "quote": c.text[:600], "score": score} for c, score in matches]
    return {"question": question,
            "document": Path(document).name,
            "method": "lexical-bm25-extractive-no-llm",
            "status": "evidence_found" if evidence else "no_supporting_evidence",
            "evidence": evidence,
            "trace": {"chunks_indexed": len(chunks), "query_terms": tokens(question),
                      "ranked_citations": [x["citation"] for x in evidence], "top_k": top_k}}


def main() -> None:
    p = argparse.ArgumentParser(description="Source-citable extractive document retrieval (not generative RAG)")
    p.add_argument("--document", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--output", help="Optional JSON report path")
    args = p.parse_args()
    report = json.dumps(answer(args.document, args.question, args.top_k), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
