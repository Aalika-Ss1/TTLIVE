import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.domain.errors import DomainError
from tournament_os.domain.evidence import validate_evidence_uri


class EvidenceTests(unittest.TestCase):
    def test_allows_public_https_uri(self) -> None:
        self.assertEqual(
            validate_evidence_uri("https://example.com/evidence.png"),
            "https://example.com/evidence.png",
        )

    def test_rejects_non_http_scheme(self) -> None:
        with self.assertRaises(DomainError) as context:
            validate_evidence_uri("file:///secret.png")

        self.assertEqual(context.exception.code, "evidence_uri_invalid")

    def test_rejects_private_ip_host(self) -> None:
        with self.assertRaises(DomainError) as context:
            validate_evidence_uri("http://127.0.0.1/evidence.png")

        self.assertEqual(context.exception.code, "evidence_uri_private_host")


if __name__ == "__main__":
    unittest.main()
