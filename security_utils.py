import re


def normalize_whatsapp_number(raw: str | None) -> str | None:
    """Normalize international phone notation to wa.me digits-only format."""
    digits = re.sub(r"[^0-9]", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if not (8 <= len(digits) <= 15) or not digits.isdigit() or digits.startswith("0"):
        return None
    # German national trunk prefix must not follow country code +49.
    if digits.startswith("49") and len(digits) > 2 and digits[2] == "0":
        return None
    return digits


def normalize_database_url(raw: str | None, fallback: str) -> str:
    """Select psycopg 3 explicitly for PostgreSQL URLs; preserve other DB URLs."""
    value = (raw or "").strip()
    if not value:
        return fallback
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://"): ]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://"): ]
    if value.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + value[len("postgresql+psycopg2://"): ]
    return value


def merge_locale_translations(locale_catalog: dict, translations: dict, metadata: dict | None = None) -> dict:
    """Add missing locale dictionaries from English fallback, then overlay translations."""
    if "en" not in locale_catalog:
        raise ValueError("English fallback locale is required")
    metadata = metadata or {}
    for code, labels in translations.items():
        if code not in locale_catalog:
            name, direction = metadata.get(code, (code, "ltr"))
            locale_catalog[code] = {**locale_catalog["en"], "name": name, "dir": direction}
        locale_catalog[code].update(labels)
    return locale_catalog


def csv_safe(value) -> str:
    """Prefix spreadsheet formula-like values so CSV cells open as text."""
    text = "" if value is None else str(value)
    # Strip common whitespace/control/BOM prefixes before checking what a spreadsheet
    # might interpret. Preserve the original value after adding the text marker.
    candidate = text.lstrip("\ufeff\u200b\u200c\u200d \t\r\n\v\f")
    if candidate.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text
