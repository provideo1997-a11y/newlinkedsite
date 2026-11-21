import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = PROJECT_ROOT / "app.py"


def _literal_assignment(name):
    tree = ast.parse(APP_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Could not find literal assignment for {name}")


def test_every_locale_has_all_new_ui_labels():
    ui_copy = _literal_assignment("UI_COPY")
    expected_locales = {"en", "fr", "ar", "ar-tn", "es", "de", "it", "pt", "tr", "zh", "ja"}
    assert set(ui_copy) == expected_locales
    required = {
        "skip_to_content", "primary_navigation", "language_label", "back_to_top",
        "dashboard_metrics", "dashboard_filter", "dashboard_search_placeholder",
        "dashboard_status_filter", "dashboard_all_statuses", "dashboard_no_matches",
        "dashboard_showing", "cases_table_label", "dashboard_recent_limit",
        "copy_reference", "reference_copied", "copy_failed", "print_report",
        "invalid_credentials", "case_status_updated", "submitting_request",
        "whatsapp_consent_label", "whatsapp_consent_required", "whatsapp_handoff_title",
        "whatsapp_handoff_body", "whatsapp_open_button", "whatsapp_waiting",
        "case_save_failed", "submission_slow",
    }
    for locale, labels in ui_copy.items():
        assert set(labels) == required, f"{locale} has a different UI translation catalog"
        assert all(labels[key] for key in required), f"{locale} has an empty UI label"


def test_shared_shell_has_progressive_loader_skip_link_and_main_landmark():
    base = (PROJECT_ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    assert 'class="skip-link" href="#main-content"' in base
    assert '<main id="main-content" tabindex="-1">' in base
    assert 'aria-controls="main-nav"' in base
    assert 'role="status" aria-live="polite"' in base


def test_dashboard_has_accessible_search_filters_and_loaded_row_limit_disclosure():
    dashboard = (PROJECT_ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
    assert 'id="case-search"' in dashboard
    assert 'id="case-status-filter"' in dashboard
    assert 'data-case-row data-case-status=' in dashboard
    assert 'id="case-filter-empty" hidden' in dashboard
    assert "dashboard_recent_limit" in dashboard
    assert "t('flag_' ~ flag.strip())" in dashboard
    assert 'role="region" tabindex="0"' in dashboard


def test_case_report_has_copy_and_print_controls():
    report = (PROJECT_ROOT / "templates" / "case_detail.html").read_text(encoding="utf-8")
    assert 'data-copy-reference=' in report
    assert 'id="print-report"' in report
    assert 'id="copy-feedback" role="status" aria-live="polite"' in report


def test_intake_keeps_native_validation_and_counter_description():
    contact = (PROJECT_ROOT / "templates" / "contact.html").read_text(encoding="utf-8")
    assert 'id="case-create-form"' in contact
    assert "type='date'" in contact
    assert "**{'aria-describedby': 'story-count-hint'}" in contact


def test_client_scripts_cover_filter_copy_print_and_bfcache_restore():
    script = (PROJECT_ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "case-search" in script and "case-status-filter" in script
    assert "data-copy-reference" in script and "print-report" in script
    assert "document.documentElement.classList.add('js')" in script


def test_loader_is_progressive_and_print_reduced_motion_styles_exist():
    css = (PROJECT_ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    script = (PROJECT_ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert ".loader { display: none; }" in css
    assert ".js .loader { display: grid; }" in css
    assert "@media print" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "document.documentElement.classList.add('js')" in script
