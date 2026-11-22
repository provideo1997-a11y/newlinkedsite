from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _route():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index('def contact():')
    end = source.index("@app.get('/case/ready/<token>')", start)
    return source[start:end]


def test_case_is_committed_before_redirect_to_second_page():
    route = _route()
    assert 'db.session.commit()' in route
    assert route.index('handoff_token = issue_case_handoff_token(case_ref)') < route.index('db.session.commit()')
    assert route.index('db.session.commit()') < route.index("redirect(url_for('case_ready', token=handoff_token), code=303)")
    assert 'build_case_whatsapp_url(whatsapp_number, item)' in route
    assert "contact_method='whatsapp'" in route
    assert 'db.session.rollback()' in route


def test_second_page_loads_saved_case_and_contains_server_generated_whatsapp_link():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    start = source.index("@app.get('/case/ready/<token>')")
    end = source.index('@app.errorhandler(429)', start)
    route = source[start:end]
    assert '_case_handoff_serializer.loads(token, max_age=24 * 60 * 60)' in route
    assert 'Inquiry.query.filter_by(case_ref=case_ref).first_or_404()' in route
    assert "build_case_whatsapp_url(os.environ.get('WHATSAPP_NUMBER', '4917642484892'), item)" in route
    assert "render_template('case_ready.html', item=item, whatsapp_url=whatsapp_url)" in route


def test_second_page_has_one_whatsapp_link_and_no_extra_actions():
    page = (ROOT / 'templates/case_ready.html').read_text(encoding='utf-8')
    assert page.count('id="case-ready-whatsapp"') == 1
    assert 'data-whatsapp-url="{{ whatsapp_url }}"' in page
    assert '<button' in page and 'type="button"' in page
    assert 'href="{{ whatsapp_url }}"' not in page
    assert "url_for('home')" in page
    assert page.count('data-whatsapp-url="{{ whatsapp_url }}"') == 1


def test_whatsapp_message_contains_full_saved_case_report():
    helper = (ROOT / 'whatsapp_utils.py').read_text(encoding='utf-8')
    for term in ('REQUESTER DETAILS', 'INCIDENT DETAILS', 'USER-SUBMITTED DESCRIPTION', 'GENERATED TRIAGE REPORT', 'Risk indicator score'):
        assert term in helper
