from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_contact_form_has_one_whatsapp_submit_and_no_delivery_alternatives():
    form = (ROOT / "templates" / "contact.html").read_text(encoding="utf-8")
    assert form.count('type="submit"') == 1
    assert "t('send_to_whatsapp')" in form
    assert "contact-choice" not in form
    assert "contact_method" not in form
    assert "private_title" not in form
    assert "whatsapp_title" not in form
    assert "whatsapp-consent" in form and "required" in form
    assert "submitted.html" not in form


def test_successful_submission_redirects_directly_to_whatsapp_after_commit():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/privacy')", start)
    route = source[start:end]
    assert "db.session.flush()" in route
    assert route.index("db.session.commit()") < route.index("response = redirect(whatsapp_url, code=303)")
    assert "build_case_whatsapp_url(configured_whatsapp, item)" in route
    assert "render_template(\n            'submitted.html'" not in route
    assert "contact_method='whatsapp'" in route
    assert "response.headers['Referrer-Policy'] = 'no-referrer'" in route


def test_no_receipt_template_or_extra_whatsapp_button_remains():
    assert not (ROOT / "templates" / "submitted.html").exists()
    assert "whatsapp-open-link" not in "\n".join(
        p.read_text(encoding="utf-8") for p in (ROOT / "templates").glob("*.html")
    )


def test_all_locales_have_single_button_label_and_configuration_error():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "WHATSAPP_INTAKE_COPY" for t in n.targets))
    labels = ast.literal_eval(node)
    assert set(labels) == {"en", "fr", "ar", "ar-tn", "es", "de", "it", "pt", "tr", "zh", "ja"}
    for locale, values in labels.items():
        assert values["send_to_whatsapp"]
        assert values["whatsapp_configuration_error"]
        assert values["secure_note"]


def test_server_requires_whatsapp_consent_and_checks_destination_before_commit():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/privacy')", start)
    route = source[start:end]
    assert "if form.whatsapp_consent.data != 'yes':" in route
    assert route.index("build_case_whatsapp_url(configured_whatsapp, item)") < route.index("db.session.commit()")
    assert "db.session.rollback()" in route
    assert "WHATSAPP_NUMBER" in route
