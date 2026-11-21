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
    assert "v='csrf-refresh-20261121'" in base
