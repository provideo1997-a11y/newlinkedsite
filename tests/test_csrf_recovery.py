from pathlib import Path
import ast
from itsdangerous import URLSafeTimedSerializer, BadSignature

ROOT = Path(__file__).resolve().parents[1]


def test_intake_uses_only_flask_wtf_csrf_without_custom_case_token():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    form_source = source[source.index('class InquiryForm'):source.index('class LoginForm')]
    assert 'case_token' not in form_source
    assert 'HiddenField' not in source
    assert '_case_token_serializer' not in source
    assert 'refresh_case_token' not in source
    assert 'CSRFProtect(app)' in source
    assert 'class Meta:' in form_source
    assert 'csrf = False' in form_source
    assert '@csrf.exempt' in source
    assert 'def is_same_origin_intake_submission()' in source


def test_csrf_error_re_renders_form_without_challenge_or_token_retry_loop():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('@app.errorhandler(CSRFError)')
    end = source.index('@app.errorhandler(Exception)', start)
    handler = source[start:end]
    assert "session.pop('csrf_token', None)" in handler
    assert "formdata.pop('csrf_token', None)" in handler
    assert 'InquiryForm(formdata=formdata)' in handler
    assert "flash(tr('intake_csrf_error'), 'error')" in handler
    assert "render_template('contact.html', form=form)" in handler
    assert 'refresh_case_token' not in handler
    assert 'human_answer' not in handler


def test_contact_form_is_normal_html_post_and_keeps_one_create_button():
    form = (ROOT / 'templates/contact.html').read_text(encoding='utf-8')
    assert 'method="post"' in form
    assert 'form.hidden_tag()' in form
    assert 'csrf_token' not in form
    assert form.count('type="submit"') == 1
    assert 'contact-choice' not in form
    assert 'name="contact_method"' not in form
    assert 'case_token' not in form


def test_lang_query_redirect_only_applies_to_get_requests():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "if request.method == 'GET' and request.args.get('lang') in LANGS:" in source


def test_case_handoff_token_remains_signed_and_expires():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == '_case_handoff_serializer' for t in n.targets
    ))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'issue_case_handoff_token')
    secret = 'handoff-test-secret'
    ns = {'app': type('A', (), {'config': {'SECRET_KEY': secret}}), 'URLSafeTimedSerializer': URLSafeTimedSerializer}
    exec(compile(ast.Module(body=[node, func], type_ignores=[]), 'handoff', 'exec'), ns)
    token = ns['issue_case_handoff_token']('YKZ-261121-ABCDEF123456')
    assert ns['_case_handoff_serializer'].loads(token, max_age=86400) == {'ref': 'YKZ-261121-ABCDEF123456'}
    try:
        ns['_case_handoff_serializer'].loads('not-a-token', max_age=86400)
    except BadSignature:
        pass
    else:
        raise AssertionError('Invalid handoff tokens must be rejected')
