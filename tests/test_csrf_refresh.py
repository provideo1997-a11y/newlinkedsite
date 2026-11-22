from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_csrf_error_discards_rejected_token_before_rendering_fresh_form():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('@app.errorhandler(CSRFError)')
    end = source.index('@app.errorhandler(Exception)', start)
    handler = source[start:end]
    assert "session.pop('csrf_token', None)" in handler
    assert "formdata.pop('csrf_token', None)" in handler
    assert 'InquiryForm(formdata=formdata)' in handler
    assert "response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'" in handler
    assert 'return response' in handler


def test_contact_pages_are_not_cached():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('@app.after_request')
    end = source.index("@app.get('/')", start)
    middleware = source[start:end]
    assert "if request.path == '/contact' or request.path.startswith('/case/ready/')" in middleware
    assert "resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'" in middleware
