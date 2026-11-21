from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_render_python_version_is_explicitly_pinned():
    assert (ROOT / ".python-version").read_text().strip() == "3.12.8"
    assert "PYTHON_VERSION" in (ROOT / "render.yaml").read_text()


def test_post_requests_are_logged_without_form_values():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "intake_request_received support_ref=%s content_length=%s" in source
    assert "intake_request_completed support_ref=%s status=%s elapsed_ms=%s" in source
    assert "request.form" not in source[source.index("def language_and_security") : source.index("@app.after_request")]


def test_unexpected_exceptions_get_a_correlated_safe_500_page():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "@app.errorhandler(Exception)" in source
    assert "if isinstance(error, HTTPException):" in source
    assert "unhandled_request_failure support_ref=%s method=%s endpoint=%s" in source
    assert "server_error.html" in source
    assert "exc_info=(type(error), error, error.__traceback__)" in source
    page = (ROOT / "templates/server_error.html").read_text(encoding="utf-8")
    assert "support_reference" in page
    assert "request.form" not in page


def test_db_exceptions_hide_bound_parameters():
    source = (ROOT / "security_utils.py").read_text(encoding="utf-8")
    assert '"hide_parameters": True' in source


def test_intake_health_endpoint_reports_only_safe_configuration_state():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("@app.get('/health/intake')")
    end = source.index("@app.get('/health/db')", start)
    endpoint = source[start:end]
    assert "normalize_whatsapp_number" in endpoint
    assert "database_status" in endpoint
    assert "sys.version.split()[0]" in endpoint
    assert "DATABASE_URL" not in endpoint
    assert "WHATSAPP_NUMBER'" in endpoint
