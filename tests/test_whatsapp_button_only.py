from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_first_page_has_one_create_case_submit_and_no_whatsapp_choice():
    form = (ROOT / 'templates/contact.html').read_text(encoding='utf-8')
    assert form.count('type="submit"') == 1
    assert "t('create_secure_case')" in form
    assert "t('send_to_whatsapp')" not in form
    assert 'contact-choice' not in form
    assert 'name="contact_method"' not in form
    assert 'whatsapp-consent' in form and 'required' in form


def test_second_page_has_one_whatsapp_action_and_a_return_path():
    page = (ROOT / 'templates/case_ready.html').read_text(encoding='utf-8')
    assert page.count('id="case-ready-whatsapp"') == 1
    assert page.count('href="{{ whatsapp_url }}"') == 1
    assert 'target="_blank"' in page
    assert 'rel="noopener noreferrer"' in page
    assert "t('case_ready_send')" in page
    assert "url_for('home')" in page
    assert "t('back')" in page
    assert 'After pressing Send in WhatsApp' in page


def test_success_is_post_redirect_get_to_signed_saved_case_page():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert 'db.session.commit()' in route
    assert 'handoff_token = issue_case_handoff_token(case_ref)' in route
    assert "redirect(url_for('case_ready', token=handoff_token), code=303)" in route
    assert 'whatsapp_success' not in source


def test_all_locales_have_both_create_and_send_labels():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == 'WHATSAPP_INTAKE_COPY' for t in n.targets
    ))
    labels = ast.literal_eval(node)
    assert set(labels) == {'en','fr','ar','ar-tn','es','de','it','pt','tr','zh','ja'}
    for locale, values in labels.items():
        for key in ('create_secure_case','case_ready_title','case_ready_send','case_ready_note'):
            assert values.get(key), f'{locale} missing {key}'


def test_fragile_ajax_submission_is_removed_from_contact_javascript():
    js = (ROOT / 'static/js/app.js').read_text(encoding='utf-8')
    assert 'fetch(form.action' not in js
    assert 'case-intake-form' not in js
    assert 'case-create-form' in js
    assert 'button.disabled = true' in js
