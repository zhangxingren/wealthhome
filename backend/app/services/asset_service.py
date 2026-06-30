"""资产汇总 & 投资盈亏服务"""

from typing import Dict, Optional
from app.core.database import get_db

# 债券估值 SQL
_BOND_VAL = (
    "COALESCE(SUM(quantity * COALESCE(NULLIF(current_price,0), "
    "NULLIF(cost_price,0), face_value)),0)"
)


def calc_user_summary(user_id: int, db=None) -> Dict:
    """计算用户资产汇总"""
    own_db = db is None

    def _do(db):
        def _sum(query, *params):
            return float(db.execute(query, params).fetchone()[0] or 0)

        cash = _sum("SELECT COALESCE(SUM(amount),0) FROM asset_cash WHERE user_id=?", user_id)
        deposit = _sum("SELECT COALESCE(SUM(principal),0) FROM asset_deposit WHERE user_id=?", user_id)
        fund = _sum("SELECT COALESCE(SUM(shares*current_nav),0) FROM asset_fund WHERE user_id=?", user_id)
        stock = _sum("SELECT COALESCE(SUM(shares*current_price),0) FROM asset_stock WHERE user_id=?", user_id)
        bond = _sum(f"SELECT {_BOND_VAL} FROM asset_bond WHERE user_id=?", user_id)
        pm = _sum(
            "SELECT COALESCE(SUM(weight_grams * COALESCE(current_price_per_gram, buy_price_per_gram)), 0) "
            "FROM asset_precious_metal WHERE user_id=? AND is_hidden=0", user_id
        )
        debt = _sum("SELECT COALESCE(SUM(remaining),0) FROM liabilities WHERE user_id=?", user_id)

        total_asset = cash + deposit + fund + stock + bond + pm
        return {
            "cash": round(cash, 2),
            "deposit": round(deposit, 2),
            "fund": round(fund, 2),
            "stock": round(stock, 2),
            "bond": round(bond, 2),
            "precious_metal": round(pm, 2),
            "total_asset": round(total_asset, 2),
            "total_liability": round(debt, 2),
            "net_worth": round(total_asset - debt, 2),
        }

    if own_db:
        with get_db() as db:
            return _do(db)
    return _do(db)


def calc_investment_summary(user_id: int) -> Dict:
    """投资盈亏汇总"""
    with get_db() as db:
        stocks = db.execute(
            "SELECT shares, cost_price, current_price FROM asset_stock WHERE user_id=?",
            (user_id,)
        ).fetchall()
        funds = db.execute(
            "SELECT shares, cost_nav, current_nav FROM asset_fund WHERE user_id=?",
            (user_id,)
        ).fetchall()
        bonds = db.execute(
            "SELECT quantity, cost_price, COALESCE(NULLIF(current_price,0), face_value) as cur_price "
            "FROM asset_bond WHERE user_id=?",
            (user_id,)
        ).fetchall()

    stock_cost = sum(r["shares"] * (r["cost_price"] or 0) for r in stocks)
    stock_market = sum(r["shares"] * (r["current_price"] or 0) for r in stocks)
    stock_profit = stock_market - stock_cost

    fund_cost = sum(r["shares"] * (r["cost_nav"] or 0) for r in funds)
    fund_market = sum(r["shares"] * (r["current_nav"] or 0) for r in funds)
    fund_profit = fund_market - fund_cost

    bond_cost = sum(r["quantity"] * (r["cost_price"] or 0) for r in bonds)
    bond_market = sum(r["quantity"] * (r["cur_price"] or 0) for r in bonds)
    bond_profit = bond_market - bond_cost

    total_cost = stock_cost + fund_cost + bond_cost
    total_market = stock_market + fund_market + bond_market
    total_profit = stock_profit + fund_profit + bond_profit

    return {
        "stock": round(stock_profit, 2),
        "fund": round(fund_profit, 2),
        "bond": round(bond_profit, 2),
        "total": round(total_profit, 2),
        "total_cost": round(total_cost, 2),
        "total_market_value": round(total_market, 2),
        "total_profit": round(total_profit, 2),
        "total_profit_pct": round(total_profit / total_cost * 100, 2) if total_cost > 0 else 0,
    }


def calc_family_summary(family_id: int, db=None) -> Dict:
    """计算家庭资产汇总"""
    own_db = db is None

    def _do(db):
        users = db.execute(
            "SELECT id FROM users WHERE family_id=?", (family_id,)
        ).fetchall()
        member_ids = [u["id"] for u in users]
        if not member_ids:
            return {"member_count": 0, "members": [], "summary": calc_empty_summary()}

        member_summaries = []
        total = calc_empty_summary()
        for uid in member_ids:
            s = calc_user_summary(uid, db)
            member_summaries.append({"user_id": uid, "summary": s})
            for key in total:
                total[key] += s[key]

        return {
            "member_count": len(member_ids),
            "members": member_summaries,
            "summary": {k: round(v, 2) for k, v in total.items()},
        }

    if own_db:
        with get_db() as db:
            return _do(db)
    return _do(db)


def calc_empty_summary() -> Dict:
    return {
        "cash": 0, "deposit": 0, "fund": 0, "stock": 0,
        "bond": 0, "precious_metal": 0,
        "total_asset": 0, "total_liability": 0, "net_worth": 0,
    }


def get_asset_detail(user_id: int) -> Dict:
    """获取所有资产明细列表"""
    with get_db() as db:
        cash = [dict(r) for r in db.execute(
            "SELECT id, name, amount, currency, account_name, note FROM asset_cash WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

        deposit = [dict(r) for r in db.execute(
            "SELECT id, name, bank, principal, rate, start_date, end_date, currency, note FROM asset_deposit WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

        fund = [dict(r) for r in db.execute(
            "SELECT id, code, name, shares, cost_nav, current_nav, fund_type, note FROM asset_fund WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

        stock = [dict(r) for r in db.execute(
            "SELECT id, code, name, shares, cost_price, current_price, market, note FROM asset_stock WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

        bond = [dict(r) for r in db.execute(
            "SELECT id, name, issuer, face_value, rate, maturity_date, currency, quantity, cost_price, current_price, note FROM asset_bond WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

        pm = [dict(r) for r in db.execute(
            "SELECT id, name, type, weight_grams, buy_price_per_gram, buy_date, buy_total, current_price_per_gram, notes FROM asset_precious_metal WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()]

    return {"cash": cash, "deposit": deposit, "fund": fund, "stock": stock, "bond": bond, "precious_metal": pm}
