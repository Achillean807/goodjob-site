#!/usr/bin/env python3
"""
Murayama Good Job Site — API + Static File Server

A lightweight HTTP server built on the standard library that serves static
files and exposes JSON API endpoints for article management.

Usage:
    python3 server.py
    python3 server.py --port 10814
    python3 server.py --bind 0.0.0.0 --port 8080
"""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time
import io
import uuid
from http import HTTPStatus
try:
    from PIL import Image as _PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
try:
    import pillow_avif  # noqa: F401 -- registers AVIF format with Pillow if installed
except ImportError:
    pass
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Paths (resolved relative to the script's own directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTICLES_PATH = os.path.join(DATA_DIR, "articles.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
ACCOUNTS_PATH = os.path.join(DATA_DIR, "accounts.json")
DB_PATH = os.path.join(DATA_DIR, "goodjob.sqlite3")
DATABASE_URL = os.environ.get("GOODJOB_DATABASE_URL", "").strip()
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")

VALID_ROLES = {"admin", "editor", "viewer", "custom"}
VALID_PERMISSIONS = {
    "articles.read",
    "articles.write",
    "articles.delete",
    "uploads.write",
    "accounts.manage",
}
ACCOUNT_PUBLIC_FIELDS = ("username", "name", "role", "enabled", "permissions",
                         "createdAt", "updatedAt")

# R2 / CDN config — admin uploads go directly to R2 object storage.
# Override via env vars for dev / alternative deployments.
R2_REMOTE = os.environ.get("GOODJOB_R2_REMOTE", "r2:goodjob-images")
CDN_DOMAIN = os.environ.get("GOODJOB_CDN_DOMAIN", "https://goodjob-img.weddingwishlove.com")
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")
WEBP_QUALITY = int(os.environ.get("GOODJOB_WEBP_QUALITY", "90"))
# Cap uploaded images at this pixel width before WebP encoding — huge raw photos
# (iPhone ProRAW, mirrorless 8000px JPEGs) would otherwise stall Pillow for tens
# of seconds and produce unnecessarily large output.
MAX_UPLOAD_WIDTH = int(os.environ.get("GOODJOB_MAX_UPLOAD_WIDTH", "3000"))
# Thumbnail config — small preview variant for admin gallery / table.
THUMB_WIDTH = int(os.environ.get("GOODJOB_THUMB_WIDTH", "400"))
THUMB_QUALITY = int(os.environ.get("GOODJOB_THUMB_QUALITY", "75"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path):
    """Read and parse a JSON file.  Returns None on any error."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _write_json_atomic(path, data):
    """Write *data* as JSON to *path* atomically via a temp file + os.replace."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp_path, path)


def _db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _using_postgres():
    return bool(DATABASE_URL)


def _pg_connect():
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as exc:
        raise RuntimeError(
            "GOODJOB_DATABASE_URL is set, but psycopg2 is not installed"
        ) from exc
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _init_db():
    """Create database tables and import legacy JSON data on first boot."""
    if _using_postgres():
        _init_pg_db()
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    with _db_connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            featured INTEGER NOT NULL DEFAULT 0,
            featured_order INTEGER NOT NULL DEFAULT 0,
            hero_image TEXT NOT NULL DEFAULT '',
            link_url TEXT,
            video_id TEXT,
            video_vertical INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            row_index INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS article_images (
            article_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            url TEXT NOT NULL,
            PRIMARY KEY (article_id, position),
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS article_awards (
            article_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            name TEXT,
            year INTEGER,
            level TEXT,
            category TEXT,
            project_name TEXT,
            role TEXT,
            entrant TEXT,
            detail_url TEXT,
            url TEXT,
            label TEXT,
            PRIMARY KEY (article_id, position),
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'custom',
            enabled INTEGER NOT NULL DEFAULT 1,
            salt TEXT NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS account_permissions (
            username TEXT NOT NULL,
            permission TEXT NOT NULL,
            PRIMARY KEY (username, permission),
            FOREIGN KEY (username) REFERENCES accounts(username) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
        """)

        # 修補 C：SQLite 從 JSON seed 預設禁用 — 避免「SQLite 為空 + 舊版
        # data/articles.json 殘留」的組合在主機端誤觸覆蓋線上資料的災難。
        # 啟用這條 seed 路徑必須顯式設 GOODJOB_ALLOW_JSON_SEED=1，
        # migrate 流程會自動開啟。
        if os.environ.get("GOODJOB_ALLOW_JSON_SEED", "").strip() != "1":
            return

        if conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 0:
            articles = _read_articles_json()
            if articles:
                _replace_articles(conn, articles)
                print(f"[db] imported {len(articles)} article(s) from legacy JSON")

        if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
            accounts = _read_accounts_json()
            if accounts:
                _replace_accounts(conn, accounts)
                print(f"[db] imported {len(accounts)} account(s) from legacy JSON")

        if conn.execute("SELECT COUNT(*) FROM config").fetchone()[0] == 0:
            cfg = _read_config_json()
            if cfg:
                _replace_config(conn, cfg)
                print("[db] imported legacy config JSON")


def _init_pg_db():
    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                featured INTEGER NOT NULL DEFAULT 0,
                featured_order INTEGER NOT NULL DEFAULT 0,
                hero_image TEXT NOT NULL DEFAULT '',
                link_url TEXT,
                video_id TEXT,
                video_vertical INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                row_index INTEGER NOT NULL DEFAULT 0
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS article_images (
                article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                url TEXT NOT NULL,
                PRIMARY KEY (article_id, position)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS article_awards (
                article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                name TEXT,
                year INTEGER,
                level TEXT,
                category TEXT,
                project_name TEXT,
                role TEXT,
                entrant TEXT,
                detail_url TEXT,
                url TEXT,
                label TEXT,
                PRIMARY KEY (article_id, position)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'custom',
                enabled INTEGER NOT NULL DEFAULT 1,
                salt TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS account_permissions (
                username TEXT NOT NULL REFERENCES accounts(username) ON DELETE CASCADE,
                permission TEXT NOT NULL,
                PRIMARY KEY (username, permission)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
            """)


def _read_config_json():
    return _read_json(CONFIG_PATH) or {}


def _read_articles_json():
    data = _read_json(ARTICLES_PATH)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("articles"), list):
        return data["articles"]
    return []


def _read_accounts_json():
    data = _read_json(ACCOUNTS_PATH)
    if isinstance(data, dict) and isinstance(data.get("accounts"), list):
        return data["accounts"]
    return []


def _replace_articles(conn, articles):
    conn.execute("DELETE FROM article_awards")
    conn.execute("DELETE FROM article_images")
    conn.execute("DELETE FROM articles")
    for row_index, article in enumerate(articles):
        article_id = str(article.get("id") or "")
        if not article_id:
            continue
        conn.execute("""
            INSERT INTO articles (
                id, title, description, category, featured, featured_order,
                hero_image, link_url, video_id, video_vertical, sort_order,
                created_at, updated_at, row_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            article.get("title") or "",
            article.get("description") or "",
            article.get("category") or "",
            1 if article.get("featured") else 0,
            int(article.get("featuredOrder") or 0),
            article.get("heroImage") or "",
            article.get("linkUrl"),
            article.get("videoId"),
            1 if article.get("videoVertical") else 0,
            int(article.get("sortOrder") or 0),
            article.get("createdAt"),
            article.get("updatedAt"),
            row_index,
        ))
        for position, url in enumerate(article.get("images") or []):
            if url:
                conn.execute(
                    "INSERT INTO article_images (article_id, position, url) VALUES (?, ?, ?)",
                    (article_id, position, url),
                )
        for position, award in enumerate(article.get("awards") or []):
            conn.execute("""
                INSERT INTO article_awards (
                    article_id, position, name, year, level, category, project_name,
                    role, entrant, detail_url, url, label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article_id,
                position,
                award.get("name"),
                award.get("year"),
                award.get("level"),
                award.get("category"),
                award.get("projectName"),
                award.get("role"),
                award.get("entrant"),
                award.get("detailUrl"),
                award.get("url"),
                award.get("label"),
            ))


def _article_from_row(conn, row):
    article_id = row["id"]
    images = [
        r["url"] for r in conn.execute(
            "SELECT url FROM article_images WHERE article_id = ? ORDER BY position",
            (article_id,),
        )
    ]
    awards = []
    for r in conn.execute(
        "SELECT * FROM article_awards WHERE article_id = ? ORDER BY position",
        (article_id,),
    ):
        award = {
            "name": r["name"],
            "year": r["year"],
            "level": r["level"],
            "category": r["category"],
            "projectName": r["project_name"],
            "role": r["role"],
            "entrant": r["entrant"],
            "detailUrl": r["detail_url"],
            "url": r["url"],
            "label": r["label"],
        }
        awards.append({k: v for k, v in award.items() if v is not None})

    article = {
        "id": article_id,
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "featured": bool(row["featured"]),
        "featuredOrder": row["featured_order"],
        "heroImage": row["hero_image"],
        "images": images,
        "linkUrl": row["link_url"],
        "videoId": row["video_id"],
        "videoVertical": bool(row["video_vertical"]),
        "sortOrder": row["sort_order"],
    }
    if row["created_at"]:
        article["createdAt"] = row["created_at"]
    if row["updated_at"]:
        article["updatedAt"] = row["updated_at"]
    if awards:
        article["awards"] = awards
    return article


def _replace_accounts(conn, accounts):
    conn.execute("DELETE FROM account_permissions")
    conn.execute("DELETE FROM accounts")
    for account in accounts:
        username = account.get("username")
        if not username:
            continue
        conn.execute("""
            INSERT INTO accounts (
                username, name, role, enabled, salt, password_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            account.get("name") or username,
            account.get("role") or "custom",
            1 if account.get("enabled", True) else 0,
            account.get("salt") or "",
            account.get("passwordHash") or "",
            account.get("createdAt"),
            account.get("updatedAt"),
        ))
        for permission in account.get("permissions") or []:
            conn.execute(
                "INSERT OR IGNORE INTO account_permissions (username, permission) VALUES (?, ?)",
                (username, permission),
            )


def _account_from_row(conn, row):
    permissions = [
        r["permission"] for r in conn.execute(
            "SELECT permission FROM account_permissions WHERE username = ? ORDER BY permission",
            (row["username"],),
        )
    ]
    return {
        "username": row["username"],
        "name": row["name"],
        "role": row["role"],
        "enabled": bool(row["enabled"]),
        "permissions": permissions,
        "salt": row["salt"],
        "passwordHash": row["password_hash"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _replace_config(conn, cfg):
    conn.execute("DELETE FROM config")
    for key, value in (cfg or {}).items():
        if value is not None:
            conn.execute(
                "INSERT INTO config (key, value) VALUES (?, ?)",
                (str(key), str(value)),
            )


def _pg_replace_articles(conn, articles):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM article_awards")
        cur.execute("DELETE FROM article_images")
        cur.execute("DELETE FROM articles")
        for row_index, article in enumerate(articles):
            article_id = str(article.get("id") or "")
            if not article_id:
                continue
            cur.execute("""
                INSERT INTO articles (
                    id, title, description, category, featured, featured_order,
                    hero_image, link_url, video_id, video_vertical, sort_order,
                    created_at, updated_at, row_index
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                article_id,
                article.get("title") or "",
                article.get("description") or "",
                article.get("category") or "",
                1 if article.get("featured") else 0,
                int(article.get("featuredOrder") or 0),
                article.get("heroImage") or "",
                article.get("linkUrl"),
                article.get("videoId"),
                1 if article.get("videoVertical") else 0,
                int(article.get("sortOrder") or 0),
                article.get("createdAt"),
                article.get("updatedAt"),
                row_index,
            ))
            for position, url in enumerate(article.get("images") or []):
                if url:
                    cur.execute(
                        "INSERT INTO article_images (article_id, position, url) VALUES (%s, %s, %s)",
                        (article_id, position, url),
                    )
            for position, award in enumerate(article.get("awards") or []):
                cur.execute("""
                    INSERT INTO article_awards (
                        article_id, position, name, year, level, category,
                        project_name, role, entrant, detail_url, url, label
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    article_id,
                    position,
                    award.get("name"),
                    award.get("year"),
                    award.get("level"),
                    award.get("category"),
                    award.get("projectName"),
                    award.get("role"),
                    award.get("entrant"),
                    award.get("detailUrl"),
                    award.get("url"),
                    award.get("label"),
                ))


def _pg_article_from_row(conn, row):
    article_id = row["id"]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT url FROM article_images WHERE article_id = %s ORDER BY position",
            (article_id,),
        )
        images = [r["url"] for r in cur.fetchall()]
        cur.execute(
            "SELECT * FROM article_awards WHERE article_id = %s ORDER BY position",
            (article_id,),
        )
        award_rows = cur.fetchall()

    awards = []
    for r in award_rows:
        award = {
            "name": r["name"],
            "year": r["year"],
            "level": r["level"],
            "category": r["category"],
            "projectName": r["project_name"],
            "role": r["role"],
            "entrant": r["entrant"],
            "detailUrl": r["detail_url"],
            "url": r["url"],
            "label": r["label"],
        }
        awards.append({k: v for k, v in award.items() if v is not None})

    article = {
        "id": article_id,
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "featured": bool(row["featured"]),
        "featuredOrder": row["featured_order"],
        "heroImage": row["hero_image"],
        "images": images,
        "linkUrl": row["link_url"],
        "videoId": row["video_id"],
        "videoVertical": bool(row["video_vertical"]),
        "sortOrder": row["sort_order"],
    }
    if row["created_at"]:
        article["createdAt"] = row["created_at"]
    if row["updated_at"]:
        article["updatedAt"] = row["updated_at"]
    if awards:
        article["awards"] = awards
    return article


def _pg_replace_accounts(conn, accounts):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM account_permissions")
        cur.execute("DELETE FROM accounts")
        for account in accounts:
            username = account.get("username")
            if not username:
                continue
            cur.execute("""
                INSERT INTO accounts (
                    username, name, role, enabled, salt, password_hash, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                account.get("name") or username,
                account.get("role") or "custom",
                1 if account.get("enabled", True) else 0,
                account.get("salt") or "",
                account.get("passwordHash") or "",
                account.get("createdAt"),
                account.get("updatedAt"),
            ))
            for permission in account.get("permissions") or []:
                cur.execute(
                    "INSERT INTO account_permissions (username, permission) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (username, permission),
                )


def _pg_account_from_row(conn, row):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT permission FROM account_permissions WHERE username = %s ORDER BY permission",
            (row["username"],),
        )
        permissions = [r["permission"] for r in cur.fetchall()]
    return {
        "username": row["username"],
        "name": row["name"],
        "role": row["role"],
        "enabled": bool(row["enabled"]),
        "permissions": permissions,
        "salt": row["salt"],
        "passwordHash": row["password_hash"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _pg_replace_config(conn, cfg):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM config")
        for key, value in (cfg or {}).items():
            if value is not None:
                cur.execute(
                    "INSERT INTO config (key, value) VALUES (%s, %s)",
                    (str(key), str(value)),
                )


def _export_runtime_data():
    """Return all runtime data from the currently configured backend."""
    return {
        "articles": _load_articles(),
        "accounts": _load_accounts(),
        "config": _load_config(),
    }


def _import_runtime_data_to_postgres(database_url, payload):
    """Replace PostgreSQL runtime tables with *payload*."""
    global DATABASE_URL
    previous = DATABASE_URL
    DATABASE_URL = database_url
    try:
        _init_pg_db()
        with _pg_connect() as conn:
            _pg_replace_articles(conn, payload.get("articles") or [])
            _pg_replace_accounts(conn, payload.get("accounts") or [])
            _pg_replace_config(conn, payload.get("config") or {})
    finally:
        DATABASE_URL = previous


def _pg_count_articles(database_url):
    """Return the article count in the target PostgreSQL, or 0 if the table is
    missing / unreachable. Used by --migrate-runtime-to-postgres to refuse
    overwriting a populated runtime DB without --force-replace.

    Note: only PG-side errors (table missing, connection refused) are swallowed
    as "target is empty". psycopg2 import failure (RuntimeError from
    _pg_connect) is re-raised so the caller sees a clear environment problem
    instead of silently bypassing the --force-replace guard.
    """
    global DATABASE_URL
    previous = DATABASE_URL
    DATABASE_URL = database_url
    try:
        try:
            with _pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS n FROM articles")
                    row = cur.fetchone()
                    if row is None:
                        return 0
                    # RealDictCursor returns dict-like rows
                    return int(row.get("n") if hasattr(row, "get") else row[0])
        except RuntimeError:
            # _pg_connect raises RuntimeError when psycopg2 isn't installed.
            # That's an environment / setup problem, not "target is empty" —
            # surface it instead of silently bypassing the --force-replace guard.
            raise
        except Exception:
            # PG-side errors (table doesn't exist, can't connect) — treat as
            # empty so a fresh migration into a brand-new DB still works.
            return 0
    finally:
        DATABASE_URL = previous


def _upload_to_r2(data_bytes, r2_key):
    """Upload raw bytes to R2 at the given object key.

    Returns the public CDN URL on success, or None on failure.
    Uses rclone subprocess so zero new Python dependencies are required.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    try:
        tmp.write(data_bytes)
        tmp.close()
        result = subprocess.run(
            [RCLONE_BIN, "copyto", tmp.name, f"{R2_REMOTE}/{r2_key}"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            sys.stderr.write(f"[r2-upload] rclone failed: {result.stderr.strip()}\n")
            return None
        return f"{CDN_DOMAIN}/{r2_key}"
    except (OSError, subprocess.TimeoutExpired) as e:
        sys.stderr.write(f"[r2-upload] exception: {e}\n")
        return None
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _classify_upload_name(filename, article_id):
    """Map an uploaded filename to a clean key under works/{article_id}/.

    Mirrors migrate_to_r2.py logic so admin uploads share the same naming
    convention as the initial bulk migration.
    """
    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    out_ext = ".webp" if ext in {".jpg", ".jpeg", ".png"} else ext

    m = re.search(r"-(hero|detail-\d+|scene-\d+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"
    if base.startswith(f"{article_id}_"):
        rest = re.sub(r"_+", "_", base[len(article_id) + 1:].strip("_"))
        return f"{rest}{out_ext}"
    m = re.match(r"^[0-9a-f]{8}_(.+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"
    safe = re.sub(r"[^\w\-]", "_", base)
    return f"{safe}{out_ext}"


def _load_config():
    """Return the legacy admin config dict, or an empty dict on failure."""
    if _using_postgres():
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT key, value FROM config")
                rows = cur.fetchall()
        return {r["key"]: r["value"] for r in rows}

    with _db_connect() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
    return {r["key"]: r["value"] for r in rows}


def _load_articles():
    """Return the articles list from the configured database, or an empty list."""
    if _using_postgres():
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM articles ORDER BY row_index, id")
                rows = cur.fetchall()
            return [_pg_article_from_row(conn, row) for row in rows]

    with _db_connect() as conn:
        rows = conn.execute("SELECT * FROM articles ORDER BY row_index, id").fetchall()
        return [_article_from_row(conn, row) for row in rows]


def _save_articles(articles):
    """Persist the articles list to the configured database atomically."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if _using_postgres():
        with _pg_connect() as conn:
            _pg_replace_articles(conn, articles)
        return

    with _db_connect() as conn:
        _replace_articles(conn, articles)


def _load_accounts():
    """Return the accounts list from the configured database, or [] if missing."""
    if _using_postgres():
        with _pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM accounts ORDER BY username")
                rows = cur.fetchall()
            return [_pg_account_from_row(conn, row) for row in rows]

    with _db_connect() as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY username").fetchall()
        return [_account_from_row(conn, row) for row in rows]


def _save_accounts(accounts):
    """Persist the accounts list to the configured database atomically."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if _using_postgres():
        with _pg_connect() as conn:
            _pg_replace_accounts(conn, accounts)
        return

    with _db_connect() as conn:
        _replace_accounts(conn, accounts)


def _hash_password(salt, password):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _generate_salt():
    return secrets.token_hex(16)


def _public_account(account):
    """Return account dict with sensitive fields stripped."""
    return {k: account.get(k) for k in ACCOUNT_PUBLIC_FIELDS if k in account}


def _find_account(accounts, username):
    for a in accounts:
        if a.get("username") == username:
            return a
    return None


def _count_active_admins(accounts, exclude_username=None):
    """Count enabled accounts with accounts.manage permission."""
    count = 0
    for a in accounts:
        if exclude_username and a.get("username") == exclude_username:
            continue
        if a.get("enabled") and "accounts.manage" in (a.get("permissions") or []):
            count += 1
    return count


def _json_bytes(obj, status_hint=200):
    """Serialise *obj* to UTF-8 JSON bytes."""
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def _parse_multipart(body, content_type):
    """
    Minimal multipart/form-data parser.

    Returns a list of dicts:
        [{"name": ..., "filename": ..., "content_type": ..., "data": bytes}, ...]

    Only handles the subset we need (file uploads).
    """
    # Extract boundary from Content-Type header
    m = re.search(r"boundary=([^\s;]+)", content_type)
    if not m:
        return []
    boundary = m.group(1).encode("utf-8")
    # RFC 2046: the actual delimiter is "--" + boundary
    delimiter = b"--" + boundary
    parts = body.split(delimiter)
    results = []
    for part in parts:
        # Skip preamble / epilogue
        if part in (b"", b"--", b"--\r\n", b"\r\n"):
            continue
        if part.startswith(b"--"):
            continue
        # Split headers from body (separated by \r\n\r\n)
        sep = part.find(b"\r\n\r\n")
        if sep == -1:
            continue
        header_block = part[:sep].decode("utf-8", errors="replace")
        file_data = part[sep + 4:]
        # Trim trailing \r\n left before next boundary
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]

        info = {"data": file_data}
        # Parse Content-Disposition
        for line in header_block.splitlines():
            line = line.strip()
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.startswith("name="):
                        info["name"] = token.split("=", 1)[1].strip('" ')
                    elif token.startswith("filename="):
                        info["filename"] = token.split("=", 1)[1].strip('" ')
            elif line.lower().startswith("content-type:"):
                info["content_type"] = line.split(":", 1)[1].strip()
        results.append(info)
    return results


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class MurayamaHandler(SimpleHTTPRequestHandler):
    """Extends SimpleHTTPRequestHandler with JSON API routes."""

    # Override server_version for log output
    server_version = "MurayamaServer/1.0"

    # ------------------------------------------------------------------
    # Routing helpers
    # ------------------------------------------------------------------

    def _is_api(self):
        return self.path.startswith("/api/")

    def _is_admin_page(self):
        """Check if requesting /admin or /admin/ — used for path rewrite to /admin/index.html.

        Do NOT extend this to subpaths; doing so would rewrite /admin/app.js → /admin/index.html
        and break the admin SPA. For noindex header logic, use _is_admin_path() instead.
        """
        stripped = self.path.split("?")[0].split("#")[0]
        return stripped in ("/admin", "/admin/")

    def _is_admin_path(self):
        """Check if request targets /admin or any subpath under /admin/ — used for X-Robots-Tag noindex.

        Covers /admin, /admin/, /admin/index.html, /admin/app.js, /admin/anything.
        Decoded via unquote to defeat URL-escape evasion (e.g., %2fadmin%2f).
        """
        stripped = unquote(self.path.split("?")[0].split("#")[0])
        return stripped == "/admin" or stripped.startswith("/admin/")

    def _is_quote_path(self):
        """Proposal pages are private client-facing previews, not search results."""
        stripped = unquote(self.path.split("?")[0].split("#")[0])
        return stripped == "/quote" or stripped.startswith("/quote/")

    def _is_robots_path(self):
        stripped = unquote(self.path.split("?")[0].split("#")[0])
        return stripped == "/robots.txt"

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def end_headers(self):
        if self._is_quote_path():
            self.send_header(
                "X-Robots-Tag",
                "noindex, nofollow, noarchive, nosnippet, noimageindex",
            )
            self.send_header("Cache-Control", "private, no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif self._is_admin_path():
            self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
            self.send_header("Cache-Control", "private, no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif self._is_robots_path():
            self.send_header("Cache-Control", "private, no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, data, status=200):
        body = _json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _check_auth(self):
        """
        Validate HTTP Basic Auth against data/accounts.json (preferred) or
        data/config.json (legacy single-user fallback).

        On success, stores the matched account dict on `self._auth_account`
        and returns True. On failure, sends 401 and returns False.
        """
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            self._send_401()
            return False

        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            user, password = decoded.split(":", 1)
        except Exception:
            self._send_401()
            return False

        accounts = _load_accounts()
        if accounts:
            account = _find_account(accounts, user)
            if (account
                    and account.get("enabled")
                    and _hash_password(account.get("salt", ""), password)
                        == account.get("passwordHash", "")):
                self._auth_account = account
                return True
            self._send_401()
            return False

        # Legacy fallback: single-user config.json
        cfg = _load_config()
        expected_user = cfg.get("adminUser", "")
        expected_hash = cfg.get("adminPasswordHash", "")
        salt = cfg.get("adminSalt", "")
        if (user == expected_user and expected_hash
                and _hash_password(salt, password) == expected_hash):
            self._auth_account = {
                "username": expected_user,
                "name": expected_user,
                "role": "admin",
                "enabled": True,
                "permissions": sorted(VALID_PERMISSIONS),
            }
            return True
        self._send_401()
        return False

    def _require_permission(self, permission):
        """Check the authenticated account has *permission*; send 403 if not."""
        account = getattr(self, "_auth_account", None)
        if account and permission in (account.get("permissions") or []):
            return True
        self._send_error_json(403, "Forbidden: missing permission " + permission)
        return False

    def _send_401(self):
        body = _json_bytes({"error": "Unauthorized"})
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    # ------------------------------------------------------------------
    # Body reading
    # ------------------------------------------------------------------

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _read_json_body(self):
        raw = self._read_body()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # ------------------------------------------------------------------
    # API: articles
    # ------------------------------------------------------------------

    def _api_get_articles(self):
        """GET /api/articles — return all articles with computed heroImage."""
        articles = _load_articles()
        for art in articles:
            # Compute heroImage path if images list exists
            images = art.get("images", [])
            if images and not art.get("heroImage"):
                art["heroImage"] = images[0]
        self._send_json({"articles": articles})

    def _api_get_images(self, article_id):
        """GET /api/images/{id} — return image list for an article."""
        articles = _load_articles()
        article = None
        for a in articles:
            if str(a.get("id")) == article_id:
                article = a
                break
        if article is None:
            self._send_error_json(404, "Article not found")
            return
        images = article.get("images", [])
        self._send_json({"id": article_id, "images": images})

    def _api_create_article(self):
        """POST /api/articles — create a new article (auth required)."""
        if not self._check_auth():
            return
        if not self._require_permission("articles.write"):
            return
        data = self._read_json_body()
        if not data or not isinstance(data, dict):
            self._send_error_json(400, "Invalid JSON body")
            return

        articles = _load_articles()
        # Assign a unique id
        new_id = data.get("id") or str(uuid.uuid4())[:8]
        # Ensure unique
        existing_ids = {str(a.get("id")) for a in articles}
        if new_id in existing_ids:
            self._send_error_json(409, f"Article id '{new_id}' already exists")
            return

        data["id"] = new_id
        data.setdefault("images", [])
        data.setdefault("createdAt", time.strftime("%Y-%m-%dT%H:%M:%S"))
        data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles.append(data)
        _save_articles(articles)
        self._send_json(data, status=201)

    def _api_update_article(self, article_id):
        """PUT /api/articles/{id} — update an existing article (auth required)."""
        if not self._check_auth():
            return
        if not self._require_permission("articles.write"):
            return
        data = self._read_json_body()
        if not data or not isinstance(data, dict):
            self._send_error_json(400, "Invalid JSON body")
            return

        articles = _load_articles()
        idx = None
        for i, a in enumerate(articles):
            if str(a.get("id")) == article_id:
                idx = i
                break
        if idx is None:
            self._send_error_json(404, "Article not found")
            return

        # Merge fields (preserve id)
        article = articles[idx]
        for key, val in data.items():
            if key == "id":
                continue  # never overwrite id
            article[key] = val
        article["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles[idx] = article
        _save_articles(articles)
        self._send_json(article)

    def _api_delete_article(self, article_id):
        """DELETE /api/articles/{id} — remove an article (auth required)."""
        if not self._check_auth():
            return
        if not self._require_permission("articles.delete"):
            return

        articles = _load_articles()
        new_articles = [a for a in articles if str(a.get("id")) != article_id]
        if len(new_articles) == len(articles):
            self._send_error_json(404, "Article not found")
            return
        _save_articles(new_articles)
        self._send_json({"deleted": article_id})

    def _api_upload(self, article_id):
        """POST /api/upload/{id} — upload image for an article (auth required)."""
        if not self._check_auth():
            return
        if not self._require_permission("uploads.write"):
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_error_json(400, "Expected multipart/form-data")
            return

        body = self._read_body()
        parts = _parse_multipart(body, content_type)
        if not parts:
            self._send_error_json(400, "No files found in upload")
            return

        # Find the article
        articles = _load_articles()
        article = None
        art_idx = None
        for i, a in enumerate(articles):
            if str(a.get("id")) == article_id:
                article = a
                art_idx = i
                break
        if article is None:
            self._send_error_json(404, "Article not found")
            return

        # Compute next sequential index for this article's uploads.
        # Scheme: {article_id}-{N}.webp — keeps all filenames ASCII and clearly
        # tied to the owning article. Scans existing images (any `-\d+.webp` tail)
        # so newly-uploaded files don't collide with legacy detail-N/scene-N.
        seq_re = re.compile(r"-(\d+)\.webp(?:[?#].*)?$", re.IGNORECASE)
        next_idx = 0
        for url in (article.get("images") or []):
            m = seq_re.search(url or "")
            if m:
                try:
                    n = int(m.group(1))
                    if n > next_idx:
                        next_idx = n
                except ValueError:
                    pass

        saved_paths = []
        failed = []
        for part in parts:
            filename = part.get("filename")
            if not filename:
                continue
            img_data = part["data"]
            thumb_data = None

            # Convert to WebP when Pillow is available (quality matches migration).
            if _PILLOW_AVAILABLE:
                try:
                    img = _PILImage.open(io.BytesIO(img_data))
                    img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
                    # Pre-resize oversized photos so encoding doesn't stall for 30+s.
                    if img.width > MAX_UPLOAD_WIDTH:
                        img.thumbnail((MAX_UPLOAD_WIDTH, MAX_UPLOAD_WIDTH * 10),
                                      _PILImage.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
                    img_data = buf.getvalue()
                    # Generate small thumbnail for admin gallery preview.
                    try:
                        thumb_img = img.copy()
                        thumb_img.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 10), _PILImage.LANCZOS)
                        thumb_buf = io.BytesIO()
                        thumb_img.save(thumb_buf, format="WEBP", quality=THUMB_QUALITY, method=4)
                        thumb_data = thumb_buf.getvalue()
                    except Exception as e:
                        sys.stderr.write(f"[upload] thumb generation failed for {filename}: {e}\n")
                except Exception as e:
                    sys.stderr.write(f"[upload] WebP conversion failed for {filename}: {e}\n")

            # Auto-name as {article_id}-{N}.webp — drops any non-ASCII / raw
            # client filename. R2 key + public URL stay clean ASCII.
            next_idx += 1
            target_name = f"{article_id}-{next_idx}.webp"
            r2_key = f"works/{article_id}/{target_name}"
            cdn_url = _upload_to_r2(img_data, r2_key)
            if cdn_url is None:
                failed.append(filename)
                continue
            saved_paths.append(cdn_url)

            # Upload thumbnail alongside (best-effort; skip log on failure).
            if thumb_data:
                thumb_key = f"works/{article_id}/{target_name[:-5]}-thumb.webp"
                _upload_to_r2(thumb_data, thumb_key)

        if failed and not saved_paths:
            self._send_error_json(500, f"All uploads failed: {failed}")
            return

        # Update article images list
        if "images" not in article:
            article["images"] = []
        article["images"].extend(saved_paths)
        article["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles[art_idx] = article
        _save_articles(articles)

        resp = {"uploaded": saved_paths}
        if failed:
            resp["failed"] = failed
        self._send_json(resp, status=201)

    # ------------------------------------------------------------------
    # API: session
    # ------------------------------------------------------------------

    def _api_get_session(self):
        """GET /api/session — return current authenticated account profile."""
        if not self._check_auth():
            return
        self._send_json({"account": _public_account(self._auth_account)})

    # ------------------------------------------------------------------
    # API: accounts
    # ------------------------------------------------------------------

    def _validate_account_payload(self, data, *, require_username, require_password):
        """Validate fields shared by create / update.  Returns (ok, error_msg)."""
        if not isinstance(data, dict):
            return False, "Invalid JSON body"

        if require_username:
            username = (data.get("username") or "").strip()
            if not username or not re.match(r"^[A-Za-z0-9_.\-]{2,32}$", username):
                return False, "Invalid username (2-32 chars, A-Z a-z 0-9 _ . -)"

        if require_password or data.get("password"):
            password = data.get("password") or ""
            if len(password) < 6:
                return False, "Password must be at least 6 characters"

        if "role" in data and data["role"] not in VALID_ROLES:
            return False, "Invalid role"

        if "permissions" in data:
            perms = data["permissions"]
            if not isinstance(perms, list):
                return False, "permissions must be a list"
            for p in perms:
                if p not in VALID_PERMISSIONS:
                    return False, f"Invalid permission: {p}"
        return True, None

    def _api_list_accounts(self):
        """GET /api/accounts — list all accounts (auth + accounts.manage)."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return
        accounts = _load_accounts()
        self._send_json({"accounts": [_public_account(a) for a in accounts]})

    def _api_create_account(self):
        """POST /api/accounts — create a new account (auth + accounts.manage)."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        data = self._read_json_body()
        ok, err = self._validate_account_payload(
            data, require_username=True, require_password=True
        )
        if not ok:
            self._send_error_json(400, err)
            return

        username = data["username"].strip()
        accounts = _load_accounts()
        if _find_account(accounts, username):
            self._send_error_json(409, f"Account '{username}' already exists")
            return

        salt = _generate_salt()
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        new_account = {
            "username": username,
            "name": (data.get("name") or username).strip(),
            "role": data.get("role") or "custom",
            "enabled": bool(data.get("enabled", True)),
            "permissions": list(data.get("permissions") or []),
            "salt": salt,
            "passwordHash": _hash_password(salt, data["password"]),
            "createdAt": now,
            "updatedAt": now,
        }
        accounts.append(new_account)
        _save_accounts(accounts)
        self._send_json({"account": _public_account(new_account)}, status=201)

    def _api_update_account(self, username):
        """PUT /api/accounts/{username} — update an existing account."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        data = self._read_json_body()
        ok, err = self._validate_account_payload(
            data, require_username=False, require_password=False
        )
        if not ok:
            self._send_error_json(400, err)
            return

        accounts = _load_accounts()
        account = _find_account(accounts, username)
        if account is None:
            self._send_error_json(404, "Account not found")
            return

        # Compute the post-update state to enforce last-admin invariant.
        new_enabled = bool(data["enabled"]) if "enabled" in data else account.get("enabled", True)
        new_perms = list(data["permissions"]) if "permissions" in data else (account.get("permissions") or [])
        was_active_admin = account.get("enabled") and "accounts.manage" in (account.get("permissions") or [])
        will_be_active_admin = new_enabled and "accounts.manage" in new_perms
        if was_active_admin and not will_be_active_admin:
            if _count_active_admins(accounts, exclude_username=username) == 0:
                self._send_error_json(400, "Cannot demote the last active admin")
                return

        if "name" in data:
            account["name"] = (data["name"] or username).strip()
        if "role" in data:
            account["role"] = data["role"]
        if "enabled" in data:
            account["enabled"] = new_enabled
        if "permissions" in data:
            account["permissions"] = new_perms
        if data.get("password"):
            account["salt"] = _generate_salt()
            account["passwordHash"] = _hash_password(account["salt"], data["password"])
        account["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        _save_accounts(accounts)
        self._send_json({"account": _public_account(account)})

    def _api_delete_account(self, username):
        """DELETE /api/accounts/{username} — remove an account."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        if self._auth_account.get("username") == username:
            self._send_error_json(400, "Cannot delete your own account")
            return

        accounts = _load_accounts()
        target = _find_account(accounts, username)
        if target is None:
            self._send_error_json(404, "Account not found")
            return

        was_active_admin = target.get("enabled") and "accounts.manage" in (target.get("permissions") or [])
        if was_active_admin and _count_active_admins(accounts, exclude_username=username) == 0:
            self._send_error_json(400, "Cannot delete the last active admin")
            return

        accounts = [a for a in accounts if a.get("username") != username]
        _save_accounts(accounts)
        self._send_json({"deleted": username})

    # ------------------------------------------------------------------
    # Route dispatcher
    # ------------------------------------------------------------------

    def _route_api(self, method):
        """Dispatch an API request.  Returns True if handled."""
        path = self.path.split("?")[0].rstrip("/")
        path = unquote(path)

        # GET /api/articles
        if method == "GET" and path == "/api/articles":
            self._api_get_articles()
            return True

        # GET /api/images/{id}
        if method == "GET" and path.startswith("/api/images/"):
            article_id = path[len("/api/images/"):]
            if article_id:
                self._api_get_images(article_id)
                return True

        # POST /api/articles
        if method == "POST" and path == "/api/articles":
            self._api_create_article()
            return True

        # PUT /api/articles/{id}
        if method == "PUT" and path.startswith("/api/articles/"):
            article_id = path[len("/api/articles/"):]
            if article_id:
                self._api_update_article(article_id)
                return True

        # DELETE /api/articles/{id}
        if method == "DELETE" and path.startswith("/api/articles/"):
            article_id = path[len("/api/articles/"):]
            if article_id:
                self._api_delete_article(article_id)
                return True

        # POST /api/upload/{id}
        if method == "POST" and path.startswith("/api/upload/"):
            article_id = path[len("/api/upload/"):]
            if article_id:
                self._api_upload(article_id)
                return True

        # GET /api/session
        if method == "GET" and path == "/api/session":
            self._api_get_session()
            return True

        # GET /api/accounts
        if method == "GET" and path == "/api/accounts":
            self._api_list_accounts()
            return True

        # POST /api/accounts
        if method == "POST" and path == "/api/accounts":
            self._api_create_account()
            return True

        # PUT /api/accounts/{username}
        if method == "PUT" and path.startswith("/api/accounts/"):
            username = path[len("/api/accounts/"):]
            if username:
                self._api_update_account(username)
                return True

        # DELETE /api/accounts/{username}
        if method == "DELETE" and path.startswith("/api/accounts/"):
            username = path[len("/api/accounts/"):]
            if username:
                self._api_delete_account(username)
                return True

        return False

    # ------------------------------------------------------------------
    # HTTP method overrides
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self._is_api():
            if not self._route_api("GET"):
                self._send_error_json(404, "Not found")
            return
        # Serve /admin and /admin/ as admin/index.html
        if self._is_admin_page():
            self.path = "/admin/index.html"
        clean_path = self.path.split("?")[0].split("#")[0]
        # Serve /sitemap.xml dynamically
        if clean_path == "/sitemap.xml":
            self._serve_sitemap()
            return
        # Keep the legacy public JSON URL backed by SQLite instead of a file.
        if clean_path == "/data/articles.json":
            self._send_json({"articles": _load_articles()})
            return
        # Serve /works/{id} as dynamic SEO page
        if clean_path.startswith("/works/"):
            article_id = clean_path[len("/works/"):].strip("/")
            if article_id:
                self._serve_works_page(article_id)
                return
        # Fall through to static file serving
        super().do_GET()

    def _serve_works_page(self, article_id, head_only=False):
        """Dynamically generate an SEO-friendly HTML page for a work."""
        articles = _load_articles()
        article = next((a for a in articles if a.get("id") == article_id), None)
        if not article:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if not head_only:
                self.wfile.write(b"<h1>404 Not Found</h1>")
            return

        site_url = "https://goodjob.weddingwishlove.com"
        page_url = f"{site_url}/works/{article_id}"
        title = article.get("title", "")
        description = article.get("description", "")
        # Keep crawler/share summaries compact even when the CMS copy has paragraphs.
        meta_source = re.sub(r"\s+", " ", description).strip()
        meta_desc = meta_source[:157] + "..." if len(meta_source) > 160 else meta_source
        # Hero image
        hero = article.get("heroImage") or ""
        if hero and not hero.startswith("http"):
            og_image = site_url + hero
        else:
            og_image = hero or f"{site_url}/assets/images/og-default.jpg"

        cat_labels = {
            "business": "主題活動", "party": "春酒尾牙",
            "magic": "魔法學院", "civil": "戶政改造"
        }
        cat_label = cat_labels.get(article.get("category", ""), "作品")
        images = article.get("images") or ([hero] if hero else [])

        # Gallery HTML — alt = 標題 + 分類 + 關鍵字，幫助 Google Image Search
        img_alt_suffix = f"{cat_label}活動佈置 村山良作"
        gallery_html = ""
        for i, img in enumerate(images[:20], 1):
            escaped = img.replace('"', '&quot;')
            alt = f"{title} {img_alt_suffix} {i}"
            gallery_html += f'<img src="{escaped}" alt="{alt}" loading="lazy">\n'

        # JSON-LD structured data
        jsonld = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "name": title,
            "description": meta_desc,
            "image": og_image,
            "url": page_url,
            "author": {
                "@type": "Organization",
                "name": "村山良作 Murayama Goodjob",
                "url": site_url
            },
            "genre": cat_label
        }
        import json as _json
        jsonld_str = _json.dumps(jsonld, ensure_ascii=False)

        css_v = "20260406b"
        html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}｜村山良作 Murayama Goodjob</title>
  <meta name="description" content="{meta_desc}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}｜村山良作">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:site_name" content="村山良作 Murayama Goodjob">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}｜村山良作">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image" content="{og_image}">
  <link rel="canonical" href="{page_url}">
  <link rel="stylesheet" href="/assets/site.css?v={css_v}">
  <script type="application/ld+json">{jsonld_str}</script>
  <style>
    .works-page {{ max-width: 960px; margin: 0 auto; padding: 100px 24px 60px; }}
    .works-hero {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; border-radius: 8px; display: block; }}
    .works-meta {{ margin: 24px 0 8px; display: flex; align-items: center; gap: 12px; }}
    .works-title {{ font-size: clamp(1.8rem, 3vw, 2.8rem); margin: 0 0 20px; line-height: 1.2; }}
    .works-desc {{ font-size: 1rem; line-height: 1.9; color: rgba(255,255,255,.74); white-space: pre-wrap; margin: 0 0 40px; }}
    .works-gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 32px; }}
    .works-gallery img {{ width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: 6px; display: block; }}
    .works-back {{ display: inline-flex; align-items: center; gap: 8px; color: rgba(255,255,255,.6); text-decoration: none; font-size: .9rem; margin-bottom: 32px; }}
    .works-back:hover {{ color: #fff; }}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="site-nav">
      <a href="/" class="site-logo">
        <img src="/assets/images/logo.png" alt="村山良作" width="40" height="40">
        <span class="site-name">村山良作</span>
      </a>
      <div class="site-nav-links">
        <a href="/sort-hat/">分類帽</a>
        <a href="/teabar.html">囍茶方案</a>
        <a href="/workflow.html">合作流程</a>
      </div>
    </nav>
  </header>

  <main class="works-page">
    <a href="/#shelf" class="works-back">← 所有作品</a>
    <img class="works-hero" src="{hero}" alt="{title} {cat_label}活動佈置 村山良作">
    <div class="works-meta">
      <span class="detail-tag">{cat_label}</span>
    </div>
    <h1 class="works-title">{title}</h1>
    <p class="works-desc">{description}</p>
    <section>
      <h2 style="font-size:1.4rem;margin:0 0 16px;">精彩花絮</h2>
      <div class="works-gallery">
        {gallery_html}
      </div>
    </section>
  </main>
</body>
</html>"""

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _serve_sitemap(self, head_only=False):
        """Dynamically generate sitemap.xml with all works pages."""
        import xml.etree.ElementTree as ET
        articles = _load_articles()
        site_url = "https://goodjob.weddingwishlove.com"

        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        # Static pages
        for loc in ["", "/teabar.html", "/workflow.html", "/wedding-packages/", "/wedding-packages/outdoor.html"]:
            lines.append(f"  <url><loc>{site_url}{loc}</loc></url>")
        # Dynamic works pages
        for a in articles:
            aid = a.get("id", "")
            if aid:
                lines.append(f"  <url><loc>{site_url}/works/{aid}</loc></url>")
        lines.append("</urlset>")

        body = "\n".join(lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def do_HEAD(self):
        if self._is_api():
            if not self._route_api("GET"):
                self._send_error_json(404, "Not found")
            return
        if self._is_admin_page():
            self.path = "/admin/index.html"
        clean_path = self.path.split("?")[0].split("#")[0]
        if clean_path == "/data/articles.json":
            body = _json_bytes({"articles": _load_articles()})
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        if clean_path == "/sitemap.xml":
            self._serve_sitemap(head_only=True)
            return
        if clean_path.startswith("/works/"):
            article_id = clean_path[len("/works/"):].strip("/")
            if article_id:
                self._serve_works_page(article_id, head_only=True)
                return
        super().do_HEAD()

    def do_POST(self):
        if self._is_api():
            if not self._route_api("POST"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    def do_PUT(self):
        if self._is_api():
            if not self._route_api("PUT"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    def do_DELETE(self):
        if self._is_api():
            if not self._route_api("DELETE"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_message(self, format, *args):
        """Log to stdout with timestamp."""
        sys.stdout.write("[%s] %s - %s\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            self.address_string(),
            format % args,
        ))
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Murayama Good Job Site Server")
    parser.add_argument("--port", type=int, default=10814, help="Port to listen on (default: 10814)")
    parser.add_argument("--bind", default="127.0.0.1", help="Address to bind to (default: 127.0.0.1)")
    parser.add_argument(
        "--migrate-runtime-to-postgres",
        metavar="DATABASE_URL",
        help="one-time migration: copy the current runtime backend into PostgreSQL and exit",
    )
    parser.add_argument(
        "--force-replace",
        action="store_true",
        help="(with --migrate-runtime-to-postgres) overwrite target PostgreSQL even if it already has articles. dangerous — make a pg_dump first.",
    )
    args = parser.parse_args()

    # Ensure we serve files from the script's directory
    os.chdir(BASE_DIR)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    if args.migrate_runtime_to_postgres:
        # migrate 是顯式請求，允許從 SQLite / JSON 為來源
        os.environ["GOODJOB_ALLOW_SQLITE"] = "1"
        os.environ["GOODJOB_ALLOW_JSON_SEED"] = "1"

        # 修補 D：防呆 — 偵測目標 PostgreSQL 是否已經有資料，避免誤覆蓋線上
        target_url = args.migrate_runtime_to_postgres
        existing_count = _pg_count_articles(target_url)
        if existing_count > 0 and not args.force_replace:
            sys.stderr.write(
                f"[fatal] target PostgreSQL already has {existing_count} article(s).\n"
                "  refusing to wipe runtime data without --force-replace.\n"
                "  if you really mean to overwrite, take a pg_dump first, then re-run\n"
                "  with both --migrate-runtime-to-postgres AND --force-replace.\n"
            )
            sys.exit(1)

        _init_db()
        payload = _export_runtime_data()
        _import_runtime_data_to_postgres(target_url, payload)
        print(
            "[migrate] copied runtime data to PostgreSQL: "
            f"{len(payload['articles'])} article(s), "
            f"{len(payload['accounts'])} account(s), "
            f"{len(payload['config'])} config value(s)"
        )
        return

    # 修補 B：runtime 預設必須走 PostgreSQL — 避免 systemd override 失效時
    # 偷偷 fallback 到 SQLite 並從舊 JSON seed 把線上資料覆蓋掉。
    # 本機 dev / 故意走 SQLite，需顯式 GOODJOB_ALLOW_SQLITE=1。
    if not _using_postgres() and os.environ.get("GOODJOB_ALLOW_SQLITE", "").strip() != "1":
        sys.stderr.write(
            "[fatal] GOODJOB_DATABASE_URL is not set.\n"
            "  Production runtime requires PostgreSQL — refusing to start on SQLite\n"
            "  fallback because past incidents wiped article data.\n"
            "  If this is an intentional dev run on SQLite, set GOODJOB_ALLOW_SQLITE=1.\n"
            "  On the live host, check /etc/systemd/system/murayama-goodjob.service.d/postgres.conf\n"
            "  and run: sudo systemctl daemon-reload && sudo systemctl restart murayama-goodjob.service\n"
        )
        sys.exit(1)

    _init_db()

    # Validate auth source: prefer accounts table, fall back to legacy config table
    accounts = _load_accounts()
    cfg = _load_config()
    if accounts:
        active_admins = _count_active_admins(accounts)
        print(f"[auth] {len(accounts)} account(s) loaded ({active_admins} active admin(s))")
        if active_admins == 0:
            print("[warn] no active admin account — accounts.manage operations will be locked")
    elif cfg.get("adminUser"):
        print(f"[auth] legacy single-user mode (adminUser='{cfg.get('adminUser')}')")
    else:
        print("[warn] no accounts.json and no adminUser in config.json — admin auth will reject all requests")

    server = HTTPServer((args.bind, args.port), MurayamaHandler)
    print(f"Murayama server running on http://{args.bind}:{args.port}/")
    print(f"  Static root : {BASE_DIR}")
    print(f"  Data dir    : {DATA_DIR}")
    print(f"  DB backend  : {'PostgreSQL' if _using_postgres() else 'SQLite'}")
    if not _using_postgres():
        print(f"  SQLite DB   : {DB_PATH}")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
