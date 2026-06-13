import sys
import unittest
from os import environ
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from tournament_os.api.main import app


class AdminAuthBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

    def test_admin_api_fails_closed_without_configured_token(self) -> None:
        environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

        response = self.client.post("/admin/scores/score_1/submit")

        self.assertEqual(response.status_code, 403)

    def test_admin_api_rejects_wrong_token(self) -> None:
        environ["TOURNAMENT_OS_ADMIN_TOKEN"] = "expected-token"

        response = self.client.post(
            "/admin/scores/score_1/submit",
            headers={"x-admin-token": "wrong-token"},
        )

        self.assertEqual(response.status_code, 403)

    def test_web_admin_fails_closed_without_token(self) -> None:
        environ["TOURNAMENT_OS_ADMIN_TOKEN"] = "expected-token"

        response = self.client.get("/web/admin/tournaments/demo")

        self.assertEqual(response.status_code, 403)

    def test_bearer_token_is_accepted_for_admin_boundary(self) -> None:
        environ["TOURNAMENT_OS_ADMIN_TOKEN"] = "expected-token"

        response = self.client.post(
            "/admin/scores/score_1/submit",
            headers={"authorization": "Bearer expected-token"},
        )

        self.assertNotEqual(response.status_code, 403)

    def test_public_health_does_not_require_admin_token(self) -> None:
        environ.pop("TOURNAMENT_OS_ADMIN_TOKEN", None)

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
