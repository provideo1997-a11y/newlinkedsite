from pathlib import Path
from security_utils import sqlalchemy_engine_options, ensure_unique_case_reference_index

ROOT = Path(__file__).resolve().parents[1]


def test_postgres_driver_has_bounded_connect_lock_statement_and_pool_waits():
    options = sqlalchemy_engine_options('postgresql+psycopg://user:pass@host/db')
    assert options['pool_timeout'] == 5
    assert options['pool_size'] == 2
    assert options['max_overflow'] == 1
    assert options['connect_args']['connect_timeout'] == 5
    assert 'statement_timeout=12000' in options['connect_args']['options']
    assert 'lock_timeout=5000' in options['connect_args']['options']


def test_sqlite_has_bounded_lock_wait():
    options = sqlalchemy_engine_options('sqlite:////tmp/yakuza.db')
    assert options['connect_args']['timeout'] == 5


def test_intake_has_no_extra_contact_choice_or_custom_form_token():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    form = source[source.index('class InquiryForm'):source.index('class LoginForm')]
    assert 'contact_method=' not in form
    assert 'case_token' not in form
    assert 'human_answer' not in form
    template = (ROOT / 'templates/contact.html').read_text(encoding='utf-8')
    assert template.count('type="submit"') == 1
    assert 'form.hidden_tag()' in template
    assert 'contact-choice' not in template


def test_case_is_saved_before_redirect_to_signed_second_page():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert 'case_ref = ' in route
    assert 'db.session.add(item)' in route
    assert route.index('db.session.commit()') < route.index("redirect(url_for('case_ready', token=issue_case_handoff_token(case_ref)), code=303)")
    assert "contact_method='whatsapp'" in route
    assert 'db.session.rollback()' in route
    assert 'fetch(' not in route


def test_db_health_endpoint_is_available_without_exposing_connection_details():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "@app.get('/health/db')" in source
    assert "'database': 'reachable'" in source
    assert "'database': 'unavailable'" in source


def test_optional_intake_fields_are_safe_when_left_blank():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    for field in ('phone', 'incident_date', 'account_handle', 'evidence_url'):
        assert f"(form.{field}.data or '').strip()" in route


def test_whatsapp_number_is_validated_before_any_case_is_committed():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert "normalize_whatsapp_number(os.environ.get('WHATSAPP_NUMBER', ''))" in route
    assert route.index('normalize_whatsapp_number(') < route.index('db.session.commit()')


def test_duplicate_case_reference_index_migration(tmp_path):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE inquiry (id INTEGER PRIMARY KEY, case_ref VARCHAR(32))'))
        connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-261121-AAAAAAAAAAAA')"))
    assert ensure_unique_case_reference_index(engine) is True
    assert ensure_unique_case_reference_index(engine) is False
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO inquiry (case_ref) VALUES ('YKZ-261121-AAAAAAAAAAAA')"))
    except IntegrityError:
        pass
    else:
        raise AssertionError('Duplicate case reference was not blocked')
    engine.dispose()
