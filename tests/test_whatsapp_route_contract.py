from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_case_is_committed_before_redirect_to_second_page():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert 'db.session.commit()' in route
    commit_path = route[route.index("stage = 'database_commit'"):]
    assert commit_path.index('db.session.commit()') < commit_path.index("redirect(url_for('case_ready'")
    assert "code=303" in route
    assert "build_case_whatsapp_url(configured_whatsapp, item)" in route
    assert "contact_method='whatsapp'" in route
    assert 'db.session.rollback()' in route


def test_second_page_loads_saved_case_and_contains_server_generated_whatsapp_link():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index("@app.get('/case/ready/<token>')")
    end = source.index('@app.errorhandler(429)', start)
    route = source[start:end]
    assert '_case_handoff_serializer.loads(token, max_age=24 * 60 * 60)' in route
    assert 'Inquiry.query.filter_by(case_ref=case_ref).first_or_404()' in route
    assert "build_case_whatsapp_url(os.environ.get('WHATSAPP_NUMBER', ''), item)" in route
    assert "render_template('case_ready.html', item=item, whatsapp_url=whatsapp_url)" in route


def test_whatsapp_handoff_page_has_one_explicit_whatsapp_link_and_no_extra_actions():
    page = (ROOT / 'templates/case_ready.html').read_text(encoding='utf-8')
    assert page.count('id="case-ready-whatsapp"') == 1
    assert 'href="{{ whatsapp_url }}"' in page
    assert "t('case_ready_send')" in page
    assert 'target="_blank"' not in page
    assert page.count('<a ') == 1


def test_whatsapp_message_is_built_from_saved_case_with_complete_report():
    helper = (ROOT / 'whatsapp_utils.py').read_text(encoding='utf-8')
    for term in ('REQUESTER DETAILS', 'INCIDENT DETAILS', 'USER-SUBMITTED DESCRIPTION', 'GENERATED TRIAGE REPORT', 'Risk indicator score'):
        assert term in helper


def test_whatsapp_configuration_checked_before_case_commit():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    route = source[start:end]
    assert "os.environ.get('WHATSAPP_NUMBER', '')" in route
    assert route.index('normalize_whatsapp_number(configured_whatsapp)') < route.index('db.session.commit()')


def test_case_ready_page_is_non_cacheable_and_referrer_is_suppressed():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert "request.path.startswith('/case/ready/')" in source
    assert "resp.headers['Referrer-Policy'] = 'no-referrer'" in source
