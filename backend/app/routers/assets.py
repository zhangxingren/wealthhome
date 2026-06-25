"""资产管理 CRUD — 现金 / 定期 / 基金 / 股票 / 债权"""

from typing import Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.database import get_db
import asyncio
from app.auth import get_current_user

router = APIRouter(prefix="/api/assets", tags=["资产"])

# ─── 通用 CRUD 工厂 ────────────────────────────────────

ALLOWED_TABLES = {"asset_cash", "asset_deposit", "asset_fund", "asset_stock", "asset_bond"}

BOND_VALUATION_SQL = (
    "COALESCE(SUM(quantity * COALESCE(NULLIF(current_price,0), "
    "NULLIF(cost_price,0), face_value)),0)"
)

def create_crud_router(
    table_name: str,
    model_in,
    row_mapper_fn: Callable,
    *,
    insert_fields: list[str],
    update_fields: list[str],
    has_updated_at: bool = True,
    custom_list_fn: Optional[Callable] = None,
):
    """为资产表生成 list/create/update/delete 四个标准端点"""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"不允许的表名: {table_name}")
    prefix = table_name.replace("asset_", "")

    def _list(limit: int = Query(default=100), offset: int = Query(default=0), user=Depends(get_current_user)):
        if custom_list_fn:
            return custom_list_fn(user)
        with get_db() as db:
            rows = db.execute(
                f"SELECT * FROM {table_name} WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (int(user["sub"]), limit, offset),
            ).fetchall()
        return [row_mapper_fn(r) for r in rows]

    def _create(body: model_in, user=Depends(get_current_user)):
        uid = int(user["sub"])
        cols = "user_id," + ",".join(insert_fields)
        placeholders = ",".join(["?"] * (len(insert_fields) + 1))
        vals = (uid, *(getattr(body, f) for f in insert_fields))
        with get_db() as db:
            cur = db.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", vals)
            row = db.execute(f"SELECT * FROM {table_name} WHERE id=?", (cur.lastrowid,)).fetchone()
        return row_mapper_fn(row)

    def _update(asset_id: int, body: model_in, user=Depends(get_current_user)):
        uid = int(user["sub"])
        with get_db() as db:
            r = db.execute(
                f"SELECT id FROM {table_name} WHERE id=? AND user_id=?", (asset_id, uid)
            ).fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="资产不存在")
            set_parts = [f"{f}=?" for f in update_fields]
            if has_updated_at:
                set_parts.append("updated_at=datetime('now','localtime')")
            set_clause = ",".join(set_parts)
            vals = (*(getattr(body, f) for f in update_fields), asset_id)
            db.execute(f"UPDATE {table_name} SET {set_clause} WHERE id=?", vals)
            row = db.execute(f"SELECT * FROM {table_name} WHERE id=?", (asset_id,)).fetchone()
        return row_mapper_fn(row)

    def _delete(asset_id: int, user=Depends(get_current_user)):
        uid = int(user["sub"])
        with get_db() as db:
            r = db.execute(f"DELETE FROM {table_name} WHERE id=? AND user_id=?", (asset_id, uid))
            if r.rowcount == 0:
                raise HTTPException(status_code=404, detail="资产不存在")

    router.add_api_route(f"/{prefix}", _list, methods=["GET"])
    router.add_api_route(f"/{prefix}", _create, methods=["POST"], status_code=201)
    router.add_api_route(f"/{prefix}/{{asset_id}}", _update, methods=["PUT"])
    router.add_api_route(f"/{prefix}/{{asset_id}}", _delete, methods=["DELETE"], status_code=204)


# ─── 现金 / 活期 ───────────────────────────────────────

class CashIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    currency: str = "CNY"
    amount: float = 0
    account_name: str = ""
    note: str = ""
    tags: str = ""


class CashOut(CashIn):
    id: int
    user_id: int
    created_at: str
    updated_at: str


def _cash_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"], "currency": r["currency"],
            "amount": r["amount"], "account_name": r["account_name"], "note": r["note"],
            "tags": r["tags"], "created_at": r["created_at"], "updated_at": r["updated_at"]}


create_crud_router(
    "asset_cash", CashIn, _cash_row,
    insert_fields=["name", "currency", "amount", "account_name", "note", "tags"],
    update_fields=["name", "currency", "amount", "account_name", "note", "tags"],
    has_updated_at=True,
)


# ─── 定期存单 ──────────────────────────────────────────

class DepositIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    bank: str = ""
    principal: float = Field(0, ge=0, le=1e12)
    rate: float = Field(0, ge=0, le=100)
    start_date: str
    end_date: str
    currency: str = "CNY"
    note: str = ""
    tags: str = ""


def _deposit_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"], "bank": r["bank"],
            "principal": r["principal"], "rate": r["rate"], "start_date": r["start_date"],
            "end_date": r["end_date"], "currency": r["currency"], "note": r["note"],
            "tags": r["tags"], "created_at": r["created_at"]}


create_crud_router(
    "asset_deposit", DepositIn, _deposit_row,
    insert_fields=["name", "bank", "principal", "rate", "start_date", "end_date", "currency", "note", "tags"],
    update_fields=["name", "bank", "principal", "rate", "start_date", "end_date", "currency", "note", "tags"],
    has_updated_at=False,
)


@router.get("/deposit/{asset_id}/interest")
def get_deposit_interest(asset_id: int, user=Depends(get_current_user)):
    """计算定期存单已产生的利息"""
    from datetime import date
    with get_db() as db:
        r = db.execute("SELECT * FROM asset_deposit WHERE id=? AND user_id=?", (asset_id, int(user["sub"]))).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="资产不存在")
        principal = r["principal"]
        rate = r["rate"] / 100.0
        start = date.fromisoformat(r["start_date"])
        end = date.fromisoformat(r["end_date"])
        today = date.today()
        calc_date = min(today, end)
        days = (calc_date - start).days
        total_days = (end - start).days or 1
        total_interest = round(principal * rate * (total_days / 365), 2)
        accrued_interest = round(principal * rate * (days / 365), 2)
        progress = round(days / total_days * 100, 1) if total_days > 0 else 0
        return {
            "principal": principal,
            "rate_pct": r["rate"],
            "start_date": r["start_date"],
            "end_date": r["end_date"],
            "days_elapsed": days,
            "total_days": total_days,
            "accrued_interest": accrued_interest,
            "total_interest": total_interest,
            "progress_pct": progress,
        }


# ─── 基金 ──────────────────────────────────────────────

class FundIn(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)
    name: str = Field(..., min_length=1, max_length=64)
    shares: float = 0
    cost_nav: float = 0
    current_nav: float = 0
    fund_type: str = ""
    note: str = ""
    tags: str = ""


def _fund_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "code": r["code"], "name": r["name"],
            "shares": r["shares"], "cost_nav": r["cost_nav"], "current_nav": r["current_nav"],
            "fund_type": r["fund_type"], "note": r["note"], "tags": r["tags"],
            "created_at": r["created_at"], "updated_at": r["updated_at"]}


create_crud_router(
    "asset_fund", FundIn, _fund_row,
    insert_fields=["code", "name", "shares", "cost_nav", "current_nav", "fund_type", "note", "tags"],
    update_fields=["code", "name", "shares", "cost_nav", "current_nav", "fund_type", "note", "tags"],
    has_updated_at=True,
)


@router.post("/fund/fetch-prices")
async def fetch_fund_prices(payload: dict, user=Depends(get_current_user)):
    """使用天天基金公开接口刷新所有基金当前净值（并行请求）"""
    import httpx
    import re
    import json
    uid = int(user["sub"])
    with get_db() as db:
        rows = db.execute("SELECT id,code FROM asset_fund WHERE user_id=?", (uid,)).fetchall()
    if not rows:
        return {"message": "无基金持仓", "updated": 0}

    async def _fetch_one(r):
        try:
            url = f"https://fundgz.1234567.com.cn/js/{r['code']}.js"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers={"Referer": "https://fund.eastmoney.com/"})
            if resp.status_code != 200:
                return None
            match = re.search(r'jsonpgz\((\{.*\})\)', resp.text)
            nav = None
            if match:
                data = json.loads(match.group(1))
                def _safe_nav(s):
                    try:
                        v = float(s)
                        return v if v > 0 else 0.0
                    except (ValueError, TypeError):
                        return 0.0
                gsz = _safe_nav(data.get("gsz", ""))
                dwjz = _safe_nav(data.get("dwjz", ""))
                nav = gsz or dwjz
            # 天天基金 gz 接口返回空数据时，用东方财富 NAV 接口兜底（LOF 等基金）
            if not nav or nav <= 0:
                try:
                    nav_url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={r['code']}&pageIndex=1&pageSize=1"
                    async with httpx.AsyncClient(timeout=10) as client2:
                        nav_resp = await client2.get(nav_url, headers={"Referer": "https://fund.eastmoney.com/"})
                    if nav_resp.status_code == 200:
                        nav_data = nav_resp.json()
                        items = nav_data.get("Data", {}).get("LSJZList", [])
                        if items:
                            dwjz_val = float(items[0].get("DWJZ", 0))
                            if dwjz_val > 0:
                                nav = dwjz_val
                except Exception:
                    pass
            if nav and nav > 0:
                return (r["id"], nav)
        except Exception:
            return None

    results = await asyncio.gather(*[_fetch_one(r) for r in rows])
    updated = 0
    with get_db() as db:
        for res in results:
            if res is not None:
                fid, nav = res
                db.execute(
                    "UPDATE asset_fund SET current_nav=?, updated_at=datetime('now','localtime') WHERE id=?",
                    (nav, fid))
                updated += 1
    return {"message": f"成功更新 {updated} 只基金净值", "updated": updated}


# ─── 股票 ──────────────────────────────────────────────

class StockIn(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)
    name: str = Field(..., min_length=1, max_length=64)
    shares: float = 0
    cost_price: float = 0
    current_price: float = 0
    market: str = "sh"
    note: str = ""
    tags: str = ""


def _stock_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "code": r["code"], "name": r["name"],
            "shares": r["shares"], "cost_price": r["cost_price"], "current_price": r["current_price"],
            "market": r["market"], "note": r["note"], "tags": r["tags"],
            "created_at": r["created_at"], "updated_at": r["updated_at"]}


create_crud_router(
    "asset_stock", StockIn, _stock_row,
    insert_fields=["code", "name", "shares", "cost_price", "current_price", "market", "note", "tags"],
    update_fields=["code", "name", "shares", "cost_price", "current_price", "market", "note", "tags"],
    has_updated_at=True,
)


@router.post("/stock/fetch-prices")
def fetch_stock_prices(payload: dict = {}, user=Depends(get_current_user)):
    """使用 Tushare daily API 批量刷新所有股票/ETF 最新收盘价"""
    import requests as req

    api_key = payload.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="请提供 Tushare API Key")

    uid = int(user["sub"])
    with get_db() as db:
        rows = db.execute("SELECT id,code,market FROM asset_stock WHERE user_id=?", (uid,)).fetchall()
    if not rows:
        return {"message": "无股票持仓", "updated": 0}

    ts_codes = []
    code_map = {}  # ts_code -> row_id
    for r in rows:
        mkt = r["market"].upper()
        ts = r["code"] + "." + mkt
        ts_codes.append(ts)
        code_map[ts] = r["id"]

    try:
        resp = req.post(
            "https://api.tushare.pro",
            json={
                "api_name": "daily",
                "token": api_key,
                "params": {"ts_code": ",".join(ts_codes), "limit": 200},
                "fields": "ts_code,close",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Tushare API 请求失败: {str(e)}")

    if data.get("code") != 0:
        raise HTTPException(status_code=502, detail=f"Tushare 返回错误: {data.get('msg', '未知错误')}")

    items = data.get("data", {}).get("items", [])
    if not items:
        return {"message": "Tushare 未返回任何行情数据", "updated": 0}

    seen = set()
    price_map = {}  # ts_code -> close_price
    for row_data in items:
        ts_code = row_data[0]
        close_price = float(row_data[1])
        if ts_code not in seen:
            seen.add(ts_code)
            price_map[ts_code] = close_price

    import re

    updated = 0
    failed_codes = []
    with get_db() as db:
        for ts, rid in code_map.items():
            price = price_map.get(ts)
            if price is None:
                failed_codes.append(ts)
                continue
            db.execute(
                "UPDATE asset_stock SET current_price=?, updated_at=datetime('now','localtime') WHERE id=?",
                (price, rid),
            )
            updated += 1

    # ── 新浪行情 API 兜底 ──
    sina_failed = []
    for ts in failed_codes:
        try:
            parts = ts.split(".")
            if len(parts) != 2:
                sina_failed.append(ts)
                continue
            code, market = parts
            sina_url = f"http://hq.sinajs.cn/list={market.lower()}{code}"
            sina_resp = req.get(
                sina_url,
                headers={"Referer": "https://finance.sina.com.cn"},
                timeout=10,
            )
            sina_resp.encoding = "gbk"
            text = sina_resp.text
            match = re.search(r'"([^"]+)"', text)
            if match:
                fields = match.group(1).split(",")
                if len(fields) >= 4 and fields[3]:
                    price = float(fields[3])
                    if price > 0:
                        rid = code_map[ts]
                        with get_db() as db:
                            db.execute(
                                "UPDATE asset_stock SET current_price=?, updated_at=datetime('now','localtime') WHERE id=?",
                                (price, rid),
                            )
                        updated += 1
                        continue
            sina_failed.append(ts)
        except Exception:
            sina_failed.append(ts)

    failed_codes = sina_failed

    msg = f"成功更新 {updated} 只股票现价"
    if failed_codes:
        msg += f"，{len(failed_codes)} 只未返回数据：{'; '.join(failed_codes)}"
    return {"message": msg, "updated": updated, "failed_stocks": failed_codes}


# ─── 债权 ──────────────────────────────────────────────

class BondIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    issuer: str = ""
    face_value: float = 0
    rate: float = 0
    maturity_date: str
    currency: str = "CNY"
    quantity: float = 1
    cost_price: float = 0
    current_price: float = 0
    note: str = ""
    tags: str = ""


def _bond_row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"], "issuer": r["issuer"],
            "face_value": r["face_value"], "rate": r["rate"], "maturity_date": r["maturity_date"],
            "currency": r["currency"], "quantity": r.get("quantity", 1),
            "cost_price": r.get("cost_price", 0), "current_price": r.get("current_price", 0),
            "note": r["note"], "tags": r["tags"], "created_at": r["created_at"]}


create_crud_router(
    "asset_bond", BondIn, _bond_row,
    insert_fields=["name", "issuer", "face_value", "rate", "maturity_date", "currency", "quantity", "cost_price", "current_price", "note", "tags"],
    update_fields=["name", "issuer", "face_value", "rate", "maturity_date", "currency", "quantity", "cost_price", "current_price", "note", "tags"],
    has_updated_at=False,
)


# ─── 汇总查询（供 OpenClaw AI 调用）───────────────────

def _user_summary(uid: int, db) -> dict:
    cash = db.execute("SELECT COALESCE(SUM(amount),0) FROM asset_cash WHERE user_id=?", (uid,)).fetchone()[0]
    deposit = db.execute("SELECT COALESCE(SUM(principal),0) FROM asset_deposit WHERE user_id=?", (uid,)).fetchone()[0]
    fund = db.execute("SELECT COALESCE(SUM(shares*current_nav),0) FROM asset_fund WHERE user_id=?", (uid,)).fetchone()[0]
    stock = db.execute("SELECT COALESCE(SUM(shares*current_price),0) FROM asset_stock WHERE user_id=?", (uid,)).fetchone()[0]
    bond = db.execute(f"SELECT {BOND_VALUATION_SQL} FROM asset_bond WHERE user_id=?", (uid,)).fetchone()[0]
    precious_metal = db.execute(
        "SELECT COALESCE(SUM(weight_grams * COALESCE(current_price_per_gram, buy_price_per_gram)), 0) "
        "FROM asset_precious_metal WHERE user_id=? AND is_hidden=0", (uid,)
    ).fetchone()[0]
    debt = db.execute("SELECT COALESCE(SUM(remaining),0) FROM liabilities WHERE user_id=?", (uid,)).fetchone()[0]
    total = cash + deposit + fund + stock + bond + precious_metal
    return {
        "cash": round(cash, 2),
        "deposit": round(deposit, 2),
        "fund": round(fund, 2),
        "stock": round(stock, 2),
        "bond": round(bond, 2),
        "precious_metal": round(precious_metal, 2),
        "total_asset": round(total, 2),
        "total_liability": round(debt, 2),
        "net_worth": round(total - debt, 2),
    }


def _calc_investment_summary(db, user_ids: list) -> dict:
    """共用投资盈亏计算：支持个人 / 家庭（传入不同 user_ids）"""
    placeholders = ",".join("?" * len(user_ids))

    stock = db.execute(
        f"SELECT COALESCE(SUM(cost_price*shares),0), COALESCE(SUM(current_price*shares),0) "
        f"FROM asset_stock WHERE user_id IN ({placeholders})", user_ids
    ).fetchone()
    fund = db.execute(
        f"SELECT COALESCE(SUM(cost_nav*shares),0), COALESCE(SUM(current_nav*shares),0) "
        f"FROM asset_fund WHERE user_id IN ({placeholders})", user_ids
    ).fetchone()
    bond = db.execute(
        f"SELECT COALESCE(SUM(quantity * cost_price),0), "
        f"{BOND_VALUATION_SQL} "
        f"FROM asset_bond WHERE user_id IN ({placeholders})", user_ids
    ).fetchone()
    pm = db.execute(
        f"SELECT COALESCE(SUM(buy_total),0), "
        f"COALESCE(SUM(weight_grams * COALESCE(current_price_per_gram, buy_price_per_gram)),0) "
        f"FROM asset_precious_metal WHERE user_id IN ({placeholders}) AND is_hidden=0", user_ids
    ).fetchone()

    total_cost = round(stock[0] + fund[0] + bond[0] + pm[0], 2)
    total_market_value = round(stock[1] + fund[1] + bond[1] + pm[1], 2)
    total_profit = round(total_market_value - total_cost, 2)
    total_profit_pct = round(total_profit / total_cost * 100, 2) if total_cost > 0 else 0

    return {
        "total_cost": total_cost,
        "total_market_value": total_market_value,
        "total_profit": total_profit,
        "total_profit_pct": total_profit_pct,
    }


@router.get("/investment-summary")
def investment_summary(user=Depends(get_current_user)):
    """投资盈亏汇总：股票 + 基金 + 债券 + 贵金属"""
    uid = int(user["sub"])
    with get_db() as db:
        return _calc_investment_summary(db, [uid])


@router.get("/family/investment-summary")
def family_investment_summary(user=Depends(get_current_user)):
    """家庭投资盈亏汇总：汇总所有家庭成员的投资情况"""
    uid = int(user["sub"])
    with get_db() as db:
        user_row = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
        if not user_row or not user_row["family_id"]:
            return {"total_cost": 0, "total_market_value": 0, "total_profit": 0, "total_profit_pct": 0}
        members = db.execute(
            "SELECT id FROM users WHERE family_id=?", (user_row["family_id"],)
        ).fetchall()
        member_ids = [m["id"] for m in members]
        if not member_ids:
            return {"total_cost": 0, "total_market_value": 0, "total_profit": 0, "total_profit_pct": 0}
        return _calc_investment_summary(db, member_ids)


@router.get("/summary")
def asset_summary(scope: str = "mine", user=Depends(get_current_user)):
    """资产汇总: scope=mine|family"""
    uid = int(user["sub"])
    with get_db() as db:
        if scope == "family":
            # 获取同家庭所有成员
            user_row = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
            if not user_row or not user_row["family_id"]:
                return {"members": {}, "family": _user_summary(uid, db)}
            members = db.execute(
                "SELECT id, username, display_name FROM users WHERE family_id=?", (user_row["family_id"],)
            ).fetchall()
            members_summary = {}
            family_totals = {"cash": 0, "deposit": 0, "fund": 0, "stock": 0, "bond": 0, "precious_metal": 0,
                           "total_asset": 0, "total_liability": 0, "net_worth": 0}
            for m in members:
                s = _user_summary(m["id"], db)
                members_summary[str(m["id"])] = {"username": m["username"], "display_name": m["display_name"] or "", "summary": s}
                for k in family_totals:
                    family_totals[k] += s[k]
            family_totals = {k: round(v, 2) for k, v in family_totals.items()}
            return {"members": members_summary, "family": family_totals}
        else:
            return _user_summary(uid, db)


@router.get("/detail")
def asset_detail(category: Optional[str] = Query(None, description="分类: cash/deposit/fund/stock/bond, 不传则返回全部"),
                 user=Depends(get_current_user)):
    """返回资产明细，适合 OpenClaw 查询具体持仓"""
    uid = int(user["sub"])
    result = {}

    def _fetch(table, mapper, cat_name):
        with get_db() as db:
            rows = db.execute(f"SELECT * FROM {table} WHERE user_id=? ORDER BY id", (uid,)).fetchall()
        return [mapper(r) for r in rows]

    def _fetch_pm():
        from app.routers.precious_metals import _fetch_user_pm
        return _fetch_user_pm(uid, include_hidden=True)

    if not category or category == "cash":
        result["cash"] = _fetch("asset_cash", _cash_row, "cash")
    if not category or category == "deposit":
        result["deposit"] = _fetch("asset_deposit", _deposit_row, "deposit")
    if not category or category == "fund":
        result["fund"] = _fetch("asset_fund", _fund_row, "fund")
    if not category or category == "stock":
        result["stock"] = _fetch("asset_stock", _stock_row, "stock")
    if not category or category == "bond":
        result["bond"] = _fetch("asset_bond", _bond_row, "bond")
    if not category or category == "precious_metal":
        result["precious_metal"] = _fetch_pm()

    return result


@router.get("/family/trend")
def family_trend(days: int = Query(30, ge=1, le=365), user=Depends(get_current_user)):
    """家庭净值变化趋势：按日期汇总所有家庭成员净资产快照（排除各成员隐藏类别）"""
    from collections import defaultdict
    import json
    from app.routers.networth import take_auto_snapshot_for_all_users

    # 强制刷新今日快照，确保趋势图数据与实时资产一致
    take_auto_snapshot_for_all_users(force=True)

    uid = int(user["sub"])
    with get_db() as db:
        user_row = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
        if not user_row or not user_row["family_id"]:
            return {"dates": [], "values": []}
        members = db.execute(
            "SELECT id FROM users WHERE family_id=?", (user_row["family_id"],)
        ).fetchall()
        if not members:
            return {"dates": [], "values": []}

        # 家庭趋势以 viewer 的 familyHiddenAssets 为准，不使用成员自己的 hiddenAssets
        # （成员个人隐藏只影响自己的 Dashboard 视图，不影响家庭汇总）
        CAT_KEYS = ["cash", "deposit", "fund", "stock", "bond", "precious_metal", "total_liability"]
        member_hidden = {m["id"]: set() for m in members}  # 初始全部为空

        viewer_row = db.execute(
            "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_key='privacy_settings'",
            (uid,)
        ).fetchone()
        if viewer_row:
            try:
                viewer_ps = json.loads(viewer_row["setting_value"])
                family_hidden = viewer_ps.get("familyHiddenAssets", {}) or {}
                for mid_str, cats in family_hidden.items():
                    mid = int(mid_str)
                    if mid in member_hidden:
                        member_hidden[mid] = member_hidden[mid] | set(cats)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        member_ids = [m["id"] for m in members]
        placeholders = ",".join("?" * len(member_ids))

        # 拉取每个成员每条快照的明细（含分类字段），以便排除隐藏类别
        snap_rows = db.execute(
            f"SELECT user_id, snap_date, net_worth, cash, deposit, fund, stock, bond, "
            f"precious_metal, total_liability FROM net_worth_snapshots "
            f"WHERE user_id IN ({placeholders}) ORDER BY snap_date ASC",
            member_ids,
        ).fetchall()

    # 逐条快照：按成员隐藏类别调整 net_worth，再按日期汇总
    daily = defaultdict(float)
    for r in snap_rows:
        mid = r["user_id"]
        hidden = member_hidden.get(mid, set())
        nw = r["net_worth"]
        for cat in CAT_KEYS:
            if cat in hidden:
                if cat == "total_liability":
                    # 净值 = total_asset - total_liability；隐藏负债时应加回
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
