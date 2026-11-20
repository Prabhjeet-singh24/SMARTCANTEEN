"""Database helpers: SQLite and PostgreSQL connection handling and schema creation."""
import os
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse

from flask import current_app, g

try:
    import psycopg2
    from psycopg2.extras import DictCursor
    PG_INTEGRITY_ERROR = psycopg2.IntegrityError
except ImportError:
    psycopg2 = None
    DictCursor = None
    PG_INTEGRITY_ERROR = sqlite3.IntegrityError

try:
    from models import SCHEMA_POSTGRES, SCHEMA_SQLITE
except ImportError:
    from backend.models import SCHEMA_POSTGRES, SCHEMA_SQLITE

# Unified IntegrityError tuple so route handlers catch constraint violations on both engines
DBIntegrityError = (sqlite3.IntegrityError, PG_INTEGRITY_ERROR)


def is_pg_url(url):
    """Check if the provided path/URI indicates a PostgreSQL database."""
    if not isinstance(url, str):
        return False
    u = url.strip().lower()
    return u.startswith("postgresql://") or u.startswith("postgres://")


def sanitize_db_url(raw_url):
    """Sanitize database URL, handling password brackets, unencoded @, and postgres:// prefix."""
    raw_url = raw_url.strip().strip('"').strip("'")
    if raw_url.startswith("postgres://"):
        raw_url = "postgresql://" + raw_url[len("postgres://"):]

    m = re.match(r"^(postgresql://[^:]+:)(.*)@([^@]+)$", raw_url)
    if m:
        prefix = m.group(1)
        pwd = m.group(2)
        rest = m.group(3)
        if pwd.startswith("[") and pwd.endswith("]"):
            pwd = pwd[1:-1]
        encoded_pwd = quote_plus(unquote(pwd))
        raw_url = f"{prefix}{encoded_pwd}@{rest}"

    return raw_url


class PgCursorWrapper:
    """Cursor wrapper that translates SQLite '?' placeholders to '%s' and tracks lastrowid."""

    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None

    def _convert_sql(self, sql):
        # Convert SQLite ? parameter placeholders to PostgreSQL %s
        return re.sub(r"\?", "%s", sql)

    def execute(self, sql, params=None):
        raw_sql = sql.strip()
        is_insert = raw_sql.upper().startswith("INSERT INTO ")
        has_returning = " RETURNING " in raw_sql.upper()

        converted_sql = self._convert_sql(raw_sql)

        if is_insert and not has_returning:
            # Append RETURNING id to capture lastrowid like SQLite
            converted_sql += " RETURNING id"
            if params is not None:
                self._cur.execute(converted_sql, params)
            else:
                self._cur.execute(converted_sql)
            try:
                row = self._cur.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                self.lastrowid = None
            return self

        if params is not None:
            self._cur.execute(converted_sql, params)
        else:
            self._cur.execute(converted_sql)
        return self

    def executemany(self, sql, seq_of_params):
        converted_sql = self._convert_sql(sql.strip())
        self._cur.executemany(converted_sql, seq_of_params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)

    @property
    def description(self):
        return self._cur.description

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()


class PgConnectionWrapper:
    """Connection wrapper ensuring API compatibility with SQLite connection object."""

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PgCursorWrapper(self._conn.cursor(cursor_factory=DictCursor))

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def executemany(self, sql, seq_of_params):
        cur = self.cursor()
        return cur.executemany(sql, seq_of_params)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def executescript(self, script):
        with self._conn.cursor() as cur:
            cur.execute(script)
        self._conn.commit()


def _connect_postgres(url):
    if psycopg2 is None:
        raise RuntimeError("psycopg2-binary is required for PostgreSQL connections. Install it with: pip install psycopg2-binary")

    clean_url = sanitize_db_url(url)
    parsed = urlparse(clean_url)

    # If pooler host is used but username is missing the .<ref> suffix, automatically fix it
    if parsed.hostname and "pooler.supabase.com" in parsed.hostname:
        user = parsed.username or "postgres"
        if "." not in user:
            ref = "wuwpglwvjqrhcdkrzrto"
            user = f"{user}.{ref}"
            pwd = unquote(parsed.password or "")
            port = parsed.port or 5432
            dbname = parsed.path.lstrip("/") or "postgres"
            raw_conn = psycopg2.connect(
                host=parsed.hostname,
                port=port,
                user=user,
                password=pwd,
                dbname=dbname,
                sslmode="require",
                connect_timeout=10,
            )
            return PgConnectionWrapper(raw_conn)

    # Attempt connection with provided URL
    try:
        raw_conn = psycopg2.connect(clean_url, connect_timeout=6)
        return PgConnectionWrapper(raw_conn)
    except Exception as err:
        # Check for Supabase direct IPv6 address failure -> fallback to IPv4 connection pooler
        m = re.match(r"^db\.([a-z0-9]+)\.supabase\.co$", parsed.hostname or "")
        ref = m.group(1) if m else "wuwpglwvjqrhcdkrzrto"
        pooler_host = "aws-0-ap-south-1.pooler.supabase.com"
        user = parsed.username or "postgres"
        if not user.endswith(f".{ref}"):
            user = f"{user}.{ref}"
        pwd = unquote(parsed.password or "")
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") or "postgres"

        raw_conn = psycopg2.connect(
            host=pooler_host,
            port=port,
            user=user,
            password=pwd,
            dbname=dbname,
            sslmode="require",
            connect_timeout=10,
        )
        return PgConnectionWrapper(raw_conn)


def connect(target):
    """Open a connection (SQLite or PostgreSQL) depending on the target string."""
    if is_pg_url(str(target)):
        return _connect_postgres(str(target))

    Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_schema(conn):
    if isinstance(conn, PgConnectionWrapper):
        conn.executescript(SCHEMA_POSTGRES)
    else:
        conn.executescript(SCHEMA_SQLITE)
        conn.commit()
