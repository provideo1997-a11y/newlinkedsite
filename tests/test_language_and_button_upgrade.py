from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_language_picker_is_limited_to_four_requested_languages():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "PUBLIC_LANGUAGE_CODES = ('ar-tn', 'fr', 'en', 'ar')" in source
    assert "'ar-tn': 'تونسي'" in source
    assert "if lang not in PUBLIC_LANGUAGE_CODES:" in source
    assert "WTF_CSRF_TIME_LIMIT=24 * 60 * 60" in source
    assert "PERMANENT_SESSION_LIFETIME=timedelta(hours=24)" in source


def test_whatsapp_action_is_a_button_that_opens_the_prepared_report():
    template = (ROOT / 'templates/case_ready.html').read_text(encoding='utf-8')
    js = (ROOT / 'static/js/app.js').read_text(encoding='utf-8')
    assert 'id="case-ready-whatsapp"' in template
    assert 'data-whatsapp-url="{{ whatsapp_url }}"' in template
    assert '<button' in template and 'type="button"' in template
    assert "window.open(target, '_blank')" in js
    assert "window.location.assign(target)" in js


def test_csrf_expiry_copy_does_not_expose_token_or_session_terminology():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'Your form session expired. Your entries have been kept.' not in source
    assert 'وفات جلسة الفورم' not in source
    assert 'Le formulaire est resté ouvert trop longtemps.' in source
    assert 'الفورم قعد محلول برشة وقت.' in source
