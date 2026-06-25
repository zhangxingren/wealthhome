"""贵金属资产 — 黄金 / 白银 / 铂金 / 钯金"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/precious-metals", tags=["贵金属"])


TYPE_LABELS = {
    "gold": "黄金",
    "silver": "白银",
    "platinum": "铂金",
    "palladium": "钯金",
}


class PreciousMetalIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    type: str = Field(default="gold", pattern="^(gold|silver|platinum|palladium)$")
    weight_grams: float = Field(..., gt=0)
    buy_price_per_gram: float = Field(..., gt=0)
    buy_date: str = Field(..., description="YYYY-MM-DD")
    buy_total: float = Field(default=0, ge=0)
    current_price_per_gram: float = 0
    notes: str = ""


class PreciousMetalOut(PreciousMetalIn):
    id: int
    user_id: int
    is_hidden: bool
    created_at: str
    updated_at: str


def _row(r) -> dict:
    buy_total = r["buy_total"] or (r["weight_grams"] * r["buy_price_per_gram"])
    current_value = r["weight_grams"] * (r["current_price_per_gram"] or 0)
    profit = current_value - buy_total
    profit_pct = (profit / buy_total * 100) if buy_total > 0 else 0
    return {
        "id": r["id"],
        "user_id": r["user_id"],
        "name": r["name"],
        "type": r["type"],
        "type_label": TYPE_LABELS.get(r["type"], r["type"]),
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
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def _fetch_user_pm(uid: int, include_hidden: bool = False):
    """获取用户贵金属列表"""
    with get_db() as db:
        if include_hidden:
            rows = db.execute(
                "SELECT * FROM asset_precious_metal WHERE user_id=? ORDER BY id DESC",
                (uid,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM asset_precious_metal WHERE user_id=? AND is_hidden=0 ORDER BY id DESC",
                (uid,),
            ).fetchall()
    return [_row(r) for r in rows]


# ─── CRUD ──────────────────────────────────────────────

@router.get("")
def list_precious_metals(limit: int = Query(default=100), offset: int = Query(default=0), user=Depends(get_current_user)):
    all_items = _fetch_user_pm(int(user["sub"]))
    return all_items[offset:offset + limit]


@router.post("", status_code=201)
def create_precious_metal(body: PreciousMetalIn, user=Depends(get_current_user)):
    buy_total = body.buy_total if body.buy_total > 0 else round(body.weight_grams * body.buy_price_per_gram, 2)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO asset_precious_metal "
            "(user_id, name, type, weight_grams, buy_price_per_gram, buy_date, buy_total, current_price_per_gram, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                int(user["sub"]),
                body.name,
                body.type,
                body.weight_grams,
                body.buy_price_per_gram,
                body.buy_date,
                buy_total,
                body.current_price_per_gram,
                body.notes,
            ),
        )
        row = db.execute("SELECT * FROM asset_precious_metal WHERE id=?", (cur.lastrowid,)).fetchone()
    return _row(row)


@router.put("/{pm_id}")
def update_precious_metal(pm_id: int, body: PreciousMetalIn, user=Depends(get_current_user)):
    buy_total = body.buy_total if body.buy_total > 0 else round(body.weight_grams * body.buy_price_per_gram, 2)
    with get_db() as db:
        r = db.execute(
            "SELECT id FROM asset_precious_metal WHERE id=? AND user_id=?",
            (pm_id, int(user["sub"])),
        ).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="贵金属资产不存在")
        db.execute(
            "UPDATE asset_precious_metal SET "
            "name=?, type=?, weight_grams=?, buy_price_per_gram=?, buy_date=?, buy_total=?, "
            "current_price_per_gram=?, notes=?, updated_at=datetime('now','localtime') "
            "WHERE id=?",
            (
                body.name,
                body.type,
                body.weight_grams,
                body.buy_price_per_gram,
                body.buy_date,
                buy_total,
                body.current_price_per_gram,
                body.notes,
                pm_id,
            ),
        )
        row = db.execute("SELECT * FROM asset_precious_metal WHERE id=?", (pm_id,)).fetchone()
    return _row(row)


@router.delete("/{pm_id}", status_code=204)
def delete_precious_metal(pm_id: int, user=Depends(get_current_user)):
    """软删除：设置 is_hidden = 1"""
    with get_db() as db:
        r = db.execute(
            "SELECT id FROM asset_precious_metal WHERE id=? AND user_id=?",
            (pm_id, int(user["sub"])),
        ).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="贵金属资产不存在")
        db.execute(
            "UPDATE asset_precious_metal SET is_hidden=1, updated_at=datetime('now','localtime') WHERE id=?",
            (pm_id,),
        )


# ─── 实时价格刷新 ──────────────────────────────────────

@router.post("/refresh")
def refresh_prices(user=Depends(get_current_user)):
    """使用 akshare 获取最新国内金价/银价并刷新所有持仓"""
    uid = int(user["sub"])
    with get_db() as db:
        rows = db.execute(
            "SELECT id, type FROM asset_precious_metal WHERE user_id=? AND is_hidden=0",
            (uid,),
        ).fetchall()
    if not rows:
        return {"message": "无贵金属持仓", "updated": 0}

    # 获取实时价格
    prices = {}
    try:
        import akshare as ak

        # 黄金：上海黄金交易所 Au99.99 最新收盘价（元/克）
        try:
            df_gold = ak.spot_hist_sge(symbol="Au99.99")
            if df_gold is not None and not df_gold.empty:
                prices["gold"] = float(df_gold["close"].iloc[-1])
        except Exception:
            # 备选：上海金基准价
            try:
                df_bench = ak.spot_golden_benchmark_sge()
                if df_bench is not None and not df_bench.empty:
                    row = df_bench.iloc[-1]
                    prices["gold"] = float(row.get("早盘价", row.get("晚盘价", 0)))
            except Exception:
                pass

        # 白银：上海黄金交易所 Ag(T+D) 最新收盘价（元/千克，需除以1000）
        try:
            df_silver = ak.spot_hist_sge(symbol="Ag(T+D)")
            if df_silver is not None and not df_silver.empty:
                raw = float(df_silver["close"].iloc[-1])
                prices["silver"] = round(raw / 1000, 2)  # 元/千克 → 元/克
        except Exception:
            try:
                df_bench = ak.spot_silver_benchmark_sge()
                if df_bench is not None and not df_bench.empty:
                    row = df_bench.iloc[-1]
                    raw = float(row.get("早盘价", row.get("晚盘价", 0)))
                    prices["silver"] = round(raw / 1000, 2)
            except Exception:
                pass

        # 铂金：尝试 Pt99.95
        try:
            df_pt = ak.spot_hist_sge(symbol="Pt99.95")
            if df_pt is not None and not df_pt.empty:
                prices["platinum"] = float(df_pt["close"].iloc[-1])
        except Exception:
            pass

    except ImportError:
        raise HTTPException(status_code=500, detail="akshare 未正确安装，无法获取实时价格")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取实时价格失败: {str(e)}")

    if not prices:
        return {"message": "暂时无法获取贵金属实时价格，请稍后重试", "updated": 0, "prices": {}}

    # 更新数据库
    updated = 0
    with get_db() as db:
        for r in rows:
            p = prices.get(r["type"])
            if p and p > 0:
                db.execute(
                    "UPDATE asset_precious_metal SET current_price_per_gram=?, updated_at=datetime('now','localtime') WHERE id=?",
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
    """贵金属盈亏汇总：总成本、总市值、总盈亏、盈亏百分比"""
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