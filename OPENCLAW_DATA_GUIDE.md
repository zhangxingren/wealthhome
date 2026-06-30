# 告诉 OpenClaw 的操作指南

> 把下面这段发给 OpenClaw，然后告诉它你具体做了什么操作，它就能帮你更新资产数据。

---

## 数据库位置

数据库在 NAS Docker 容器内：

```
NAS: 100.65.88.19
SSH: xingren / zheshi122mima
容器: wealthhome
数据库: /app/data/wealthhome.db
```

操作数据库的命令格式：
```bash
docker exec wealthhome python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/wealthhome.db')
# ... 你的 SQL 语句 ...
conn.commit()
conn.close()
"
```

---

## 用户信息

| user_id | 用户名 | 角色 |
|---------|--------|------|
| 2 | xingren | admin |
| 3 | zhuzhu | user |

两个用户都属于 family_id=2。

---

## 各资产表结构

### 1. 现金 / 活期（asset_cash）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| name | 账户名 | 工资卡 |
| currency | 币种 | CNY |
| amount | 余额 | 50000.00 |
| account_name | 银行/平台 | 招商银行 |
| note | 备注 | — |

添加现金：
```sql
INSERT INTO asset_cash (user_id, name, currency, amount, account_name)
VALUES (2, '工资卡', 'CNY', 50000.00, '招商银行');
```

修改余额：
```sql
UPDATE asset_cash SET amount = 52000.00, updated_at = datetime('now','localtime')
WHERE id = 1 AND user_id = 2;
```

---

### 2. 定期存款（asset_deposit）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| name | 存款名称 | 一年定存 |
| bank | 银行 | 工商银行 |
| principal | 本金 | 100000.00 |
| rate | 年利率(%) | 2.5 |
| start_date | 起存日期 | 2025-01-01 |
| end_date | 到期日期 | 2026-01-01 |

添加存款：
```sql
INSERT INTO asset_deposit (user_id, name, bank, principal, rate, start_date, end_date)
VALUES (2, '一年定存', '工商银行', 100000.00, 2.5, '2025-01-01', '2026-01-01');
```

---

### 3. 基金（asset_fund）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| code | 基金代码 | 000001 |
| name | 基金名称 | 华夏成长混合 |
| shares | 持有份额 | 1000.00 |
| cost_nav | 成本净值 | 1.5000 |
| current_nav | 当前净值 | 1.6500 |
| fund_type | 类型 | 混合型 |

添加基金：
```sql
INSERT INTO asset_fund (user_id, code, name, shares, cost_nav, current_nav, fund_type)
VALUES (2, '000001', '华夏成长混合', 1000.00, 1.5000, 1.6500, '混合型');
```

修改份额（加仓/减仓）：
```sql
UPDATE asset_fund
SET shares = 1500.00, cost_nav = 1.5500, updated_at = datetime('now','localtime')
WHERE id = 1 AND user_id = 2;
```

---

### 4. 股票（asset_stock）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| code | 股票代码 | 600519 |
| name | 股票名称 | 贵州茅台 |
| shares | 持股数 | 100 |
| cost_price | 成本价 | 1600.00 |
| current_price | 当前价 | 1680.00 |
| market | 市场 | sh(沪) / sz(深) / hk(港) / us(美) |

添加股票：
```sql
INSERT INTO asset_stock (user_id, code, name, shares, cost_price, current_price, market)
VALUES (2, '600519', '贵州茅台', 100, 1600.00, 1680.00, 'sh');
```

修改持股：
```sql
UPDATE asset_stock
SET shares = 150, cost_price = 1620.00, current_price = 1680.00, updated_at = datetime('now','localtime')
WHERE id = 1 AND user_id = 2;
```

---

### 5. 债券（asset_bond）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| name | 名称 | 国债2025 |
| issuer | 发行方 | 财政部 |
| face_value | 面值 | 100.00 |
| rate | 票面利率(%) | 3.0 |
| maturity_date | 到期日 | 2028-01-01 |
| quantity | 数量 | 100 |
| cost_price | 买入价 | 98.00 |
| current_price | 当前价 | 99.50 |

添加债券：
```sql
INSERT INTO asset_bond (user_id, name, issuer, face_value, rate, maturity_date, quantity, cost_price, current_price)
VALUES (2, '国债2025', '财政部', 100.00, 3.0, '2028-01-01', 100, 98.00, 99.50);
```

---

### 6. 贵金属（asset_precious_metal）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| name | 名称 | 金条 |
| type | 类型 | gold / silver / platinum / palladium |
| weight_grams | 克重 | 50.00 |
| buy_price_per_gram | 买入单价(元/克) | 480.00 |
| buy_date | 购买日期 | 2025-03-15 |
| buy_total | 买入总价 | 24000.00 |
| current_price_per_gram | 当前单价 | 520.00 |

添加贵金属：
```sql
INSERT INTO asset_precious_metal (user_id, name, type, weight_grams, buy_price_per_gram, buy_date, buy_total, current_price_per_gram)
VALUES (2, '金条', 'gold', 50.00, 480.00, '2025-03-15', 24000.00, 520.00);
```

---

### 7. 负债（liabilities）

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 用户 ID | 2 |
| name | 负债名称 | 房贷 |
| principal | 本金 | 1000000.00 |
| rate | 年利率(%) | 4.5 |
| term_months | 期限(月) | 360 |
| repay_type | 还款方式 | 等额本息 / 等额本金 |
| start_date | 开始日期 | 2020-01-01 |
| monthly_payment | 月供 | 5066.00 |
| remaining | 剩余本金 | 850000.00 |

添加负债：
```sql
INSERT INTO liabilities (user_id, name, principal, rate, term_months, repay_type, start_date, monthly_payment, remaining)
VALUES (2, '房贷', 1000000.00, 4.5, 360, '等额本息', '2020-01-01', 5066.00, 850000.00);
```

---

## 净值快照

在修改资产数据后，建议记录一条净值快照：

```sql
INSERT INTO net_worth_snapshots (user_id, snap_date, total_asset, total_debt, net_worth,
    cash, deposit, fund, stock, bond, precious_metal, total_liability)
VALUES (2, date('now','localtime'),
    -- 下面填实际汇总值
    500000, 850000, -350000,
    50000, 100000, 50000, 168000, 9950, 26000, 850000);
```

---

## 常用操作示例

### “我卖掉了某只股票”
```sql
DELETE FROM asset_stock WHERE id = X AND user_id = 2;
```

### “我取出了某笔定期存款”
```sql
DELETE FROM asset_deposit WHERE id = X AND user_id = 2;
```

### “我赎回了某只基金”
```sql
DELETE FROM asset_fund WHERE id = X AND user_id = 2;
```

### “我修改了现金余额”
```sql
UPDATE asset_cash SET amount = 新余额, updated_at = datetime('now','localtime')
WHERE id = X AND user_id = 2;
```

---

## 重要提醒

1. **所有 SQL 都要加 `user_id` 条件**——xingren=2，zhuzhu=3
2. **修改完记得 `conn.commit()`**——否则数据不会保存
3. **修改数据后建议记录净值快照**——这样才能在趋势图上看到变化
4. **NAS 上的数据库路径**：容器内 `/app/data/wealthhome.db`，宿主机 `/vol1/1000/Docker/home-money/wealthhome/_data/wealthhome.db`
