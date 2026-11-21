from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ajax_csrf_failure_refreshes_token_without_requesting_page_reload():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("@app.errorhandler(CSRFError)")
    end = source.index("@app.get('/privacy')", start)
    handler = source[start:end]
    assert "csrf_token = generate_csrf()" in handler
    assert "'code': 'CSRF_TOKEN_REFRESHED'" in handler
    assert "'csrf_token': csrf_token" in handler
    assert "'case_token': case_token" in handler
    assert "'retryable': retryable" in handler
    assert "'reload': True" not in handler


def test_client_retries_one_csrf_refresh_and_never_calls_location_reload():
    source = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
    start = source.index("// Reliable single-button intake.")
    end = source.index("// Admin list filtering", start)
    js = source[start:end]
    assert "payload.code === 'CSRF_TOKEN_REFRESHED'" in js
    assert "applyRefreshedTokens(payload)" in js
    assert "response = await sendRequest()" in js
    assert "if (!payload.retryable)" in js
    assert "window.location.reload()" not in source
    assert "payload.reload" not in js
    assert "window.location.assign(destination.href)" in js


def test_form_posts_to_canonical_contact_path_and_language_cleaner_only_redirects_get():
    form = (ROOT / "templates/contact.html").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "action=\"{{ url_for('contact') }}\"" in form
    assert "if request.method == 'GET' and request.args.get('lang') in LANGS:" in app


def test_js_asset_cache_key_changes_to_force_updated_csrf_recovery_script():
    base = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    assert "v='case-token-recovery-20261121b'" in base


def test_route_level_expired_case_token_returns_refresh_code_csrf_token_and_new_question():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("def whatsapp_success(", start)
    route = source[start:end]
    assert "'code': 'CASE_TOKEN_REFRESHED'" in route
    assert "'csrf_token': generate_csrf()" in route
    assert "'case_token': form.case_token.data" in route
    assert "'human_question': question" in route
    assert "'retryable': False" in route


def test_client_handles_route_level_case_token_refresh_and_focuses_new_check():
    source = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
    start = source.index("// Reliable single-button intake.")
    end = source.index("// Admin list filtering", start)
    js = source[start:end]
    assert "payload.code === 'CASE_TOKEN_REFRESHED'" in js
    assert "applyRefreshedTokens(payload)" in js
    assert "answer.focus({ preventScroll: true })" in js
    assert "answer.scrollIntoView" in js


def test_expired_authentic_case_token_can_be_renewed_without_changing_answer():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def refresh_case_token(")
    end = source.index("class Inquiry(", start)
    helper = source[start:end]
    assert "max_age=24 * 60 * 60" in helper
    assert "'ref': payload['ref'], 'a': payload['a'], 'b': payload['b']" in helper
    assert "return renewed, f\"{payload['a']} + {payload['b']}\", True" in helper


def test_case_token_helpers_preserve_challenge_when_token_expires_but_signature_is_valid():
    import ast
    import random
    import secrets
    import time
    import re
    from datetime import datetime, timezone
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"issue_case_token", "_validate_case_token_payload", "read_case_token", "refresh_case_token"}
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in funcs} == names

    secret = "stable-test-secret-which-is-long-enough"
    namespace = {
        "_case_token_serializer": URLSafeTimedSerializer(secret, salt="yakuza-case-intake-v1"),
        "BadSignature": BadSignature,
        "datetime": datetime,
        "timezone": timezone,
        "secrets": secrets,
        "random": random,
        "re": re,
    }
    exec(compile(ast.Module(body=funcs, type_ignores=[]), "app_case_token_helpers", "exec"), namespace)

    class OldTimestampSerializer(URLSafeTimedSerializer):
        def make_signer(self, salt=None):
            signer = super().make_signer(salt)
            signer.get_timestamp = lambda: int(time.time()) - 2 * 60 * 60
            return signer

    old_serializer = OldTimestampSerializer(secret, salt="yakuza-case-intake-v1")
    original_payload = {"ref": "YKZ-261121-ABCDEF123456", "a": 7, "b": 4}
    expired_token = old_serializer.dumps(original_payload)
    try:
        namespace["read_case_token"](expired_token)
    except SignatureExpired:
        pass
    else:
        raise AssertionError("Test token should be outside the normal one-hour lifetime")

    renewed_token, question, retryable = namespace["refresh_case_token"](expired_token)
    assert retryable is True
    assert question == "7 + 4"
    assert namespace["read_case_token"](renewed_token) == original_payload


def test_case_token_signed_by_old_secret_gets_a_new_visible_challenge():
    import ast
    import random
    import secrets
    import re
    from datetime import datetime, timezone
    from itsdangerous import URLSafeTimedSerializer, BadSignature

    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"issue_case_token", "_validate_case_token_payload", "read_case_token", "refresh_case_token"}
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {
        "_case_token_serializer": URLSafeTimedSerializer("new-test-secret", salt="yakuza-case-intake-v1"),
        "BadSignature": BadSignature,
        "datetime": datetime,
        "timezone": timezone,
        "secrets": secrets,
        "random": random,
        "re": re,
    }
    exec(compile(ast.Module(body=funcs, type_ignores=[]), "app_case_token_helpers", "exec"), namespace)
    old_token = URLSafeTimedSerializer("old-test-secret", salt="yakuza-case-intake-v1").dumps(
        {"ref": "YKZ-261121-ABCDEF123456", "a": 7, "b": 4}
    )
    new_token, question, retryable = namespace["refresh_case_token"](old_token)
    assert retryable is False
    assert question != "7 + 4" or namespace["read_case_token"](new_token)["ref"] != "YKZ-261121-ABCDEF123456"
    assert namespace["read_case_token"](new_token)["ref"].startswith("YKZ-")
