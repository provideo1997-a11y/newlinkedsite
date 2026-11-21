from pathlib import Path
import ast
import re
import secrets
import time
from datetime import datetime, timezone

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

ROOT = Path(__file__).resolve().parents[1]


def _token_helpers():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    names = {'issue_case_token', '_validate_case_token_payload', 'read_case_token', 'refresh_case_token'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    serializer_node = next(node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == '_case_token_serializer' for target in node.targets
    ))
    namespace = {
        'app': type('A', (), {'config': {'SECRET_KEY': 'stable-test-secret'}}),
        '_case_token_serializer': URLSafeTimedSerializer('stable-test-secret', salt='yakuza-case-intake-v1'),
        'URLSafeTimedSerializer': URLSafeTimedSerializer,
        'BadSignature': BadSignature,
        'SignatureExpired': SignatureExpired,
        'datetime': datetime,
        'timezone': timezone,
        'secrets': secrets,
        're': re,
    }
    exec(compile(ast.Module(body=[serializer_node, *nodes], type_ignores=[]), 'case_tokens', 'exec'), namespace)
    return namespace


def test_intake_no_longer_uses_ajax_or_arithmetic_challenge():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    js = (ROOT / 'static/js/app.js').read_text(encoding='utf-8')
    form = (ROOT / 'templates/contact.html').read_text(encoding='utf-8')
    assert 'fetch(form.action' not in js
    assert 'window.location.reload()' not in js
    assert 'human_answer' not in app
    assert 'human_question' not in app
    assert 'human-check' not in form
    assert 'human_answer' not in form
    assert 'human-question' not in form


def test_contact_csrf_handler_preserves_fields_and_issues_fresh_tokens():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('@app.errorhandler(CSRFError)')
    end = source.index("@app.get('/privacy')", start)
    handler = source[start:end]
    assert 'InquiryForm(formdata=request.form' in handler
    assert 'refresh_case_token(submitted_case_token)' in handler
    assert 'form.case_token.data = case_token' in handler
    assert 'form.csrf_token.data = generate_csrf()' in handler
    assert "flash(tr('intake_csrf_error'), 'error')" in handler
    assert 'human_answer' not in handler
    assert 'human_question' not in handler


def test_contact_form_is_normal_html_post_and_keeps_one_create_button():
    form = (ROOT / 'templates/contact.html').read_text(encoding='utf-8')
    assert 'method="post"' in form
    assert 'id="case-create-form"' in form
    assert form.count('type="submit"') == 1
    assert 'form.hidden_tag()' in form
    assert 'case-intake-form' not in form


def test_lang_query_redirect_only_applies_to_get_requests():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "if request.method == 'GET' and request.args.get('lang') in LANGS:" in source


def test_static_asset_cache_key_points_to_two_step_flow():
    base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
    assert "v='render-post-diagnostics-20261121b'" in base


def test_case_reference_token_has_no_arithmetic_challenge_and_is_signed():
    ns = _token_helpers()
    token = ns['issue_case_token']()
    payload = ns['read_case_token'](token)
    assert set(payload) == {'ref'}
    assert re.fullmatch(r'YKZ-[0-9]{6}-[A-F0-9]{12}', payload['ref'])


def test_expired_form_token_can_be_refreshed_without_changing_case_reference():
    ns = _token_helpers()

    class OldTimestampSerializer(URLSafeTimedSerializer):
        def make_signer(self, salt=None):
            signer = super().make_signer(salt)
            signer.get_timestamp = lambda: int(time.time()) - 8 * 24 * 60 * 60
            return signer

    old = OldTimestampSerializer('stable-test-secret', salt='yakuza-case-intake-v1')
    original_ref = 'YKZ-261121-ABCDEF123456'
    expired = old.dumps({'ref': original_ref})
    try:
        ns['read_case_token'](expired)
    except SignatureExpired:
        pass
    else:
        raise AssertionError('The normal form token lifetime should be bounded')
    renewed, reusable = ns['refresh_case_token'](expired)
    assert reusable is True
    assert ns['read_case_token'](renewed) == {'ref': original_ref}


def test_invalid_signed_token_is_replaced_not_trusted():
    ns = _token_helpers()
    renewed, reusable = ns['refresh_case_token']('tampered')
    assert reusable is False
    assert re.fullmatch(r'YKZ-[0-9]{6}-[A-F0-9]{12}', ns['read_case_token'](renewed)['ref'])


def test_handoff_token_is_signed_and_expires():
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
