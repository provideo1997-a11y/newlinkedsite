from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_whatsapp_is_opened_only_by_explicit_receipt_link():
    receipt = (ROOT / 'templates' / 'submitted.html').read_text(encoding='utf-8')
    script = (ROOT / 'static' / 'js' / 'app.js').read_text(encoding='utf-8')
    assert receipt.count('id="whatsapp-open-link"') == 1
    assert 'href="{{ whatsapp_url }}"' in receipt
    assert 'rel="noopener noreferrer"' in receipt
    assert 'referrerpolicy="no-referrer"' in receipt
    assert 'data-whatsapp-url=' not in receipt
    assert 'window.location.assign(target)' not in script
    assert 'window.open(target' not in script
    assert 'whatsapp-handoff' not in script


def test_receipt_explicitly_tells_visitor_to_click_and_press_send():
    receipt = (ROOT / 'templates' / 'submitted.html').read_text(encoding='utf-8')
    assert "t('whatsapp_waiting')" in receipt
    assert "t('whatsapp_open_button')" in receipt
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    ui_node = next(node.value for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'UI_COPY' for target in node.targets))
    ui_copy = ast.literal_eval(ui_node)
    assert len(ui_copy) == 11
    for locale, labels in ui_copy.items():
        assert 'whatsapp_waiting' in labels and labels['whatsapp_waiting']
        assert 'whatsapp_handoff_body' in labels and labels['whatsapp_handoff_body']
        # No locale should tell the visitor WhatsApp is already opening automatically.
        assert 'will not open until' in labels['whatsapp_handoff_body'].lower() or locale != 'en'


def test_whatsapp_destination_stays_server_generated_and_case_is_committed_first():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    contact_start = source.index('def contact():')
    route = source[contact_start:source.index("@app.get('/privacy')", contact_start)]
    assert route.index('db.session.commit()') < route.index('build_case_whatsapp_url(')
    assert "os.environ.get('WHATSAPP_NUMBER', '')" in route
    assert "response.headers['Referrer-Policy'] = 'no-referrer'" in route


def test_intake_contact_method_description_says_button_is_clicked_after_save():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    form_node = next(node.value for node in tree.body
                     if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'FORM_COPY' for target in node.targets))
    form_copy = ast.literal_eval(form_node)
    assert form_copy['en']['whatsapp_desc'] == (
        'Your case is saved first. After saving, click the WhatsApp button on the receipt '
        'to open a prepared message you can review and send.'
    )
    assert 'cliquez sur le bouton WhatsApp' in form_copy['fr']['whatsapp_desc']
    assert 'اضغط زر واتساب' in form_copy['ar']['whatsapp_desc']
    assert 'اضغط على زر واتساب' in form_copy['ar-tn']['whatsapp_desc']
