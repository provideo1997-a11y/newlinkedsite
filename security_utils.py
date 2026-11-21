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


def sqlalchemy_engine_options(database_uri: str) -> dict:
    """Return bounded SQLAlchemy pool/driver timeouts for the configured database.

    PostgreSQL uses psycopg 3. A connection attempt, lock wait, or statement is
    bounded so an unavailable database cannot leave an intake request waiting
    until the web worker is killed. SQLite receives a bounded lock wait too.
    """
    uri = (database_uri or "").strip().lower()
    options = {"pool_pre_ping": True, "pool_recycle": 300}
    if uri.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
        options.update({
            "pool_size": 2,
            "max_overflow": 1,
            "pool_timeout": 5,
            "connect_args": {
                "connect_timeout": 5,
                "options": (
                    "-c statement_timeout=12000 "
                    "-c lock_timeout=5000 "
                    "-c idle_in_transaction_session_timeout=15000"
                ),
            },
        })
    elif uri.startswith("sqlite:"):
        options["connect_args"] = {"timeout": 5}
    return options


def ensure_unique_case_reference_index(engine) -> bool:
    """Ensure an existing Inquiry table enforces unique, non-null case references.

    SQLAlchemy ``create_all`` does not add constraints/indexes to a table that
    already existed before the model gained ``unique=True``. The idempotent
    intake path relies on this invariant for concurrent retries, so add an
    explicit unique index when the database lacks one. Returns True only when
    an index was created. Existing duplicate non-null references are reported
    as a migration error instead of silently weakening duplicate protection.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "case_ref" not in {column["name"] for column in inspector.get_columns("inquiry")}:
        raise RuntimeError("The inquiry.case_ref migration must run before its unique index migration.")

    for index in inspector.get_indexes("inquiry"):
        if index.get("unique") and index.get("column_names") == ["case_ref"]:
            return False
    for constraint in inspector.get_unique_constraints("inquiry"):
        if constraint.get("column_names") == ["case_ref"]:
            return False

    with engine.connect() as connection:
        duplicate = connection.execute(text(
            "SELECT case_ref FROM inquiry "
            "WHERE case_ref IS NOT NULL "
            "GROUP BY case_ref HAVING COUNT(*) > 1 LIMIT 1"
        )).first()
    if duplicate:
        raise RuntimeError(
            "Duplicate non-null inquiry.case_ref values exist. Resolve them before enabling safe case retries."
        )

    with engine.begin() as connection:
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_inquiry_case_ref ON inquiry (case_ref)"
        ))
    return True
