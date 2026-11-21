"""Privacy-aware WhatsApp click-to-chat helpers for saved YAKUZA cases.

The site can create a local case and prepare a WhatsApp draft. WhatsApp's
click-to-chat interface still requires the visitor to review and press Send.
"""
from __future__ import annotations

from urllib.parse import quote

from security_utils import normalize_whatsapp_number


_PLATFORM_LABELS = {
    "not-specified": "Not specified",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "tiktok": "TikTok",
    "google": "Google",
    "x": "X",
    "linkedin": "LinkedIn",
    "other": "Other",
}
_TOPIC_LABELS = {
    "recovery": "Account access and recovery",
    "hacked": "Compromised account response",
    "impersonation": "Impersonation / fake profile",
    "scam": "Scam / fraud incident review",
    "privacy": "Privacy / data exposure",
    "reputation": "Brand / reputation protection",
    "compliance": "Policy / compliance guidance",
    "security": "Security check-up / prevention",
    "risk": "Digital risk response",
    "other": "Other request",
}
_URGENCY_LABELS = {"normal": "Normal", "high": "High", "critical": "Critical"}
_FLAG_LABELS = {
    "credential_request": "Request for password or authentication code",
    "guaranteed_recovery_claim": "Guaranteed account-recovery claim",
    "off_platform_payment_pressure": "Pressure to pay off-platform",
}


def _one_line(value: object, fallback: str = "Not provided") -> str:
    """Format a metadata value as one line without control-character spoofing."""
    if value is None:
        return fallback
    text = str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return " ".join(text.split()) or fallback


def build_case_whatsapp_message(case: object) -> str:
    """Build a complete, plain-text WhatsApp draft from a committed case object."""
    case_ref = _one_line(getattr(case, "case_ref", None), "Reference unavailable")
    created_at = getattr(case, "created_at", None)
    if created_at is not None and hasattr(created_at, "isoformat"):
        created_label = created_at.isoformat(timespec="seconds")
    else:
        created_label = _one_line(created_at)

    topic = str(getattr(case, "topic", "other") or "other")
    platform = str(getattr(case, "platform", "not-specified") or "not-specified")
    urgency = str(getattr(case, "urgency", "normal") or "normal")
    flags_raw = getattr(case, "risk_flags", "") or ""
    flags = [
        _FLAG_LABELS.get(flag.strip(), _one_line(flag.strip()))
        for flag in str(flags_raw).split(",") if flag.strip()
    ]

    # Keep the original narrative intact. Delimiters make it clear that the
    # description is user-supplied content, not instructions from the service.
    narrative = str(getattr(case, "message", "") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    triage = str(getattr(case, "triage_report", "") or "").strip()
    evidence = _one_line(getattr(case, "evidence_url", ""), "Not supplied")

    lines = [
        "YAKUZA — NEW SECURE CASE",
        f"Case reference: {case_ref}",
        f"Created (UTC): {created_label}",
        "",
        "REQUESTER DETAILS",
        f"Name: {_one_line(getattr(case, 'name', None))}",
        f"Email: {_one_line(getattr(case, 'email', None))}",
        f"Phone / WhatsApp: {_one_line(getattr(case, 'phone', None))}",
        "",
        "INCIDENT DETAILS",
        f"Platform: {_PLATFORM_LABELS.get(platform, _one_line(platform))}",
        f"Account handle / profile: {_one_line(getattr(case, 'account_handle', None))}",
        f"Incident date: {_one_line(getattr(case, 'incident_date', None))}",
        f"Category: {_TOPIC_LABELS.get(topic, _one_line(topic))}",
        f"Priority: {_URGENCY_LABELS.get(urgency, _one_line(urgency))}",
        f"Evidence link: {evidence}",
        f"Preferred contact: {_one_line(getattr(case, 'contact_method', None), 'Private inbox')}",
        "Requester authorization: confirmed during intake",
        "WhatsApp data-sharing consent: confirmed during intake",
        "",
        "USER-SUBMITTED DESCRIPTION (verbatim)",
        "--- BEGIN DESCRIPTION ---",
        narrative,
        "--- END DESCRIPTION ---",
        "",
        "AUTOMATED INTAKE REVIEW (ADVISORY ONLY)",
        f"Risk indicator score: {getattr(case, 'risk_score', 0) or 0}/90",
        "Risk indicators: " + ("; ".join(flags) if flags else "No configured indicators detected"),
    ]
    if triage:
        lines.extend(["", "GENERATED TRIAGE REPORT", triage])
    lines.extend([
        "",
        "Case status: NEW — saved in the YAKUZA case database before WhatsApp hand-off.",
        "Please review this message and press Send in WhatsApp to share it with YAKUZA.",
        "Automated indicators are not a fraud finding or a final conclusion.",
    ])
    return "\n".join(lines)


def build_case_whatsapp_url(raw_number: str | None, case: object) -> str | None:
    """Return a wa.me URL containing the full saved-case draft, or None if invalid."""
    number = normalize_whatsapp_number(raw_number)
    if not number:
        return None
    message = build_case_whatsapp_message(case)
    return f"https://wa.me/{number}?text={quote(message, safe='')}"
