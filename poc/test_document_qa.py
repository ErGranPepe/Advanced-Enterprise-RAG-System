import json
from pathlib import Path
import tempfile
import unittest

from poc.document_qa import answer, load_chunks, split_chunks

class DocumentTests(unittest.TestCase):
    def test_retrieval_and_exact_citation(self):
        with tempfile.TemporaryDirectory() as p:
            file = Path(p) / "contract.md"
            file.write_text("# Pricing\nAnnual price: 1200 EUR.\n\n# Support\nSupport response time: two business days.\n", encoding="utf8")
            result = answer(file, "annual price", 1)
            self.assertEqual(result["status"], "evidence_found")
            self.assertIn("1200 EUR", result["evidence"][0]["quote"])
            self.assertIn(result["evidence"][0]["citation"], [c.citation for c in load_chunks(file)])
    def test_no_evidence_abstains(self):
        with tempfile.TemporaryDirectory() as p:
            f = Path(p) / "brief.md"
            f.write_text("# Scope\nSupports invoices and receipts.\n", encoding="utf8")
            self.assertEqual(answer(f, "pineapple quantum volcano")["status"], "no_supporting_evidence")
    def test_chunking_is_deterministic(self):
        content = "# Intro\nFirst paragraph.\n\n# Other\nSecond paragraph."
        self.assertEqual(split_chunks(content,"sample.md"),split_chunks(content,"sample.md"))
        self.assertEqual(len(split_chunks(content,"sample.md")),2)
    def test_unsupported_files_fail(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/"test.docx"
            f.write_bytes(b"x")
            with self.assertRaises(ValueError): load_chunks(f)
    def test_trace_is_json(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/"brief.txt"
            f.write_text("Warranty excludes batteries.",encoding="utf8")
            self.assertEqual(json.loads(json.dumps(answer(f,"batteries")))["trace"]["chunks_indexed"],1)
    def test_pdf_page_citation_when_installed(self):
        try: import fitz
        except ImportError: self.skipTest("PyMuPDF optional")
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/"agreement.pdf"
            d=fitz.open()
            d.new_page().insert_text((40,100),"Cancellation fee is 20 EUR.")
            d.save(f)
            d.close()
            self.assertIn("agreement.pdf:p1#C",answer(f,"cancellation fee")["evidence"][0]["citation"])

if __name__=="__main__":
    unittest.main()
