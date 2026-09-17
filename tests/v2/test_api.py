import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.index import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_cases_and_no_store(self):
        response = self.client.get("/api/v2/cases")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["cases"]), 4)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get("/api/v2/cases/unknown").status_code, 404)

    def test_execution_is_real(self):
        response = self.client.post("/api/v2/run", json={"case_id": "case_001"})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["counts"]["events"], 0)

    def test_upload_paths_and_extra_fields_rejected(self):
        for body in [{"case_id": "../secret"}, {"case_id": "case_001", "text": "arbitrary"},
                     {"case_id": ["case_001"]}, [], {}]:
            self.assertEqual(self.client.post("/api/v2/run", json=body).status_code, 400)
        self.assertEqual(self.client.post("/api/v2/run", content="x" * 300,
                                         headers={"content-type": "application/json"}).status_code, 413)
        self.assertEqual(self.client.post("/api/v2/run", files={"file": ("note.txt", b"x")}).status_code, 415)

    def test_no_fallback_on_failure(self):
        with patch("api.index.execute", side_effect=RuntimeError("private filesystem path")):
            response = self.client.post("/api/v2/run", json={"case_id": "case_001"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private filesystem", response.text)
        self.assertNotIn("artifacts", response.json())

    def test_no_false_persistence(self):
        self.assertEqual(self.client.get("/api/v2/run/anything").status_code, 410)

    def test_vercel_rewrite(self):
        self.assertEqual(self.client.get("/api?v2_path=cases").status_code, 200)


if __name__ == "__main__":
    unittest.main()
