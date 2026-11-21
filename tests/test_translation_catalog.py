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


def test_admin_copy_is_complete_for_all_bundled_locales():
    translations = _literal_assignment("ADMIN_COPY")
    expected = {"en", "fr", "ar", "ar-tn", "es", "de", "it", "pt", "tr", "zh", "ja"}
    assert set(translations) == expected
    baseline = set(translations["en"])
    for locale, labels in translations.items():
        assert set(labels) == baseline, f"Admin translation keys differ for {locale}"


def test_triage_copy_exists_for_every_admin_locale():
    translations = _literal_assignment("TRIAGE_COPY")
    admin_locales = set(_literal_assignment("ADMIN_COPY"))
    assert set(translations) == admin_locales
    assert all(len(parts) == 8 for parts in translations.values())


def test_missing_required_label_is_added_and_login_kicker_is_not_hardcoded():
    source = APP_SOURCE.read_text(encoding="utf-8")
    assert "FORM_COPY['en']['required_note']" in source
    login_template = (PROJECT_ROOT / "templates" / "admin_login.html").read_text(encoding="utf-8")
    assert "{{ t('login_kicker') }}" in login_template
    assert "RESTRICTED ACCESS / TEAM" not in login_template


def test_admin_shell_copy_covers_the_four_added_locales():
    shell = _literal_assignment("ADMIN_SHELL_COPY")
    assert set(shell) == {"pt", "tr", "zh", "ja"}
    required = {"login", "username", "password", "sign_in", "logout", "status_label", "new", "reviewing", "closed", "nav_home", "nav_contact", "cat_recovery", "cat_hacked", "cat_impersonation", "cat_scam", "cat_privacy", "cat_reputation", "cat_compliance", "cat_security", "cat_risk", "cat_other", "platform_none", "platform_instagram", "platform_facebook", "platform_tiktok", "platform_google", "platform_x", "platform_linkedin", "platform_other", "priority_normal", "priority_high", "priority_critical"}
    for locale, labels in shell.items():
        assert required <= set(labels), f"Admin shell labels missing for {locale}"


def test_app_seeds_admin_locales_before_triage_translations_are_applied():
    source = APP_SOURCE.read_text(encoding="utf-8")
    assert source.index("merge_locale_translations(") < source.index("TRIAGE_COPY =")
    assert "'pt': ('Português', 'ltr')" in source
    assert "'tr': ('Türkçe', 'ltr')" in source
    assert "'zh': ('简体中文', 'ltr')" in source
    assert "'ja': ('日本語', 'ltr')" in source


def test_translation_catalog_build_does_not_reference_unregistered_locales():
    from security_utils import merge_locale_translations

    catalog = _literal_assignment("LANGS")
    catalog["ar-tn"] = {**catalog["ar"], "name": "تونسي / العربية", "dir": "rtl"}
    admin_copy = _literal_assignment("ADMIN_COPY")
    catalog = merge_locale_translations(
        catalog,
        admin_copy,
        {
            "pt": ("Português", "ltr"),
            "tr": ("Türkçe", "ltr"),
            "zh": ("简体中文", "ltr"),
            "ja": ("日本語", "ltr"),
        },
    )
    shell_copy = _literal_assignment("ADMIN_SHELL_COPY")
    for locale, labels in shell_copy.items():
        catalog[locale].update(labels)
    login_kicker = _literal_assignment("ADMIN_LOGIN_KICKER")
    for locale, label in login_kicker.items():
        catalog[locale]["login_kicker"] = label

    assert set(admin_copy) <= set(catalog)
    for locale in admin_copy:
        for key in ("admin_title", "admin_subtitle", "login", "username", "password", "sign_in", "login_kicker", "new", "reviewing", "closed"):
            assert catalog[locale].get(key), f"{locale} is missing {key}"
