"""资产相关 Pydantic 模型"""

from typing import Optional
from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    """资产基础字段"""
    name: str
    note: Optional[str] = ""
    tags: Optional[str] = ""


class CashCreate(AssetBase):
    currency: str = "CNY"
    amount: float = 0
    account_name: Optional[str] = ""


class CashUpdate(CashCreate):
    pass


class DepositCreate(AssetBase):
    bank: Optional[str] = ""
    principal: float = 0
    rate: float = 0
    start_date: str
    end_date: str
    currency: str = "CNY"


class DepositUpdate(DepositCreate):
    pass


class FundCreate(AssetBase):
    code: str
    shares: float = 0
    cost_nav: float = 0
    current_nav: Optional[float] = 0
    fund_type: Optional[str] = ""


class FundUpdate(FundCreate):
    pass


class StockCreate(AssetBase):
    code: str
    shares: float = 0
    cost_price: float = 0
    current_price: Optional[float] = 0
    market: str = "sh"


class StockUpdate(StockCreate):
    pass


class BondCreate(AssetBase):
    issuer: Optional[str] = ""
    face_value: float = 0
    rate: float = 0
    maturity_date: str
    currency: str = "CNY"
    quantity: float = 1
    cost_price: float = 0
    current_price: float = 0


class BondUpdate(BondCreate):
    pass


class PreciousMetalCreate(AssetBase):
    name: str
    type: str = "gold"
    weight_grams: float = 0
    buy_price_per_gram: float = 0
    buy_date: str
    buy_total: float = 0
    current_price_per_gram: Optional[float] = 0
    notes: Optional[str] = ""
    is_hidden: int = 0


class PreciousMetalUpdate(PreciousMetalCreate):
    pass


class LiabilityCreate(AssetBase):
    name: str
    principal: float = 0
    rate: float = 0
    term_months: int = 0
    repay_type: str = "等额本息"
    start_date: str
    monthly_payment: Optional[float] = 0
    remaining: Optional[float] = 0


class LiabilityUpdate(LiabilityCreate):
    pass
