from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_whatsapp_sharing_consent_is_required_for_every_case():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "if form.whatsapp_consent.data != 'yes':" in source
    assert "whatsapp_consent=StringField" in source


def test_case_is_committed_before_external_redirect():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/privacy')", start)
    route = source[start:end]
    assert route.index("db.session.commit()") < route.index("return whatsapp_success(whatsapp_url, submitted_ref, wants_json)")
    helper = source[source.index("def whatsapp_success("):source.index("@app.errorhandler(CSRFError)")]
    assert "response = redirect(whatsapp_url, code=303)" in helper
    assert "db.session.rollback()" in route
    assert "intake_failure" in route and "Case intake could not be committed" not in route


def test_whatsapp_url_is_server_generated_and_configuration_checked_before_commit():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/privacy')", start)
    route = source[start:end]
    assert "os.environ.get('WHATSAPP_NUMBER', '')" in route
    assert route.index("build_case_whatsapp_url(configured_whatsapp, item)") < route.index("db.session.commit()")
    assert "response.headers['Referrer-Policy'] = 'no-referrer'" in route


def test_one_submit_button_is_the_only_contact_delivery_action():
    form = (ROOT / "templates" / "contact.html").read_text(encoding="utf-8")
    assert form.count('type="submit"') == 1
    assert "contact-choice" not in form
    assert 'name="contact_method"' not in form
    assert "t('send_to_whatsapp')" in form
