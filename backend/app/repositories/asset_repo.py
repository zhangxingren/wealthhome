"""通用资产数据访问层

提供统一的 CRUD 操作，避免各个 router 中重复的 SQL 查询。
"""

from typing import Optional, List, Dict, Any
from app.core.database import get_db

# ─── 表名白名单 ────────────────────────────────────────

ALLOWED_TABLES = {
    "asset_cash", "asset_deposit", "asset_fund", "asset_stock",
    "asset_bond", "asset_precious_metal",
    "liabilities", "net_worth_snapshots",
}


def _check_table(table: str):
    if table not in ALLOWED_TABLES:
        raise ValueError(f"不允许的表名: {table}")


# ─── CRUD 基础操作 ────────────────────────────────────

def create_asset(table: str, data: dict) -> int:
    """通用创建，返回新记录的 id"""
    _check_table(table)
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with get_db() as db:
        cur = db.execute(sql, tuple(data.values()))
        return cur.lastrowid


def get_by_id(table: str, asset_id: int, user_id: int = None) -> Optional[dict]:
    """按 id 查询单条记录，可选 user_id 校验"""
    _check_table(table)
    with get_db() as db:
        if user_id is not None:
            row = db.execute(
                f"SELECT * FROM {table} WHERE id=? AND user_id=?", (asset_id, user_id)
            ).fetchone()
        else:
            row = db.execute(
                f"SELECT * FROM {table} WHERE id=?", (asset_id,)
            ).fetchone()
    return dict(row) if row else None


def list_by_user(table: str, user_id: int, limit: int = 100, offset: int = 0) -> List[dict]:
    """按用户查询全部资产，支持分页"""
    _check_table(table)
    with get_db() as db:
        rows = db.execute(
            f"SELECT * FROM {table} WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def list_by_user_all(table: str, user_id: int) -> List[dict]:
    """按用户查询全部资产（不分页）"""
    _check_table(table)
    with get_db() as db:
        rows = db.execute(
            f"SELECT * FROM {table} WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_asset(table: str, asset_id: int, user_id: int, data: dict) -> bool:
    """更新资产，返回是否成功"""
    _check_table(table)
    if not data:
        return True
    sets = ", ".join(f"{k}=?" for k in data)
    values = list(data.values()) + [asset_id, user_id]
    sql = f"UPDATE {table} SET {sets} WHERE id=? AND user_id=?"
    with get_db() as db:
        cur = db.execute(sql, values)
        return cur.rowcount > 0


def delete_asset(table: str, asset_id: int, user_id: int) -> bool:
    """硬删除资产，返回是否成功"""
    _check_table(table)
    with get_db() as db:
        cur = db.execute(
            f"DELETE FROM {table} WHERE id=? AND user_id=?", (asset_id, user_id)
        )
        return cur.rowcount > 0


def exists(table: str, asset_id: int, user_id: int) -> bool:
    """检查资产是否存在"""
    _check_table(table)
    with get_db() as db:
        row = db.execute(
            f"SELECT 1 FROM {table} WHERE id=? AND user_id=?", (asset_id, user_id)
        ).fetchone()
    return row is not None


# ─── 汇总查询 ──────────────────────────────────────────

def sum_column(table: str, column: str, user_id: int) -> float:
    """汇总某用户某列的总和"""
    _check_table(table)
    with get_db() as db:
        row = db.execute(
            f"SELECT COALESCE(SUM({column}), 0) FROM {table} WHERE user_id=?", (user_id,)
        ).fetchone()
    return float(row[0]) if row else 0.0


def count_by_user(table: str, user_id: int) -> int:
    """统计某用户的记录数"""
    _check_table(table)
    with get_db() as db:
        row = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


# ─── 原始 SQL 查询（用于复杂汇总） ────────────────────

def raw_query(sql: str, params: tuple = ()) -> List[dict]:
    """执行原始查询，返回字典列表"""
    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def raw_query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    """执行原始查询，返回单条"""
    with get_db() as db:
        row = db.execute(sql, params).fetchone()
    return dict(row) if row else None


def raw_execute(sql: str, params: tuple = ()) -> int:
    """执行写操作，返回影响行数"""
    with get_db() as db:
        cur = db.execute(sql, params)
        return cur.rowcount


# ─── 净值快照专用 ──────────────────────────────────────

def insert_snapshot(user_id: int, snap_date: str, totals: dict) -> int:
    """插入净值快照"""
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO net_worth_snapshots "
            "(user_id,total_asset,total_debt,net_worth,snap_date,"
            "cash,deposit,fund,stock,bond,precious_metal,total_liability) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (user_id,
             totals["total_asset"], totals["total_liability"], totals["net_worth"], snap_date,
             totals["cash"], totals["deposit"], totals["fund"], totals["stock"],
             totals["bond"], totals["precious_metal"], totals["total_liability"]),
        )
        return cur.lastrowid


def snapshot_exists(user_id: int, snap_date: str) -> bool:
    """检查某用户某日是否已有快照"""
    with get_db() as db:
        row = db.execute(
            "SELECT id FROM net_worth_snapshots WHERE user_id=? AND snap_date=?",
            (user_id, snap_date),
        ).fetchone()
    return row is not None


def delete_snapshot_by_date(user_id: int, snap_date: str):
    """删除某用户某日快照（用于强制覆盖）"""
    raw_execute(
        "DELETE FROM net_worth_snapshots WHERE user_id=? AND snap_date=?",
        (user_id, snap_date),
    )


def list_snapshots(user_id: int, start: str = None, end: str = None,
                   order: str = "ASC", limit: int = None) -> List[dict]:
    """查询快照列表"""
    where = ["user_id=?"]
    params = [user_id]
    if start:
        where.append("snap_date >= ?")
        params.append(start)
    if end:
        where.append("snap_date <= ?")
        params.append(end)
    sql = f"SELECT * FROM net_worth_snapshots WHERE {' AND '.join(where)} ORDER BY snap_date {order}"
    if limit:
        sql += f" LIMIT {limit}"
    return raw_query(sql, tuple(params))


# ─── 用户设置专用 ──────────────────────────────────────

def get_setting(user_id: int, key: str) -> Optional[str]:
    """读取用户设置"""
    row = raw_query_one(
        "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_key=?",
        (user_id, key),
    )
    return row["setting_value"] if row else None


def upsert_setting(user_id: int, key: str, value: str):
    """写入或更新用户设置"""
    raw_execute(
        "INSERT INTO user_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value=excluded.setting_value",
        (user_id, key, value),
    )
