from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from whatsapp_utils import build_case_whatsapp_message, build_case_whatsapp_url


class SampleCase:
    case_ref = "YKZ-261121-ABC123DEF456"
    created_at = datetime(2026, 11, 21, 1, 30, tzinfo=timezone.utc)
    name = "Alex Example"
    email = "alex@example.com"
    phone = "+216 20 123 456"
    platform = "instagram"
    account_handle = "@sample-account"
    incident_date = "2026-11-20"
    topic = "hacked"
    urgency = "critical"
    evidence_url = "https://example.com/evidence"
    contact_method = "whatsapp"
    risk_score = 25
    risk_flags = "credential_request"
    message = "My account was accessed without permission. I changed the password but sessions remain active."
    triage_report = "Automated intake triage — review required, not a fraud determination.\nPriority: CRITICAL\nRecommendations: Review active sessions."


def test_configured_number_builds_expected_whatsapp_destination():
    url = build_case_whatsapp_url("491234567890", SampleCase())
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "wa.me"
    assert parsed.path == "/491234567890"


def test_whatsapp_message_contains_all_submitted_fields_and_full_triage_report():
    message = build_case_whatsapp_message(SampleCase())
    expected = [
        SampleCase.case_ref,
        SampleCase.name,
        SampleCase.email,
        SampleCase.phone,
        "Instagram",
        SampleCase.account_handle,
        SampleCase.incident_date,
        "Compromised account response",
        "Critical",
        SampleCase.evidence_url,
        SampleCase.message,
        "Request for password or authentication code",
        "Risk indicator score: 25/90",
        SampleCase.triage_report,
    ]
    for value in expected:
        assert value in message
    assert "BEGIN DESCRIPTION" in message and "END DESCRIPTION" in message
    assert "press Send" in message


def test_message_is_encoded_as_prefilled_whatsapp_text():
    url = build_case_whatsapp_url("+49 176 4248 4892", SampleCase())
    parsed = urlparse(url)
    text = parse_qs(parsed.query)["text"][0]
    assert SampleCase.case_ref in text
    assert SampleCase.message in text
    assert SampleCase.triage_report in text


def test_invalid_destination_does_not_build_external_url():
    assert build_case_whatsapp_url("not a phone number", SampleCase()) is None
    assert build_case_whatsapp_url("0049 0176 42484892", SampleCase()) is None
