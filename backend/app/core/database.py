"""数据库初始化与连接管理"""

import sqlite3
import os
from contextlib import contextmanager
from app.core.config import settings


def get_db_path() -> str:
    data_dir = os.path.dirname(settings.db_path)
    os.makedirs(data_dir, exist_ok=True)
    return settings.db_path


@contextmanager
def get_db():
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _ensure_indexes(db):
    """确保常用查询列有索引（幂等）"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_snapshots_user_date ON net_worth_snapshots(user_id, snap_date)",
        "CREATE INDEX IF NOT EXISTS idx_assets_cash_user ON asset_cash(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_deposit_user ON asset_deposit(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_fund_user ON asset_fund(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_stock_user ON asset_stock(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_bond_user ON asset_bond(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_precious_user ON asset_precious_metal(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_liabilities_user ON liabilities(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_family ON users(family_id)",
        "CREATE INDEX IF NOT EXISTS idx_settings_user_key ON user_settings(user_id, setting_key)",
    ]
    for sql in indexes:
        db.execute(sql)


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS families (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL DEFAULT '我的家庭',
            invite_code TEXT    NOT NULL UNIQUE,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password_hash TEXT  NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user')),
            display_name TEXT   DEFAULT '',
            family_id   INTEGER REFERENCES families(id),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_cash (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            name        TEXT    NOT NULL,
            currency    TEXT    NOT NULL DEFAULT 'CNY',
            amount      REAL    NOT NULL DEFAULT 0,
            account_name TEXT   DEFAULT '',
            note        TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_deposit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            name        TEXT    NOT NULL,
            bank        TEXT    DEFAULT '',
            principal   REAL    NOT NULL DEFAULT 0,
            rate        REAL    NOT NULL DEFAULT 0,
            start_date  TEXT    NOT NULL,
            end_date    TEXT    NOT NULL,
            currency    TEXT    NOT NULL DEFAULT 'CNY',
            note        TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_fund (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            code        TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            shares      REAL    NOT NULL DEFAULT 0,
            cost_nav    REAL    NOT NULL DEFAULT 0,
            current_nav REAL    DEFAULT 0,
            fund_type   TEXT    DEFAULT '',
            note        TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_stock (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            code        TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            shares      REAL    NOT NULL DEFAULT 0,
            cost_price  REAL    NOT NULL DEFAULT 0,
            current_price REAL  DEFAULT 0,
            market      TEXT    NOT NULL DEFAULT 'sh' CHECK(market IN ('sh','sz','hk','us')),
            note        TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_bond (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            name        TEXT    NOT NULL,
            issuer      TEXT    DEFAULT '',
            face_value  REAL    NOT NULL DEFAULT 0,
            rate        REAL    NOT NULL DEFAULT 0,
            maturity_date TEXT  NOT NULL,
            currency    TEXT    NOT NULL DEFAULT 'CNY',
            quantity    REAL    NOT NULL DEFAULT 1,
            cost_price  REAL    NOT NULL DEFAULT 0,
            current_price REAL  NOT NULL DEFAULT 0,
            note        TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS liabilities (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            name            TEXT    NOT NULL,
            principal       REAL    NOT NULL DEFAULT 0,
            rate            REAL    NOT NULL DEFAULT 0,
            term_months     INTEGER NOT NULL DEFAULT 0,
            repay_type      TEXT    NOT NULL DEFAULT '等额本息' CHECK(repay_type IN ('等额本息', '等额本金')),
            start_date      TEXT    NOT NULL,
            monthly_payment REAL    DEFAULT 0,
            remaining       REAL    DEFAULT 0,
            note            TEXT    DEFAULT '',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS asset_precious_metal (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL REFERENCES users(id),
            name                  TEXT    NOT NULL,
            type                  TEXT    NOT NULL DEFAULT 'gold' CHECK(type IN ('gold','silver','platinum','palladium')),
            weight_grams          REAL    NOT NULL DEFAULT 0,
            buy_price_per_gram    REAL    NOT NULL DEFAULT 0,
            buy_date              TEXT    NOT NULL,
            buy_total             REAL    NOT NULL DEFAULT 0,
            current_price_per_gram REAL   DEFAULT 0,
            notes                 TEXT    DEFAULT '',
            is_hidden             INTEGER NOT NULL DEFAULT 0,
            created_at            TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at            TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            setting_key  TEXT    NOT NULL,
            setting_value TEXT   NOT NULL,
            UNIQUE(user_id, setting_key)
        );

        CREATE TABLE IF NOT EXISTS net_worth_snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            total_asset REAL    NOT NULL DEFAULT 0,
            total_debt  REAL    NOT NULL DEFAULT 0,
            net_worth   REAL    NOT NULL DEFAULT 0,
            snap_date   TEXT    NOT NULL DEFAULT (date('now', 'localtime')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            cash        REAL    NOT NULL DEFAULT 0,
            deposit     REAL    NOT NULL DEFAULT 0,
            fund        REAL    NOT NULL DEFAULT 0,
            stock       REAL    NOT NULL DEFAULT 0,
            bond        REAL    NOT NULL DEFAULT 0,
            precious_metal REAL NOT NULL DEFAULT 0,
            total_liability REAL NOT NULL DEFAULT 0
        );
        """)

        # -- migration: add category columns to existing snapshots (idempotent)
        for col in ["cash", "deposit", "fund", "stock", "bond", "precious_metal", "total_liability"]:
            try:
                db.execute(f"ALTER TABLE net_worth_snapshots ADD COLUMN {col} REAL NOT NULL DEFAULT 0")
            except Exception:
                pass  # column already exists

        # -- migration: add quantity/cost_price/current_price to asset_bond (idempotent)
        for col, default_val in [("quantity", "1"), ("cost_price", "0"), ("current_price", "0")]:
            try:
                db.execute(f"ALTER TABLE asset_bond ADD COLUMN {col} REAL NOT NULL DEFAULT {default_val}")
            except Exception:
                pass  # column already exists
        # backfill: set cost_price/current_price = face_value for existing rows
        try:
            db.execute("UPDATE asset_bond SET cost_price = face_value WHERE cost_price = 0 AND face_value > 0")
            db.execute("UPDATE asset_bond SET current_price = face_value WHERE current_price = 0 AND face_value > 0")
        except Exception:
            pass

        # -- ensure performance indexes exist (idempotent)
        _ensure_indexes(db)
