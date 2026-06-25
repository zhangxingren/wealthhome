"""负债管理 — 等额本息 / 等额本金 + 还款计划表"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/liabilities", tags=["负债"])


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


class LiabilityIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    principal: float = Field(..., gt=0, le=1e12)
    rate: float = Field(..., ge=0, le=100)
    term_months: int = Field(..., gt=0)
    repay_type: str = Field(default="等额本息", pattern="^(等额本息|等额本金)$")
    start_date: str = Field(..., description="YYYY-MM-DD")
    note: str = ""


def _row(r) -> dict:
    return {"id": r["id"], "user_id": r["user_id"], "name": r["name"], "principal": r["principal"],
            "rate": r["rate"], "term_months": r["term_months"], "repay_type": r["repay_type"],
            "start_date": r["start_date"], "monthly_payment": r["monthly_payment"],
            "remaining": r["remaining"], "note": r["note"], "created_at": r["created_at"]}


@router.get("")
def list_liabilities(limit: int = Query(default=100), offset: int = Query(default=0), user=Depends(get_current_user)):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM liabilities WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (int(user["sub"]), limit, offset),
        ).fetchall()
    return [_row(r) for r in rows]


@router.post("", status_code=201)
def create_liability(body: LiabilityIn, user=Depends(get_current_user)):
    if body.repay_type == "等额本息":
        monthly, total_interest, _ = _calc_equal_installment(body.principal, body.rate, body.term_months)
    else:
        monthly, total_interest, _ = _calc_equal_principal(body.principal, body.rate, body.term_months)

    with get_db() as db:
        cur = db.execute(
            "INSERT INTO liabilities (user_id,name,principal,rate,term_months,repay_type,start_date,monthly_payment,remaining,note) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (int(user["sub"]), body.name, body.principal, body.rate, body.term_months,
             body.repay_type, body.start_date, monthly, body.principal, body.note))
        row = db.execute("SELECT * FROM liabilities WHERE id=?", (cur.lastrowid,)).fetchone()
    result = _row(row)
    result["total_interest"] = total_interest
    return result


@router.put("/{liability_id}")
def update_liability(liability_id: int, body: LiabilityIn, user=Depends(get_current_user)):
    with get_db() as db:
        r = db.execute("SELECT id FROM liabilities WHERE id=? AND user_id=?", (liability_id, int(user["sub"]))).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="负债不存在")
        if body.repay_type == "等额本息":
            monthly, _, _ = _calc_equal_installment(body.principal, body.rate, body.term_months)
        else:
            monthly, _, _ = _calc_equal_principal(body.principal, body.rate, body.term_months)
        db.execute(
            "UPDATE liabilities SET name=?,principal=?,rate=?,term_months=?,repay_type=?,start_date=?,monthly_payment=?,note=? WHERE id=?",
            (body.name, body.principal, body.rate, body.term_months, body.repay_type,
             body.start_date, monthly, body.note, liability_id))
        row = db.execute("SELECT * FROM liabilities WHERE id=?", (liability_id,)).fetchone()
    return _row(row)


@router.delete("/{liability_id}", status_code=204)
def delete_liability(liability_id: int, user=Depends(get_current_user)):
    with get_db() as db:
        r = db.execute("DELETE FROM liabilities WHERE id=? AND user_id=?", (liability_id, int(user["sub"])))
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="负债不存在")


@router.get("/{liability_id}/plan")
def repayment_plan(liability_id: int, user=Depends(get_current_user)):
    """生成还款计划表（含每期日期）"""
    with get_db() as db:
        r = db.execute("SELECT * FROM liabilities WHERE id=? AND user_id=?", (liability_id, int(user["sub"]))).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="负债不存在")

    info = dict(r)
    if info["repay_type"] == "等额本息":
        _, total_interest, plan = _calc_equal_installment(info["principal"], info["rate"], info["term_months"])
    else:
        _, total_interest, plan = _calc_equal_principal(info["principal"], info["rate"], info["term_months"])

    # 补充每期还款日期
    start = datetime.strptime(info["start_date"], "%Y-%m-%d")
    for i, item in enumerate(plan):
        item["还款日期"] = (start + relativedelta(months=i)).strftime("%Y-%m-%d")

    return {
        "liability": {"id": info["id"], "name": info["name"], "principal": info["principal"],
                      "rate": info["rate"], "term_months": info["term_months"],
                      "repay_type": info["repay_type"], "monthly_payment": info["monthly_payment"]},
        "total_interest": total_interest,
        "plan": plan,
    }


@router.put("/{liability_id}/remaining")
def update_remaining(liability_id: int, remaining: float = Query(..., ge=0), user=Depends(get_current_user)):
    """手动更新剩余本金（提前还款等场景）"""
    with get_db() as db:
        r = db.execute("SELECT id FROM liabilities WHERE id=? AND user_id=?", (liability_id, int(user["sub"]))).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="负债不存在")
        db.execute("UPDATE liabilities SET remaining=? WHERE id=?", (remaining, liability_id))
    return {"id": liability_id, "remaining": remaining}
