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
    assert "max_age=7 * 24 * 60 * 60" in source
    assert "WTF_CSRF_TIME_LIMIT=timedelta(hours=12)" in source
    template = (ROOT / "templates/contact.html").read_text(encoding="utf-8")
    assert template.count('type="submit"') == 1
    assert "form.hidden_tag()" in template
    assert "form.case_ref()" not in template


def test_case_replay_is_checked_before_insert_and_commit_is_before_handoff():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert route.index("Inquiry.query.filter_by(case_ref=submitted_ref).first()") < route.index("stage = 'case_prepare'")
    assert "human_answer" not in route and "expected_answer" not in route
    commit_path = route[route.index("stage = 'database_commit'"):]
    assert commit_path.index("db.session.commit()") < commit_path.index("redirect(url_for('case_ready'")
    assert "except IntegrityError" in route
    assert "intake_failure support_ref=%s case_ref=%s stage=%s" in route


def test_intake_uses_normal_post_and_does_not_intercept_submission_with_ajax():
    js = (ROOT / "static/js/app.js").read_text(encoding="utf-8")
    form = (ROOT / "templates/contact.html").read_text(encoding="utf-8")
    assert 'method="post"' in form
    assert 'id="case-create-form"' in form
    assert 'fetch(form.action' not in js
    assert 'case-intake-form' not in js


def test_db_health_endpoint_is_available_without_exposing_connection_details():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "@app.get('/health/db')" in source
    assert "'database': 'reachable'" in source
    assert "'database': 'unavailable'" in source


def test_csrf_expiry_copy_is_translated_and_does_not_mention_math_challenge():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("INTAKE_ERROR_COPY =")
    end = source.index("for _locale, _copy in INTAKE_ERROR_COPY.items()", start)
    catalog = source[start:end]
    locales = ("'en':", "'fr':", "'ar':", "'ar-tn':", "'es':", "'de':", "'it':", "'pt':", "'tr':", "'zh':", "'ja':")
    for locale in locales:
        assert locale in catalog
    assert 'arithmetic' not in catalog.lower()
    assert 'security question' not in catalog.lower()


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
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert "support_reference = uuid.uuid4().hex[:12].upper()" in route
    assert "support_reference = uuid.uuid4().hex[:12].upper()" in route
    assert "intake_failure support_ref=%s" in route
    assert "error_type=%s" in route
    assert "form.message.data" not in route[route.index("except Exception as exc:", route.index("stage = 'database_commit'")):]


def test_optional_intake_fields_are_safe_when_left_blank():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    start = source.index("def contact():")
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    for field in ("phone", "incident_date", "account_handle", "evidence_url"):
        assert f"(form.{field}.data or '').strip()" in route
