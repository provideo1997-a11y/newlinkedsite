from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_intake_is_exempt_from_expiring_csrf_token_validation():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    form_source = source[source.index('class InquiryForm'):source.index('class LoginForm')]
    route_start = source.index("@app.route('/contact', methods=['GET', 'POST'])")
    route_end = source.index("@app.get('/case/ready/<token>')", route_start)
    route = source[route_start:route_end]
    assert 'csrf = False' in form_source
    assert '@csrf.exempt' in route
    assert 'is_same_origin_intake_submission()' in route
    assert 'form.validate_on_submit()' in route
    assert 'CSRFProtect(app)' in source  # retained for admin and other protected routes


def test_public_intake_rejects_explicit_cross_site_but_allows_missing_origin():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def is_same_origin_intake_submission():')
    end = source.index("@app.route('/contact', methods=['GET', 'POST'])", start)
    helper = source[start:end]
    assert "request.headers.get('Origin', '').strip()" in helper
    assert "request.headers.get('Referer', '').strip()" in helper
    assert "fetch_site == 'cross-site'" in helper
    assert "actual.netloc.split(':', 1)[0].lower() == expected_host" in helper
    assert "if not supplied or supplied.lower() == 'null':" in helper
    assert "actual.scheme.lower() not in ('http', 'https')" in helper


def test_contact_pages_are_not_cached():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('@app.after_request')
    end = source.index("@app.get('/')", start)
    middleware = source[start:end]
    assert "resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'" in middleware
