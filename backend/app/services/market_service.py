"""行情数据服务

统一管理股票、基金、贵金属的行情获取逻辑。
"""

import json
import re
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import requests as req


def guess_exchange(code: str, stored_market: str) -> str:
    """根据股票代码前缀推导交易所后缀"""
    code_clean = code.strip()
    prefix = code_clean[:3]
    if prefix in ('000', '001', '002', '003', '300', '301') or code_clean.startswith(('15', '16')):
        return 'SZ'
    if prefix in ('600', '601', '603', '605', '688'):
        return 'SH'
    if code_clean.startswith(('8', '4')):
        return 'BJ'
    # 港股 / 美股
    mkt = stored_market.upper()
    if mkt == 'HK':
        return 'HK'
    if mkt == 'US':
        return 'US'
    return mkt


def fetch_stock_prices(stocks: List[Tuple[int, str, str]], token: str) -> Tuple[List[Tuple[int, float]], List[str], Dict]:
    """通过 Tushare HTTP API 获取股票最新收盘价，新浪API兜底

    Args:
        stocks: [(id, code, market), ...]
        token: Tushare API token

    Returns:
        (results, failed_codes, debug_info)
        - results: [(id, close_price), ...]
        - failed_codes: 未能获取价格的股票代码列表
        - debug_info: 调试信息
    """
    if not stocks:
        return [], [], {"requested": 0, "fetched": 0, "skipped": 0}

    ts_codes = []
    code_map: Dict[str, int] = {}
    for rid, code, mkt in stocks:
        exchange = guess_exchange(code, mkt)
        ts = code + "." + exchange
        ts_codes.append(ts)
        code_map[ts] = rid

    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    try:
        resp = req.post(
            "https://api.tushare.pro",
            json={
                "api_name": "daily",
                "token": token,
                "params": {
                    "ts_code": ",".join(ts_codes),
                    "start_date": start_date,
                },
                "fields": "ts_code,close,trade_date",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Tushare] 请求失败: {e}", file=sys.stderr)
        return [], [c + "." + guess_exchange(c, m) for _, c, m in stocks], {"error": str(e), "requested": len(stocks), "fetched": 0, "skipped": len(stocks)}

    if data.get("code") != 0:
        msg = data.get("msg", "未知错误")
        print(f"[Tushare] API 错误: {msg}", file=sys.stderr)
        # 所有股票都算 failed，走新浪兜底
        failed = [c + "." + guess_exchange(c, m) for _, c, m in stocks]
        return [], failed, {"error": msg, "requested": len(stocks), "fetched": 0, "skipped": len(stocks)}

    items = data.get("data", {}).get("items", [])
    if not items:
        print(
            f"[Tushare DEBUG] 返回空数据\n"
            f"  codes={ts_codes}\n"
            f"  start_date={start_date}\n"
            f"  resp_code={data.get('code')}, msg={data.get('msg')}\n",
            file=sys.stderr,
        )
        failed = [c + "." + guess_exchange(c, m) for _, c, m in stocks]
        return [], failed, {"requested": len(stocks), "fetched": 0, "skipped": len(stocks)}

    price_map: Dict[str, Tuple[float, str]] = {}
    for row_data in items:
        ts_code = row_data[0]
        close_price = float(row_data[1])
        trade_date = row_data[2]
        if ts_code not in price_map:
            price_map[ts_code] = (close_price, trade_date)
        elif trade_date > price_map[ts_code][1]:
            price_map[ts_code] = (close_price, trade_date)

    result: List[Tuple[int, float]] = []
    failed_codes: List[str] = []
    for ts, rid in code_map.items():
        info = price_map.get(ts)
        if info is None:
            failed_codes.append(ts)
            continue
        price = info[0]
        trade_date = info[1]
        result.append((rid, price))
        print(f"[Tushare] 更新 {ts} 收盘价={price} (交易日期={trade_date})", file=sys.stderr)

    return result, failed_codes, {"requested": len(stocks), "fetched": len(result), "tushare_failed": len(failed_codes)}


def fetch_stock_price_sina(ts_code: str) -> Optional[float]:
    """通过新浪财经API获取单只股票价格（兜底方案）

    Args:
        ts_code: Tushare格式代码, 如 "002594.SZ"

    Returns:
        收盘价(float) 或 None
    """
    try:
        parts = ts_code.split(".")
        if len(parts) != 2:
            return None
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
                    return price
    except Exception:
        pass
    return None


def fetch_fund_nav(code: str) -> Tuple[Optional[float], str]:
    """获取基金最新净值（天天基金 + 东方财富兜底）

    Returns:
        (净值, fund_type) - fund_type 可能为空字符串
    """
    fund_type = ""
    # 天天基金
    try:
        resp = req.get(
            f"https://fundgz.1234567.com.cn/js/{code}.js",
            headers={"Referer": "https://fund.eastmoney.com/"},
            timeout=8,
        )
        if resp.status_code == 200:
            text = resp.text
            if text.startswith("jsonpgz("):
                data = json.loads(text[8:-2])
                fund_type = data.get("fundtype", "")
                gztime = data.get("gztime", "")
                nav = data.get("dwjz") or data.get("gsz")
                if nav:
                    return (float(nav), fund_type)
    except Exception:
        pass

    # 东方财富兜底 (lsjz API，更可靠)
    try:
        nav_url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=1"
        nav_resp = req.get(
            nav_url,
            headers={"Referer": "https://fund.eastmoney.com/"},
            timeout=10,
        )
        if nav_resp.status_code == 200:
            nav_data = nav_resp.json()
            items = nav_data.get("Data", {}).get("LSJZList", [])
            if items:
                dwjz_val = float(items[0].get("DWJZ", 0))
                if dwjz_val > 0:
                    return (dwjz_val, fund_type)
    except Exception:
        pass

    # 最终兜底：pingzhongdata.js
    try:
        resp = req.get(
            f"https://fund.eastmoney.com/pingzhongdata/{code}.js",
            timeout=8,
        )
        if resp.status_code == 200:
            match = re.search(r'Data_netWorthTrend\s*=\s*(\[.*?\])', resp.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                if data:
                    return (float(data[-1].get("y", 0)), fund_type)
    except Exception:
        pass

    return (None, fund_type)


def fetch_precious_metal_price(metal_type: str = "gold") -> Optional[float]:
    """获取贵金属最新价格（人民币/克）

    支持类型: gold(黄金), silver(白银), platinum(铂金)
    """
    try:
        import akshare as ak

        if metal_type == "gold":
            # 黄金：上海黄金交易所 Au99.99 最新收盘价（元/克）
            try:
                df = ak.spot_hist_sge(symbol="Au99.99")
                if df is not None and not df.empty:
                    return float(df["close"].iloc[-1])
            except Exception:
                pass
            # 备选：上海金基准价
            try:
                df_bench = ak.spot_golden_benchmark_sge()
                if df_bench is not None and not df_bench.empty:
                    row = df_bench.iloc[-1]
                    val = float(row.get("早盘价", row.get("晚盘价", 0)))
                    if val > 0:
                        return val
            except Exception:
                pass

        elif metal_type == "silver":
            # 白银：Ag(T+D) 最新收盘价（元/千克，需除以1000）
            try:
                df = ak.spot_hist_sge(symbol="Ag(T+D)")
                if df is not None and not df.empty:
                    raw = float(df["close"].iloc[-1])
                    return round(raw / 1000, 2)  # 元/千克 -> 元/克
            except Exception:
                pass
            # 备选：上海银基准价
            try:
                df_bench = ak.spot_silver_benchmark_sge()
                if df_bench is not None and not df_bench.empty:
                    row = df_bench.iloc[-1]
                    raw = float(row.get("早盘价", row.get("晚盘价", 0)))
                    if raw > 0:
                        return round(raw / 1000, 2)
            except Exception:
                pass

        elif metal_type == "platinum":
            # 铂金：Pt99.95
            try:
                df = ak.spot_hist_sge(symbol="Pt99.95")
                if df is not None and not df.empty:
                    return float(df["close"].iloc[-1])
            except Exception:
                pass

    except ImportError:
        pass
    except Exception:
        pass

    return None
