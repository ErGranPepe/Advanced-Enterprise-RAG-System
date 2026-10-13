# Document QA baseline

Working extractive retrieval for Markdown, text and selectable-text PDFs with source chunk/page IDs and JSON traces. This is **not** an LLM RAG solution and does not provide semantic understanding. No customer documents, tokens or API keys.

Run from the repo root:

```bash
python -m poc.document_qa --document your-file.md --question 'What is the cancellation policy?' --output report.json
```

For PDF inputs install `pymupdf`. If the document has no extractable text the program stops with an explicit error. The source itself is in `poc/document_qa.py`.

The demonstration is intentionally limited to lexical retrieval; an actual contract would need source-span validation, labelled evaluations, privacy requirements and a reviewed deployment plan.
