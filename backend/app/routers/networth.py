"""净值快照 — 手动记录 + 历史趋势

分层架构：Router → Service → Repository → Database
"""

import json
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.services.asset_service import calc_user_summary
from app.repositories.asset_repo import (
    insert_snapshot, snapshot_exists, delete_snapshot_by_date,
    list_snapshots, delete_asset, get_by_id, raw_query, raw_query_one, raw_execute,
)

router = APIRouter(prefix="/api/networth", tags=["净值快照"])

CATEGORY_FIELDS = ["cash", "deposit", "fund", "stock", "bond", "precious_metal", "total_liability"]


def _get_hidden_categories(uid: int) -> set:
    """读取用户隐私设置，返回隐藏的资产类别集合"""
    row = raw_query_one(
        "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_key='privacy_settings'",
        (uid,),
    )
    if row:
        try:
            ps = json.loads(row["setting_value"])
            return set(ps.get("hiddenAssets", []))
        except (json.JSONDecodeError, TypeError):
            pass
    return set()


def take_auto_snapshot_for_all_users(force: bool = False):
    """为所有用户创建今日快照。force=False 时已存在则跳过；force=True 时覆盖今日快照"""
    today = date.today().isoformat()
    users = raw_query("SELECT id FROM users")
    for user in users:
        uid = user["id"]
        totals = calc_user_summary(uid)
        if force:
            delete_snapshot_by_date(uid, today)
        else:
            if snapshot_exists(uid, today):
                continue
        insert_snapshot(uid, today, totals)


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


# ─── 端点 ──────────────────────────────────────────────

@router.post("/snapshot", status_code=201)
def take_snapshot(
    snap_date: Optional[str] = Query(None, description="手动指定日期 yyyy-MM-dd，默认今天"),
    user=Depends(get_current_user),
):
    """记录当前时点净值快照，同一天不重复插入"""
    uid = int(user["sub"])
    totals = calc_user_summary(uid)
    snap = snap_date or date.today().isoformat()

    if snapshot_exists(uid, snap):
        raise HTTPException(status_code=409, detail=f"{snap} 已有快照记录")

    new_id = insert_snapshot(uid, snap, totals)
    row = get_by_id("net_worth_snapshots", new_id)
    return _snapshot_row(row)


@router.get("/snapshots")
def get_snapshots(
    start: Optional[str] = Query(None, description="开始日期 yyyy-MM-dd"),
    end: Optional[str] = Query(None, description="结束日期 yyyy-MM-dd"),
    user=Depends(get_current_user),
):
    """查询历史快照列表，按日期升序"""
    uid = int(user["sub"])
    rows = list_snapshots(uid, start, end, order="ASC")
    return [_snapshot_row(r) for r in rows]


@router.get("/trend")
def trend(
    limit: int = Query(30, ge=1, le=365),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    """最近 N 条快照趋势，返回原始快照数据；前端根据隐私设置自行过滤"""
    take_auto_snapshot_for_all_users(force=True)
    uid = int(user["sub"])
    rows = list_snapshots(uid, start, end, order="DESC", limit=limit)
    result = [_snapshot_row(r) for r in rows]
    result.reverse()
    return result


@router.get("/trend/category")
def trend_category(
    field: str = Query(..., description=f"资产类别: {', '.join(CATEGORY_FIELDS)}"),
    limit: int = Query(30, ge=1, le=365),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    """按资产类别返回趋势数据（每条快照中对应字段的值），隐藏类别返回 0"""
    if field not in CATEGORY_FIELDS:
        raise HTTPException(status_code=400, detail=f"无效类别，可选: {', '.join(CATEGORY_FIELDS)}")

    uid = int(user["sub"])
    hidden = _get_hidden_categories(uid)

    # 构建查询
    where = ["user_id=?"]
    params = [uid]
    if start:
        where.append("snap_date >= ?")
        params.append(start)
    if end:
        where.append("snap_date <= ?")
        params.append(end)

    sql = (f"SELECT snap_date, {field} as value FROM net_worth_snapshots "
           f"WHERE {' AND '.join(where)} ORDER BY snap_date DESC LIMIT ?")
    params.append(limit)
    rows = raw_query(sql, tuple(params))

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
    """最近一次快照 + 当前实时净值"""
    uid = int(user["sub"])
    totals = calc_user_summary(uid)

    last = raw_query_one(
        "SELECT * FROM net_worth_snapshots WHERE user_id=? ORDER BY snap_date DESC LIMIT 1",
        (uid,),
    )

    return {
        "last_snapshot": _snapshot_row(last) if last else None,
        "current": totals,
    }


@router.delete("/snapshot/{snapshot_id}", status_code=204)
def delete_snapshot(snapshot_id: int, user=Depends(get_current_user)):
    uid = int(user["sub"])
    if not delete_asset("net_worth_snapshots", snapshot_id, uid):
        raise HTTPException(status_code=404, detail="快照不存在")
