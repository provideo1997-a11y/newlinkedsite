import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_whatsapp_requires_separate_data_sharing_consent():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "form.contact_method.data == 'whatsapp' and form.whatsapp_consent.data != 'yes'" in source
    assert "class InquiryForm" in source and "whatsapp_consent=StringField" in source


def test_database_commit_precedes_whatsapp_url_generation():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert source.index("db.session.commit()", source.index("def contact")) < source.index(
        "build_case_whatsapp_url(", source.index("def contact")
    )
    assert "db.session.rollback()" in source
    assert "Case intake could not be committed" in source


def test_receipt_has_auto_handoff_and_manual_fallback():
    receipt = (ROOT / "templates" / "submitted.html").read_text(encoding="utf-8")
    script = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'id="whatsapp-handoff" data-whatsapp-url=' in receipt
    assert 'id="whatsapp-open-link"' in receipt
    assert "window.location.assign(target)" in script


def test_whatsapp_data_sharing_consent_is_visible_on_form():
    form = (ROOT / "templates" / "contact.html").read_text(encoding="utf-8")
    assert 'id="whatsapp-consent"' in form
    assert "whatsapp_consent_label" in form
    assert 'data-slow-message=' in form


def test_whatsapp_receipt_sets_no_referrer_without_being_overwritten():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "response.headers['Referrer-Policy'] = 'no-referrer'" in source
    assert "resp.headers.setdefault('Referrer-Policy','strict-origin-when-cross-origin')" in source
