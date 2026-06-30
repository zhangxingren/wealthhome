"""贵金属资产 — 黄金 / 白银 / 铂金 / 钯金

分层架构：Router → Service/Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user
from app.models.assets import PreciousMetalCreate, PreciousMetalUpdate
from app.repositories.asset_repo import (
    create_asset, get_by_id, list_by_user,
    update_asset, exists, raw_execute, raw_query,
)
from app.services.market_service import fetch_precious_metal_price

TABLE = "asset_precious_metal"

router = APIRouter(prefix="/api/precious-metals", tags=["贵金属"])

TYPE_LABELS = {
    "gold": "黄金", "silver": "白银",
    "platinum": "铂金", "palladium": "钯金",
}


def _row(r) -> dict:
    buy_total = r["buy_total"] or (r["weight_grams"] * r["buy_price_per_gram"])
    current_value = r["weight_grams"] * (r["current_price_per_gram"] or 0)
    profit = current_value - buy_total
    profit_pct = (profit / buy_total * 100) if buy_total > 0 else 0
    return {
        "id": r["id"], "user_id": r["user_id"], "name": r["name"],
        "type": r["type"], "type_label": TYPE_LABELS.get(r["type"], r["type"]),
        "weight_grams": r["weight_grams"],
        "buy_price_per_gram": r["buy_price_per_gram"],
        "buy_date": r["buy_date"],
        "buy_total": round(buy_total, 2),
        "current_price_per_gram": r["current_price_per_gram"] or 0,
        "current_value": round(current_value, 2),
        "profit": round(profit, 2),
        "profit_pct": round(profit_pct, 2),
        "notes": r["notes"] or "",
        "is_hidden": bool(r["is_hidden"]),
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    }


def _fetch_user_pm(uid: int, include_hidden: bool = False):
    """获取用户贵金属列表（供其他 router 调用）"""
    if include_hidden:
        items = list_by_user(TABLE, uid)
    else:
        items = raw_query(
            f"SELECT * FROM {TABLE} WHERE user_id=? AND is_hidden=0 ORDER BY id DESC",
            (uid,),
        )
    return [_row(r) for r in items]


# ─── CRUD ──────────────────────────────────────────────

@router.get("")
def list_precious_metals(limit: int = Query(default=100), offset: int = Query(default=0),
                         user=Depends(get_current_user)):
    all_items = _fetch_user_pm(int(user["sub"]))
    return all_items[offset:offset + limit]


@router.post("", status_code=201)
def create_precious_metal(body: PreciousMetalCreate, user=Depends(get_current_user)):
    buy_total = body.buy_total if body.buy_total > 0 else round(body.weight_grams * body.buy_price_per_gram, 2)
    uid = int(user["sub"])
    data = {
        "user_id": uid,
        "name": body.name, "type": body.type,
        "weight_grams": body.weight_grams,
        "buy_price_per_gram": body.buy_price_per_gram,
        "buy_date": body.buy_date,
        "buy_total": buy_total,
        "current_price_per_gram": body.current_price_per_gram or 0,
        "notes": body.notes or "",
    }
    new_id = create_asset(TABLE, data)
    row = get_by_id(TABLE, new_id)
    return _row(row)


@router.put("/{pm_id}")
def update_precious_metal(pm_id: int, body: PreciousMetalCreate, user=Depends(get_current_user)):
    uid = int(user["sub"])
    if not exists(TABLE, pm_id, uid):
        raise HTTPException(status_code=404, detail="贵金属资产不存在")

    buy_total = body.buy_total if body.buy_total > 0 else round(body.weight_grams * body.buy_price_per_gram, 2)
    data = {
        "name": body.name, "type": body.type,
        "weight_grams": body.weight_grams,
        "buy_price_per_gram": body.buy_price_per_gram,
        "buy_date": body.buy_date,
        "buy_total": buy_total,
        "current_price_per_gram": body.current_price_per_gram or 0,
        "notes": body.notes or "",
    }
    update_asset(TABLE, pm_id, uid, data)
    raw_execute(
        f"UPDATE {TABLE} SET updated_at=datetime('now','localtime') WHERE id=?",
        (pm_id,),
    )
    row = get_by_id(TABLE, pm_id)
    return _row(row)


@router.delete("/{pm_id}", status_code=204)
def delete_precious_metal(pm_id: int, user=Depends(get_current_user)):
    """软删除：设置 is_hidden = 1"""
    uid = int(user["sub"])
    if not exists(TABLE, pm_id, uid):
        raise HTTPException(status_code=404, detail="贵金属资产不存在")
    raw_execute(
        f"UPDATE {TABLE} SET is_hidden=1, updated_at=datetime('now','localtime') WHERE id=?",
        (pm_id,),
    )


# ─── 实时价格刷新 ──────────────────────────────────────

@router.post("/refresh")
def refresh_prices(user=Depends(get_current_user)):
    """使用 Market Service 获取最新贵金属价格并刷新所有持仓"""
    uid = int(user["sub"])
    rows = raw_query(
        f"SELECT id, type FROM {TABLE} WHERE user_id=? AND is_hidden=0",
        (uid,),
    )
    if not rows:
        return {"message": "无贵金属持仓", "updated": 0}

    # 获取各类型价格
    prices = {}
    for metal_type in set(r["type"] for r in rows):
        price = fetch_precious_metal_price(metal_type)
        if price:
            prices[metal_type] = price

    if not prices:
        return {"message": "暂时无法获取贵金属实时价格，请稍后重试", "updated": 0, "prices": {}}

    # 更新数据库
    updated = 0
    for r in rows:
        p = prices.get(r["type"])
        if p and p > 0:
            raw_execute(
                f"UPDATE {TABLE} SET current_price_per_gram=?, updated_at=datetime('now','localtime') WHERE id=?",
                (p, r["id"]),
            )
            updated += 1

    return {
        "message": f"成功更新 {updated} 条持仓价格",
        "updated": updated,
        "prices": {TYPE_LABELS.get(k, k): round(v, 2) for k, v in prices.items()},
    }


# ─── 盈亏汇总 ──────────────────────────────────────────

@router.get("/summary")
def precious_metal_summary(user=Depends(get_current_user)):
    """贵金属盈亏汇总"""
    uid = int(user["sub"])
    items = _fetch_user_pm(uid)
    total_cost = sum(it["buy_total"] for it in items)
    total_value = sum(it["current_value"] for it in items)
    total_profit = total_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    return {
        "count": len(items),
        "total_cost": round(total_cost, 2),
        "total_market_value": round(total_value, 2),
        "total_profit": round(total_profit, 2),
        "total_profit_pct": round(total_profit_pct, 2),
        "items": items,
    }
