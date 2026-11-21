from pathlib import Path

from security_utils import sqlalchemy_engine_options, ensure_unique_case_reference_index

ROOT = Path(__file__).resolve().parents[1]


def test_postgres_driver_has_bounded_connect_lock_statement_and_pool_waits():
    options = sqlalchemy_engine_options("postgresql+psycopg://user:pass@host/db")
    assert options["pool_timeout"] == 5
    assert options["pool_size"] == 2
    assert options["max_overflow"] == 1
    assert options["connect_args"]["connect_timeout"] == 5
    assert "statement_timeout=12000" in options["connect_args"]["options"]
    assert "lock_timeout=5000" in options["connect_args"]["options"]


def test_sqlite_has_bounded_lock_wait():
    options = sqlalchemy_engine_options("sqlite:////tmp/yakuza.db")
    assert options["connect_args"]["timeout"] == 5


def test_form_uses_signed_per_form_token_and_single_submit():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    form = source[source.index("class InquiryForm"):source.index("class LoginForm")]
    assert "case_token=HiddenField" in form
    assert "URLSafeTimedSerializer" in source
    assert "max_age=3600" in source
    template = (ROOT / "templates/contact.html").read_text(encoding="utf-8")
    assert template.count('type="submit"') == 1
    assert "form.hidden_tag()" in template
    assert "form.case_ref()" not in template


def test_case_replay_is_checked_before_human_challenge_and_commit_is_before_handoff():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("def whatsapp_success(", start)
    route = source[start:end]
    assert route.index("Inquiry.query.filter_by(case_ref=submitted_ref).first()") < route.index("expected_answer = str(token_data['a'] + token_data['b'])")
    assert route.index("db.session.commit()") < route.index("return whatsapp_success(whatsapp_url, submitted_ref, wants_json)")
    assert "except IntegrityError" in route
    assert "intake_failure support_ref=%s case_ref=%s stage=%s" in route


def test_ajax_client_has_bounded_wait_and_safe_same_button_retry():
    js = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
    assert "event.preventDefault()" in js
    assert "new AbortController()" in js
    assert "120000" in js
    assert "credentials: 'same-origin'" in js
    assert "redirect: 'error'" in js
    assert "content-type" in js
    assert "Unexpected server response." in js
    assert "payload.support_reference" in js
    assert "window.location.assign(destination.href)" in js
    assert "form.dataset.submitting = '1'" in js
    assert "case_token" in js
    assert "The server is still processing your request" in js


def test_db_health_endpoint_is_available_without_exposing_connection_details():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "@app.get('/health/db')" in source
    assert "'database': 'reachable'" in source
    assert "'database': 'unavailable'" in source


def test_every_locale_has_intake_wait_states():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("INTAKE_STATUS_COPY =")
    end = source.index("for _locale, _copy in INTAKE_STATUS_COPY.items()", start)
    catalog = source[start:end]
    locales = ("'en':", "'fr':", "'ar':", "'ar-tn':", "'es':", "'de':", "'it':", "'pt':", "'tr':", "'zh':", "'ja':")
    for locale in locales:
        assert locale in catalog
    for key in ("'saving':", "'waiting':", "'timeout':", "'network_error':", "'saved':", "'invalid_response':"):
        assert catalog.count(key) == 11


def test_legacy_inquiry_table_gets_unique_case_reference_index(tmp_path):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError

    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE inquiry (id INTEGER PRIMARY KEY, case_ref VARCHAR(32))"))
        connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-261121-AAAAAAAAAAAA')"))
    assert ensure_unique_case_reference_index(engine) is True
    assert ensure_unique_case_reference_index(engine) is False
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-261121-AAAAAAAAAAAA')"))
    except IntegrityError:
        pass
    else:
        raise AssertionError("A duplicate case reference was not blocked by the migrated index")
    engine.dispose()


def test_duplicate_legacy_case_references_fail_migration_clearly(tmp_path):
    from sqlalchemy import create_engine, text
    import pytest

    engine = create_engine(f"sqlite:///{tmp_path / 'duplicates.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE inquiry (id INTEGER PRIMARY KEY, case_ref VARCHAR(32))"))
        connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-DUPLICATE')"))
        connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-DUPLICATE')"))
    with pytest.raises(RuntimeError, match="Duplicate non-null inquiry.case_ref"):
        ensure_unique_case_reference_index(engine)
    engine.dispose()


def test_server_errors_include_a_non_sensitive_support_reference():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("def whatsapp_success(", start)
    route = source[start:end]
    assert "support_reference = uuid.uuid4().hex[:12].upper()" in route
    assert "'support_reference': support_reference" in route
    assert "intake_failure support_ref=%s" in route
    assert "error_type=%s" in route
    assert "form.message.data" not in route[route.index("except Exception as exc:", route.index("stage = 'database_commit'")):]
