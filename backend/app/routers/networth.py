"""净值快照 — 手动记录 + 历史趋势"""

import json
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/networth", tags=["净值快照"])


def _get_hidden_categories(uid: int, db) -> set:
    """读取用户隐私设置，返回隐藏的资产类别集合"""
    row = db.execute(
        "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_key='privacy_settings'",
        (uid,)
    ).fetchone()
    if row:
        try:
            ps = json.loads(row["setting_value"])
            return set(ps.get("hiddenAssets", []))
        except (json.JSONDecodeError, TypeError):
            pass
    return set()


def _calc_totals(uid: int, db=None) -> dict:
    """计算当前用户各资产类别合计、总负债、净值（返回原始值，不做隐藏过滤）"""
    own_db = db is None
    if own_db:
        with get_db() as db:
            return _calc_totals_inner(uid, db)
    else:
        return _calc_totals_inner(uid, db)


# 债券估值 SQL（与 assets.py BOND_VALUATION_SQL 一致）
_BOND_VAL = (
    "COALESCE(SUM(quantity * COALESCE(NULLIF(current_price,0), "
    "NULLIF(cost_price,0), face_value)),0)"
)

def _calc_totals_inner(uid: int, db) -> dict:
    """计算当前用户各资产类别合计、总负债、净值（返回原始值，不排除隐藏类别）。
    隐藏类别的过滤由前端 / family_trend 端点各自处理。"""

    def _sum(query, *params):
        return db.execute(query, params).fetchone()[0]

    cash = _sum("SELECT COALESCE(SUM(amount),0) FROM asset_cash WHERE user_id=?", uid)
    deposit = _sum("SELECT COALESCE(SUM(principal),0) FROM asset_deposit WHERE user_id=?", uid)
    fund = _sum("SELECT COALESCE(SUM(shares*current_nav),0) FROM asset_fund WHERE user_id=?", uid)
    stock = _sum("SELECT COALESCE(SUM(shares*current_price),0) FROM asset_stock WHERE user_id=?", uid)
    bond = _sum(f"SELECT {_BOND_VAL} FROM asset_bond WHERE user_id=?", uid)
    precious_metal = _sum(
        "SELECT COALESCE(SUM(weight_grams * COALESCE(current_price_per_gram, buy_price_per_gram)), 0) "
        "FROM asset_precious_metal WHERE user_id=? AND is_hidden=0", uid)
    debt = _sum("SELECT COALESCE(SUM(remaining),0) FROM liabilities WHERE user_id=?", uid)

    total_asset = cash + deposit + fund + stock + bond + precious_metal
    return {
        "cash": round(cash, 2),
        "deposit": round(deposit, 2),
        "fund": round(fund, 2),
        "stock": round(stock, 2),
        "bond": round(bond, 2),
        "precious_metal": round(precious_metal, 2),
        "total_asset": round(total_asset, 2),
        "total_liability": round(debt, 2),
        "net_worth": round(total_asset - debt, 2),
    }


def take_auto_snapshot_for_all_users(force: bool = False):
    """为所有用户创建今日快照。force=False 时已存在则跳过；force=True 时覆盖今日快照（用于趋势图实时刷新）"""
    today = date.today().isoformat()
    with get_db() as db:
        users = db.execute("SELECT id FROM users").fetchall()
        for user in users:
            uid = user["id"]
            totals = _calc_totals(uid)
            if force:
                db.execute(
                    "DELETE FROM net_worth_snapshots WHERE user_id=? AND snap_date=?",
                    (uid, today),
                )
            else:
                existing = db.execute(
                    "SELECT id FROM net_worth_snapshots WHERE user_id=? AND snap_date=?",
                    (uid, today),
                ).fetchone()
                if existing:
                    continue
            db.execute(
                "INSERT INTO net_worth_snapshots "
                "(user_id,total_asset,total_debt,net_worth,snap_date,"
                "cash,deposit,fund,stock,bond,precious_metal,total_liability) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid,
                 totals["total_asset"], totals["total_liability"], totals["net_worth"], today,
                 totals["cash"], totals["deposit"], totals["fund"], totals["stock"],
                 totals["bond"], totals["precious_metal"], totals["total_liability"]),
            )
        db.commit()


class SnapshotOut(BaseModel):
    id: int
    user_id: int
    total_asset: float
    total_debt: float
    net_worth: float
    snap_date: str
    created_at: str


def _snapshot_row(r) -> dict:
    return {
        "id": r["id"], "user_id": r["user_id"],
        "total_asset": r["total_asset"], "total_debt": r["total_debt"],
        "net_worth": r["net_worth"], "snap_date": r["snap_date"],
        "created_at": r["created_at"],
        "cash": r["cash"], "deposit": r["deposit"],
        "fund": r["fund"], "stock": r["stock"],
        "bond": r["bond"], "precious_metal": r["precious_metal"],
        "total_liability": r["total_liability"],
    }


@router.post("/snapshot", status_code=201)
def take_snapshot(
    snap_date: Optional[str] = Query(None, description="手动指定日期 yyyy-MM-dd，默认今天"),
    user=Depends(get_current_user),
):
    """记录当前时点净值快照，同一天不重复插入"""
    uid = int(user["sub"])
    totals = _calc_totals(uid)
    snap = snap_date or date.today().isoformat()

    with get_db() as db:
        # 同一天已有快照则跳过
        existing = db.execute(
            "SELECT id FROM net_worth_snapshots WHERE user_id=? AND snap_date=?",
            (uid, snap),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"{snap} 已有快照记录")

        cur = db.execute(
            "INSERT INTO net_worth_snapshots "
            "(user_id,total_asset,total_debt,net_worth,snap_date,"
            "cash,deposit,fund,stock,bond,precious_metal,total_liability) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid,
             totals["total_asset"], totals["total_liability"], totals["net_worth"], snap,
             totals["cash"], totals["deposit"], totals["fund"], totals["stock"],
             totals["bond"], totals["precious_metal"], totals["total_liability"]),
        )
        row = db.execute(
            "SELECT * FROM net_worth_snapshots WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    return _snapshot_row(row)


@router.get("/snapshots")
def list_snapshots(
    start: Optional[str] = Query(None, description="开始日期 yyyy-MM-dd"),
    end: Optional[str] = Query(None, description="结束日期 yyyy-MM-dd"),
    user=Depends(get_current_user),
):
    """查询历史快照列表，按日期升序"""
    uid = int(user["sub"])
    with get_db() as db:
        if start and end:
            rows = db.execute(
                "SELECT * FROM net_worth_snapshots WHERE user_id=? AND snap_date BETWEEN ? AND ? ORDER BY snap_date ASC",
                (uid, start, end),
            ).fetchall()
        elif start:
            rows = db.execute(
                "SELECT * FROM net_worth_snapshots WHERE user_id=? AND snap_date >= ? ORDER BY snap_date ASC",
                (uid, start),
            ).fetchall()
        elif end:
            rows = db.execute(
                "SELECT * FROM net_worth_snapshots WHERE user_id=? AND snap_date <= ? ORDER BY snap_date ASC",
                (uid, end),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM net_worth_snapshots WHERE user_id=? ORDER BY snap_date ASC",
                (uid,),
            ).fetchall()
    return [_snapshot_row(r) for r in rows]


@router.get("/trend")
def trend(limit: int = Query(30, ge=1, le=365), user=Depends(get_current_user)):
    """最近 N 条快照趋势，返回原始快照数据；前端根据隐私设置自行过滤"""
    # 强制刷新今日快照，确保刚更新的资产价格反映在趋势图中
    take_auto_snapshot_for_all_users(force=True)
    uid = int(user["sub"])
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM net_worth_snapshots WHERE user_id=? ORDER BY snap_date DESC LIMIT ?",
            (uid, limit),
        ).fetchall()
    result = [_snapshot_row(r) for r in rows]
    result.reverse()
    return result


CATEGORY_FIELDS = ["cash", "deposit", "fund", "stock", "bond", "precious_metal", "total_liability"]


@router.get("/trend/category")
def trend_category(
    field: str = Query(..., description=f"资产类别: {', '.join(CATEGORY_FIELDS)}"),
    limit: int = Query(30, ge=1, le=365),
    user=Depends(get_current_user),
):
    """按资产类别返回趋势数据（每条快照中对应字段的值），隐藏类别返回 0"""
    if field not in CATEGORY_FIELDS:
        raise HTTPException(status_code=400, detail=f"无效类别，可选: {', '.join(CATEGORY_FIELDS)}")
    uid = int(user["sub"])
    with get_db() as db:
        hidden = _get_hidden_categories(uid, db)
        rows = db.execute(
            f"SELECT snap_date, {field} as value FROM net_worth_snapshots "
            "WHERE user_id=? ORDER BY snap_date DESC LIMIT ?",
            (uid, limit),
        ).fetchall()
    result = []
    for r in rows:
        val = r["value"]
        if field in hidden:
            val = 0
        result.append({"snap_date": r["snap_date"], "value": val})
    result.reverse()
    return result


@router.get("/latest")
def latest(user=Depends(get_current_user)):
    """最近一次快照 + 当前实时净值（就算今天没快照也返回实时数据）"""
    uid = int(user["sub"])
    totals = _calc_totals(uid)

    with get_db() as db:
        last_row = db.execute(
            "SELECT * FROM net_worth_snapshots WHERE user_id=? ORDER BY snap_date DESC LIMIT 1",
            (uid,),
        ).fetchone()

    return {
        "last_snapshot": _snapshot_row(last_row) if last_row else None,
        "current": totals,
    }


@router.delete("/snapshot/{snapshot_id}", status_code=204)
def delete_snapshot(snapshot_id: int, user=Depends(get_current_user)):
    uid = int(user["sub"])
    with get_db() as db:
        r = db.execute(
            "DELETE FROM net_worth_snapshots WHERE id=? AND user_id=?",
            (snapshot_id, uid),
        )
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="快照不存在")
