from security_utils import (
    csv_safe,
    merge_locale_translations,
    normalize_database_url,
    normalize_whatsapp_number,
)


def test_whatsapp_normalizes_international_prefixes():
    assert normalize_whatsapp_number("0049 171 2345678") == "491712345678"
    assert normalize_whatsapp_number("+49 (171) 234-5678") == "491712345678"
    assert normalize_whatsapp_number("491712345678") == "491712345678"


def test_whatsapp_rejects_bad_numbers():
    assert normalize_whatsapp_number("") is None
    assert normalize_whatsapp_number("0049 0171 1234567") is None
    assert normalize_whatsapp_number("123") is None
    assert normalize_whatsapp_number("+00 nonsense") is None


def test_csv_formula_prefixes_are_neutralized():
    for dangerous in ("=1+1", "+SUM(A1:A2)", "-1+2", "@SUM(A1)", "\t=1+1", "\r=1+1", "\ufeff=1+1", "\u200b=1+1"):
        assert csv_safe(dangerous).startswith("'")
    assert csv_safe("ordinary text") == "ordinary text"
    assert csv_safe(None) == ""


def test_postgres_urls_use_installed_psycopg3_driver():
    assert normalize_database_url("postgres://user:pass@host/db", "fallback").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql://user:pass@host/db", "fallback").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql+psycopg2://user:pass@host/db", "fallback").startswith("postgresql+psycopg://")
    assert normalize_database_url("sqlite:///local.db", "fallback") == "sqlite:///local.db"
    assert normalize_database_url(None, "fallback") == "fallback"


def test_missing_admin_locales_are_seeded_from_english_and_overlaid():
    catalog = {"en": {"name": "English", "dir": "ltr", "login": "Sign in", "save": "Save"}}
    copies = {"pt": {"login": "Entrar"}, "tr": {"login": "Giriş yap"}}
    result = merge_locale_translations(catalog, copies, {"pt": ("Português", "ltr"), "tr": ("Türkçe", "ltr")})
    assert result["pt"]["login"] == "Entrar"
    assert result["pt"]["save"] == "Save"
    assert result["pt"]["name"] == "Português"
    assert result["tr"]["name"] == "Türkçe"
    assert result["en"]["login"] == "Sign in"
