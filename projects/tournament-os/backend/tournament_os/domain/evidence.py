from ipaddress import ip_address
from urllib.parse import urlparse

from tournament_os.domain.errors import DomainError


def validate_evidence_uri(evidence_uri: str | None) -> str | None:
    if evidence_uri is None or evidence_uri == "":
        return None

    parsed = urlparse(evidence_uri)
    if parsed.scheme not in {"http", "https"}:
        raise DomainError("evidence_uri_invalid", "Evidence URI must use http or https.")

    if not parsed.netloc:
        raise DomainError("evidence_uri_invalid", "Evidence URI must include a host.")

    host = parsed.hostname
    if host is None:
        raise DomainError("evidence_uri_invalid", "Evidence URI host is invalid.")

    try:
        parsed_ip = ip_address(host)
    except ValueError:
        return evidence_uri

    if parsed_ip.is_private or parsed_ip.is_loopback or parsed_ip.is_link_local:
        raise DomainError(
            "evidence_uri_private_host",
            "Evidence URI cannot point to a private or local network host.",
        )

    return evidence_uri
