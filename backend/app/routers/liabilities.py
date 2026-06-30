"""负债管理 — 等额本息 / 等额本金 + 还款计划表

分层架构：Router → Repository → Database
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user
from app.models.assets import LiabilityCreate, LiabilityUpdate
from app.repositories.asset_repo import (
    create_asset, get_by_id, list_by_user,
    update_asset, delete_asset, exists,
    raw_query_one, raw_execute,
)

TABLE = "liabilities"

router = APIRouter(prefix="/api/liabilities", tags=["负债"])


# ─── 还款计算逻辑 ──────────────────────────────────────

def _calc_equal_installment(principal: float, annual_rate: float, months: int):
    """等额本息：返回 (月供, 总利息, 还款计划列表)"""
    mr = annual_rate / 100 / 12
    if mr == 0:
        mp = principal / months
        return round(mp, 2), 0, _equal_principal_plan(principal, annual_rate, months)
    mp = principal * mr * (1 + mr) ** months / ((1 + mr) ** months - 1)
    mp = round(mp, 2)
    total_interest = round(mp * months - principal, 2)
    plan = []
    remaining = principal
    for i in range(1, months + 1):
        interest = round(remaining * mr, 2)
        pay_principal = round(mp - interest, 2)
        remaining = round(remaining - pay_principal, 2)
        if i == months:
            pay_principal += remaining
            remaining = 0
        plan.append({"期数": i, "月供": mp, "本金": pay_principal, "利息": interest, "剩余本金": remaining})
    return mp, total_interest, plan


def _equal_principal_plan(principal: float, annual_rate: float, months: int):
    """等额本金还款计划"""
    mr = annual_rate / 100 / 12
    monthly_principal = round(principal / months, 2)
    plan = []
    remaining = principal
    for i in range(1, months + 1):
        interest = round(remaining * mr, 2)
        mp = round(monthly_principal + interest, 2)
        remaining = round(remaining - monthly_principal, 2)
        if i == months:
            mp += remaining
            remaining = 0
        plan.append({"期数": i, "月供": mp, "本金": monthly_principal, "利息": interest, "剩余本金": remaining})
    return plan


def _calc_equal_principal(principal: float, annual_rate: float, months: int):
    """等额本金：返回 (首月月供, 总利息, 还款计划列表)"""
    plan = _equal_principal_plan(principal, annual_rate, months)
    total_interest = round(sum(item["利息"] for item in plan), 2)
    return plan[0]["月供"], total_interest, plan


def _calc_monthly(body) -> tuple:
    """根据还款方式计算月供和总利息"""
    if body.repay_type == "等额本息":
        return _calc_equal_installment(body.principal, body.rate, body.term_months)[:2]
    else:
        return _calc_equal_principal(body.principal, body.rate, body.term_months)[:2]


def _row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"],
            "principal": r["principal"], "rate": r["rate"],
            "term_months": r["term_months"], "repay_type": r["repay_type"],
            "start_date": r["start_date"], "monthly_payment": r["monthly_payment"],
            "remaining": r["remaining"], "note": r["note"], "created_at": r["created_at"]}


# ─── CRUD 端点 ─────────────────────────────────────────

@router.get("")
def list_liabilities(limit: int = Query(default=100), offset: int = Query(default=0),
                     user=Depends(get_current_user)):
    items = list_by_user(TABLE, int(user["sub"]), limit, offset)
    return [_row(r) for r in items]


@router.post("", status_code=201)
def create_liability(body: LiabilityCreate, user=Depends(get_current_user)):
    monthly, total_interest = _calc_monthly(body)
    data = {
        "user_id": int(user["sub"]),
        "name": body.name, "principal": body.principal, "rate": body.rate,
        "term_months": body.term_months, "repay_type": body.repay_type,
        "start_date": body.start_date, "monthly_payment": monthly,
        "remaining": body.principal, "note": body.note or "",
    }
    new_id = create_asset(TABLE, data)
    row = get_by_id(TABLE, new_id)
    result = _row(row)
    result["total_interest"] = total_interest
    return result


@router.put("/{liability_id}")
def update_liability(liability_id: int, body: LiabilityCreate, user=Depends(get_current_user)):
    uid = int(user["sub"])
    if not exists(TABLE, liability_id, uid):
        raise HTTPException(status_code=404, detail="负债不存在")

    monthly, _ = _calc_monthly(body)
    data = {
        "name": body.name, "principal": body.principal, "rate": body.rate,
        "term_months": body.term_months, "repay_type": body.repay_type,
        "start_date": body.start_date, "monthly_payment": monthly,
        "note": body.note or "",
    }
    update_asset(TABLE, liability_id, uid, data)
    row = get_by_id(TABLE, liability_id)
    return _row(row)


@router.delete("/{liability_id}", status_code=204)
def delete_liability(liability_id: int, user=Depends(get_current_user)):
    if not delete_asset(TABLE, liability_id, int(user["sub"])):
        raise HTTPException(status_code=404, detail="负债不存在")


@router.get("/{liability_id}/plan")
def repayment_plan(liability_id: int, user=Depends(get_current_user)):
    """生成还款计划表（含每期日期）"""
    uid = int(user["sub"])
    data = get_by_id(TABLE, liability_id, uid)
    if not data:
        raise HTTPException(status_code=404, detail="负债不存在")

    if data["repay_type"] == "等额本息":
        _, total_interest, plan = _calc_equal_installment(data["principal"], data["rate"], data["term_months"])
    else:
        _, total_interest, plan = _calc_equal_principal(data["principal"], data["rate"], data["term_months"])

    start = datetime.strptime(data["start_date"], "%Y-%m-%d")
    for i, item in enumerate(plan):
        item["还款日期"] = (start + relativedelta(months=i)).strftime("%Y-%m-%d")

    return {
        "liability": {"id": data["id"], "name": data["name"], "principal": data["principal"],
                      "rate": data["rate"], "term_months": data["term_months"],
                      "repay_type": data["repay_type"], "monthly_payment": data["monthly_payment"]},
        "total_interest": total_interest,
        "plan": plan,
    }


@router.put("/{liability_id}/remaining")
def update_remaining(liability_id: int, remaining: float = Query(..., ge=0),
                     user=Depends(get_current_user)):
    uid = int(user["sub"])
    if not exists(TABLE, liability_id, uid):
        raise HTTPException(status_code=404, detail="负债不存在")
    raw_execute("UPDATE liabilities SET remaining=? WHERE id=?", (remaining, liability_id))
    return {"id": liability_id, "remaining": remaining}
