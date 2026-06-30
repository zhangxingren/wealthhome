"""资产管理 CRUD — 现金 / 定期 / 基金 / 股票 / 债权

分层架构：Router → Service → Repository → Database
"""

import json
import sys
from datetime import date, datetime, timedelta
from typing import Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user
from app.models.assets import (
    CashCreate, CashUpdate,
    DepositCreate, DepositUpdate,
    FundCreate, FundUpdate,
    StockCreate, StockUpdate,
    BondCreate, BondUpdate,
)
from app.repositories.asset_repo import (
    create_asset, get_by_id, list_by_user,
    update_asset, delete_asset, exists,
)
from app.services.asset_service import (
    calc_user_summary, calc_investment_summary,
    calc_family_summary,
)
from app.services.market_service import (
    fetch_stock_prices, fetch_stock_price_sina, fetch_fund_nav, guess_exchange,
)

router = APIRouter(prefix="/api/assets", tags=["资产"])

# ─── 通用 CRUD 工厂 ────────────────────────────────────

TABLE_MAP = {
    "asset_cash": ("cash", ["name","currency","amount","account_name","note","tags"], True),
    "asset_deposit": ("deposit", ["name","bank","principal","rate","start_date","end_date","currency","note","tags"], False),
    "asset_fund": ("fund", ["code","name","shares","cost_nav","current_nav","fund_type","note","tags"], True),
    "asset_stock": ("stock", ["code","name","shares","cost_price","current_price","market","note","tags"], True),
    "asset_bond": ("bond", ["name","issuer","face_value","rate","maturity_date","currency","quantity","cost_price","current_price","note","tags"], False),
}


def create_crud_router(
    table_name: str,
    model_in,
    row_mapper_fn: Callable,
):
    """为资产表生成 list/create/update/delete 四个标准端点（使用 Repository 层）"""
    prefix, insert_fields, has_updated_at = TABLE_MAP[table_name]
    all_fields = insert_fields.copy()

    update_fields = [f for f in insert_fields if f != "code"]  # code 不可更新

    def _list(limit: int = Query(default=100), offset: int = Query(default=0),
              user=Depends(get_current_user)):
        uid = int(user["sub"])
        items = list_by_user(table_name, uid, limit, offset)
        return [row_mapper_fn(r) for r in items]

    def _create(body: model_in, user=Depends(get_current_user)):
        uid = int(user["sub"])
        data = {"user_id": uid}
        for f in insert_fields:
            data[f] = getattr(body, f)
        new_id = create_asset(table_name, data)
        row = get_by_id(table_name, new_id)
        return row_mapper_fn(row)

    def _update(asset_id: int, body: model_in, user=Depends(get_current_user)):
        uid = int(user["sub"])
        if not exists(table_name, asset_id, uid):
            raise HTTPException(status_code=404, detail="资产不存在")
        data = {}
        for f in update_fields:
            data[f] = getattr(body, f)
        if has_updated_at:
            # updated_at 由 SQLite trigger 或显式设置
            pass
        update_asset(table_name, asset_id, uid, data)
        # 用 raw SQL 更新 updated_at 后重新读取
        from app.repositories.asset_repo import raw_execute
        if has_updated_at:
            raw_execute(
                f"UPDATE {table_name} SET updated_at=datetime('now','localtime') WHERE id=?",
                (asset_id,),
            )
        row = get_by_id(table_name, asset_id)
        return row_mapper_fn(row)

    def _delete(asset_id: int, user=Depends(get_current_user)):
        uid = int(user["sub"])
        if not delete_asset(table_name, asset_id, uid):
            raise HTTPException(status_code=404, detail="资产不存在")

    router.add_api_route(f"/{prefix}", _list, methods=["GET"])
    router.add_api_route(f"/{prefix}", _create, methods=["POST"], status_code=201)
    router.add_api_route(f"/{prefix}/{{asset_id}}", _update, methods=["PUT"])
    router.add_api_route(f"/{prefix}/{{asset_id}}", _delete, methods=["DELETE"], status_code=204)


# ─── 现金 / 活期 ───────────────────────────────────────

def _cash_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"],
            "currency": r["currency"], "amount": r["amount"],
            "account_name": r["account_name"], "note": r["note"],
            "tags": r["tags"], "created_at": r["created_at"], "updated_at": r["updated_at"]}

create_crud_router("asset_cash", CashCreate, _cash_row)


# ─── 定期存单 ──────────────────────────────────────────

def _deposit_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"],
            "bank": r["bank"], "principal": r["principal"], "rate": r["rate"],
            "start_date": r["start_date"], "end_date": r["end_date"],
            "currency": r["currency"], "note": r["note"], "tags": r["tags"],
            "created_at": r["created_at"]}

create_crud_router("asset_deposit", DepositCreate, _deposit_row)


@router.get("/deposit/{asset_id}/interest")
def get_deposit_interest(asset_id: int, user=Depends(get_current_user)):
    """计算定期存单已产生的利息"""
    uid = int(user["sub"])
    r = get_by_id("asset_deposit", asset_id, uid)
    if not r:
        raise HTTPException(status_code=404, detail="资产不存在")

    principal = r["principal"]
    rate_pct = r["rate"]
    rate = rate_pct / 100.0
    start = date.fromisoformat(r["start_date"])
    end_date = date.fromisoformat(r["end_date"])
    today = date.today()
    calc_date = min(today, end_date)
    days = (calc_date - start).days
    total_days = (end_date - start).days or 1
    total_interest = round(principal * rate * (total_days / 365), 2)
    accrued = round(principal * rate * (days / 365), 2)
    progress = round(days / total_days * 100, 1) if total_days > 0 else 0
    return {
        "principal": principal, "rate_pct": rate_pct,
        "start_date": r["start_date"], "end_date": r["end_date"],
        "days_elapsed": days, "total_days": total_days,
        "accrued_interest": accrued, "total_interest": total_interest,
        "progress_pct": progress,
    }


# ─── 基金 ──────────────────────────────────────────────

def _fund_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "code": r["code"],
            "name": r["name"], "shares": r["shares"], "cost_nav": r["cost_nav"],
            "current_nav": r["current_nav"], "fund_type": r["fund_type"],
            "note": r["note"], "tags": r["tags"],
            "created_at": r["created_at"], "updated_at": r["updated_at"]}

create_crud_router("asset_fund", FundCreate, _fund_row)


@router.post("/fund/fetch-prices")
async def fetch_fund_prices(payload: dict = {}, user=Depends(get_current_user)):
    """使用天天基金 / 东方财富公开接口刷新所有基金当前净值（并行请求）"""
    import asyncio
    uid = int(user["sub"])
    funds = list_by_user("asset_fund", uid)

    if not funds:
        return {"message": "无基金持仓", "updated": 0}

    async def _fetch_one(fund):
        result = await asyncio.to_thread(fetch_fund_nav, fund["code"])
        if result and result[0]:
            return (fund["id"], result[0], result[1])  # (id, nav, fund_type)
        return None

    results = await asyncio.gather(*[_fetch_one(f) for f in funds])

    updated = 0
    for res in results:
        if res is not None:
            fid, nav, fund_type = res
            from app.repositories.asset_repo import raw_execute
            raw_execute(
                "UPDATE asset_fund SET current_nav=?, fund_type=CASE WHEN ? != '' THEN ? ELSE fund_type END, "
                "updated_at=datetime('now','localtime') WHERE id=?",
                (nav, fund_type, fund_type, fid),
            )
            updated += 1

    return {"message": f"成功更新 {updated} 只基金净值", "updated": updated}


# ─── 股票 ──────────────────────────────────────────────

def _stock_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "code": r["code"],
            "name": r["name"], "shares": r["shares"],
            "cost_price": r["cost_price"], "current_price": r["current_price"],
            "market": r["market"], "note": r["note"], "tags": r["tags"],
            "created_at": r["created_at"], "updated_at": r["updated_at"]}

create_crud_router("asset_stock", StockCreate, _stock_row)


@router.post("/stock/fetch-prices")
def fetch_stock_prices_endpoint(payload: dict = {}, user=Depends(get_current_user)):
    """使用 Tushare daily API 批量刷新所有股票/ETF 最新收盘价（使用 Market Service）"""
    uid = int(user["sub"])

    # ── 获取 Tushare Token ──
    raw_key = payload.get("api_key", "")
    if isinstance(raw_key, dict):
        api_key = raw_key.get("token", "")
    elif isinstance(raw_key, str):
        api_key = raw_key.strip()
    else:
        api_key = str(raw_key).strip()

    if not api_key:
        from app.repositories.asset_repo import get_setting, upsert_setting
        stored = get_setting(uid, "tushare_token")
        if stored:
            token_data = json.loads(stored) if stored else {}
            api_key = token_data.get("token", "") if isinstance(token_data, dict) else str(stored)
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="请提供 Tushare API Key（可在用户设置中保存 tushare_token，或直接传参 api_key）",
            )
    else:
        from app.repositories.asset_repo import upsert_setting
        upsert_setting(uid, "tushare_token", json.dumps({"token": api_key}))

    # ── 获取持仓 ──
    stocks = list_by_user("asset_stock", uid)
    if not stocks:
        return {"message": "无股票持仓", "updated": 0}

    stock_list = [(s["id"], s["code"], s["market"]) for s in stocks]

    # ── 调用 Market Service ──
    results, failed_codes, debug = fetch_stock_prices(stock_list, api_key)

    # ── 新浪行情 API 兜底 ──
    sina_failed = []
    if failed_codes:
        code_map = {s["code"] + "." + guess_exchange(s["code"], s["market"]): s["id"] for s in stocks}
        for ts in failed_codes:
            price = fetch_stock_price_sina(ts)
            if price and price > 0:
                rid = code_map.get(ts)
                if rid:
                    from app.repositories.asset_repo import raw_execute
                    raw_execute(
                        "UPDATE asset_stock SET current_price=?, updated_at=datetime('now','localtime') WHERE id=?",
                        (price, rid),
                    )
                    updated_sina = debug.get("fetched", 0) + 1
                    results.append((rid, price))
                    print(f"[Sina] 兜底更新 {ts} 价格={price}", file=sys.stderr)
                    continue
            sina_failed.append(ts)

    if not results and debug.get("error"):
        raise HTTPException(status_code=502, detail=f"Tushare API 错误: {debug['error']}")

    if not results and sina_failed:
        return {
            "message": f"全部 {len(sina_failed)} 只股票均未获取到行情数据。可能原因：① Token 权限不足；② 股票代码格式错误；③ 网络连接失败。"
                       f"失败代码：{'; '.join(sina_failed[:5])}{'...' if len(sina_failed) > 5 else ''}",
            "updated": 0,
            "failed_stocks": sina_failed,
        }

    if not results and debug.get("fetched", 0) == 0:
        return {
            "message": "Tushare 未返回任何行情数据。可能原因：① Token 权限不足；② 股票代码格式错误；③ 网络连接失败。",
            "updated": 0,
        }

    # ── 更新数据库 ──
    from app.repositories.asset_repo import raw_execute
    updated = 0
    for rid, price in results:
        raw_execute(
            "UPDATE asset_stock SET current_price=?, updated_at=datetime('now','localtime') WHERE id=?",
            (price, rid),
        )
        updated += 1

    msg = f"成功更新 {updated} 只股票现价"
    if sina_failed:
        msg += f"，{len(sina_failed)} 只未返回数据：{'; '.join(sina_failed[:3])}{'...' if len(sina_failed) > 3 else ''}"
    return {"message": msg, "updated": updated, "failed_stocks": sina_failed}


# ─── 债权 ──────────────────────────────────────────────

def _bond_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"],
            "issuer": r["issuer"], "face_value": r["face_value"], "rate": r["rate"],
            "maturity_date": r["maturity_date"], "currency": r["currency"],
            "quantity": r.get("quantity", 1),
            "cost_price": r.get("cost_price", 0),
            "current_price": r.get("current_price", 0),
            "note": r["note"], "tags": r["tags"], "created_at": r["created_at"]}

create_crud_router("asset_bond", BondCreate, _bond_row)


# ─── 汇总查询 ──────────────────────────────────────────

@router.get("/summary")
def asset_summary(scope: str = "mine", user=Depends(get_current_user)):
    """资产汇总: scope=mine|family（使用 Service 层）"""
    uid = int(user["sub"])
    if scope == "family":
        from app.repositories.asset_repo import raw_query_one
        user_row = raw_query_one("SELECT family_id FROM users WHERE id=?", (uid,))
        if not user_row or not user_row["family_id"]:
            return {"members": {}, "family": calc_user_summary(uid)}
        result = calc_family_summary(user_row["family_id"])
        # 转换成员摘要格式以兼容前端
        members_summary = {}
        family_totals = {"cash": 0, "deposit": 0, "fund": 0, "stock": 0,
                         "bond": 0, "precious_metal": 0,
                         "total_asset": 0, "total_liability": 0, "net_worth": 0}
        for m in result.get("members", []):
            mid = str(m["user_id"])
            s = m["summary"]
            # 获取用户名
            urow = raw_query_one("SELECT username, display_name FROM users WHERE id=?", (m["user_id"],))
            members_summary[mid] = {
                "username": urow["username"] if urow else "",
                "display_name": (urow.get("display_name") or "") if urow else "",
                "summary": s,
            }
            for k in family_totals:
                family_totals[k] += s[k]
        family_totals = {k: round(v, 2) for k, v in family_totals.items()}
        return {"members": members_summary, "family": family_totals}
    else:
        return calc_user_summary(uid)


@router.get("/investment-summary")
def investment_summary(user=Depends(get_current_user)):
    """投资盈亏汇总：股票 + 基金 + 债券 + 贵金属（使用 Service 层）"""
    uid = int(user["sub"])
    return calc_investment_summary(uid)


@router.get("/family/investment-summary")
def family_investment_summary(user=Depends(get_current_user)):
    """家庭投资盈亏汇总（使用 Service 层）"""
    uid = int(user["sub"])
    from app.repositories.asset_repo import raw_query_one, raw_query
    user_row = raw_query_one("SELECT family_id FROM users WHERE id=?", (uid,))
    if not user_row or not user_row["family_id"]:
        return {"total_cost": 0, "total_market_value": 0, "total_profit": 0, "total_profit_pct": 0}
    members = raw_query("SELECT id FROM users WHERE family_id=?", (user_row["family_id"],))
    totals = {"total_cost": 0.0, "total_market_value": 0.0, "total_profit": 0.0, "total_profit_pct": 0.0}
    for m in members:
        s = calc_investment_summary(m["id"])
        totals["total_cost"] += s.get("total_cost", 0) or 0
        totals["total_market_value"] += s.get("total_market_value", 0) or 0
        totals["total_profit"] += s.get("total_profit", 0) or 0
    totals["total_cost"] = round(totals["total_cost"], 2)
    totals["total_market_value"] = round(totals["total_market_value"], 2)
    totals["total_profit"] = round(totals["total_profit"], 2)
    totals["total_profit_pct"] = round(totals["total_profit"] / totals["total_cost"] * 100, 2) if totals["total_cost"] > 0 else 0
    return totals


@router.get("/detail")
def asset_detail(
    category: Optional[str] = Query(None, description="分类: cash/deposit/fund/stock/bond/precious_metal"),
    user=Depends(get_current_user),
):
    """返回资产明细（使用 Service 层）"""
    uid = int(user["sub"])

    if not category:
        from app.services.asset_service import get_asset_detail
        return get_asset_detail(uid)

    # 单类别查询
    table_map = {
        "cash": ("asset_cash", _cash_row),
        "deposit": ("asset_deposit", _deposit_row),
        "fund": ("asset_fund", _fund_row),
        "stock": ("asset_stock", _stock_row),
        "bond": ("asset_bond", _bond_row),
    }
    if category in table_map:
        table, mapper = table_map[category]
        items = list_by_user(table, uid)
        return {category: [mapper(r) for r in items]}
    if category == "precious_metal":
        from app.routers.precious_metals import _fetch_user_pm
        return {"precious_metal": _fetch_user_pm(uid, include_hidden=True)}

    return {}


@router.get("/family/trend")
def family_trend(
    days: int = Query(30, ge=1, le=365),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    """家庭净值变化趋势"""
    from collections import defaultdict
    from app.repositories.asset_repo import raw_query, raw_query_one
    from app.routers.networth import take_auto_snapshot_for_all_users

    take_auto_snapshot_for_all_users(force=True)

    uid = int(user["sub"])
    user_row = raw_query_one("SELECT family_id FROM users WHERE id=?", (uid,))
    if not user_row or not user_row["family_id"]:
        return {"dates": [], "values": []}

    members = raw_query("SELECT id FROM users WHERE family_id=?", (user_row["family_id"],))
    if not members:
        return {"dates": [], "values": []}

    CAT_KEYS = ["cash", "deposit", "fund", "stock", "bond", "precious_metal", "total_liability"]
    member_hidden = {m["id"]: set() for m in members}

    viewer_settings = raw_query_one(
        "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_key='privacy_settings'",
        (uid,),
    )
    if viewer_settings:
        try:
            viewer_ps = json.loads(viewer_settings["setting_value"])
            family_hidden = viewer_ps.get("familyHiddenAssets", {}) or {}
            for mid_str, cats in family_hidden.items():
                mid = int(mid_str)
                if mid in member_hidden:
                    member_hidden[mid] = member_hidden[mid] | set(cats)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    member_ids = [m["id"] for m in members]
    placeholders = ",".join("?" * len(member_ids))
    where_clauses = [f"user_id IN ({placeholders})"]
    params = list(member_ids)
    if start:
        where_clauses.append("snap_date >= ?")
        params.append(start)
    if end:
        where_clauses.append("snap_date <= ?")
        params.append(end)

    snap_rows = raw_query(
        f"SELECT user_id, snap_date, net_worth, cash, deposit, fund, stock, bond, "
        f"precious_metal, total_liability FROM net_worth_snapshots "
        f"WHERE {' AND '.join(where_clauses)} ORDER BY snap_date ASC",
        tuple(params),
    )

    daily = defaultdict(float)
    for r in snap_rows:
        mid = r["user_id"]
        hidden = member_hidden.get(mid, set())
        nw = r["net_worth"]
        for cat in CAT_KEYS:
            if cat in hidden:
                if cat == "total_liability":
                    nw += (r[cat] or 0)
                else:
                    nw -= (r[cat] or 0)
        daily[r["snap_date"]] += nw

    sorted_dates = sorted(daily.keys())
    sorted_dates = sorted_dates[-days:] if len(sorted_dates) > days else sorted_dates
    return {
        "dates": sorted_dates,
        "values": [round(daily[d], 2) for d in sorted_dates],
    }
