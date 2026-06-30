<p align="center">
  <h1 align="center">🏠 WealthHome</h1>
  <p align="center"><strong>个人与家庭财务一站式管理平台</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/vue-3.x-brightgreen?logo=vuedotjs" alt="Vue">
  <img src="https://img.shields.io/badge/fastapi-0.115+-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## ✨ 为什么用 WealthHome？

市面上的记账 App 要么太简单（只管收支），要么太复杂（企业级 ERP）。WealthHome 瞄准的是**家庭资产净值管理**这个细分场景——你知道自己有多少钱，但你知道你的**净资产**是多少吗？

- 📊 **不只是记账**：跟踪资产市值变化，知道你的钱在增值还是缩水
- 🔒 **数据完全私有**：跑在你自己的 NAS 上，不经过任何第三方
- 👨‍👩‍👧 **家庭协作**：夫妻共享资产视图，各自管理隐私
- 🆓 **完全免费**：MIT 开源，没有订阅，没有广告

## 🎯 核心功能

### 资产管理

| 资产类型 | 记录内容 | 行情更新 |
|---------|---------|---------|
| 💵 现金/活期 | 账户名、币种、余额 | — |
| 🏦 定期存款 | 本金、利率、到期日 | — |
| 📈 基金 | 基金代码、份额、成本净值、当前净值 | ✅ akshare |
| 📊 股票 | 代码、持股数、成本价、市价 | ✅ Tushare |
| 🏛️ 债券 | 发行人、面值、票面利率、到期日 | — |
| 🥇 贵金属 | 类型(金/银/铂/钯)、克重、买入价、当前价 | ✅ akshare |
| 💳 负债 | 贷款/信用卡，本金、利率、还款方式 | — |

### 净值追踪

- 一键记录净值快照，自动汇总各类资产
- ECharts 趋势图，直观看到财富增长曲线
- 按时间范围筛选（7天/30天/90天/自定义）

### 家庭模式

- 邀请码加入家庭组，夫妻共同管理
- 家庭总资产仪表盘，一目了然
- **隐私控制**：按成员、按类别独立设置隐藏，各自数据互不干扰

### 更多

- 🔐 JWT 登录认证，PBKDF2-SHA256 密码哈希
- 📥 数据导出：Excel（按类别分 Sheet）/ CSV / JSON
- 🌐 全局时间范围选择器，所有页面联动
- 👁️ 一键切换隐私模式，金额显示为 `***`
- 📱 响应式布局，手机/平板/PC 均可使用

---

## 🚀 快速开始

### 前置要求

- Docker 20.10+ & Docker Compose 2.0+
- 或 Python 3.12+ & Node.js 18+（本地开发）

### Docker 部署（推荐）

```bash
# 克隆
git clone https://github.com/zhangxingren/wealthhome.git
cd wealthhome

# 启动（首次自动构建镜像 + 初始化数据库）
docker compose up -d

# 访问：http://localhost:8000
```

### 环境变量

在 `docker-compose.yml` 或 `.env` 中配置：

| 变量 | 必填 | 说明 | 示例 |
|------|:--:|------|------|
| `JWT_SECRET` | ✅ | JWT 签名密钥 | `openssl rand -hex 32` |
| `DB_PATH` | — | 数据库路径 | `/app/data/wealthhome.db` |
| `TUSHARE_TOKEN` | — | Tushare Token（股票行情） | 注册 https://tushare.pro |
| `MARKET_REFRESH_INTERVAL` | — | 行情自动刷新间隔(分钟) | `60` |

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API 文档 → http://localhost:8000/docs

# 前端
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 📂 项目架构

```
wealthhome/
├── backend/app/
│   ├── core/             # 基础设施（config, database, auth）
│   ├── models/           # Pydantic 数据模型
│   ├── repositories/     # 数据访问层（通用 CRUD + 表名白名单）
│   ├── services/         # 业务逻辑层 + 行情服务
│   ├── utils/            # 统一 API 响应格式
│   └── routers/          # API 路由（assets, networth, family...）
├── frontend/src/
│   ├── views/            # 页面组件（Dashboard, NetWorth, 各资产页）
│   ├── components/       # 共享组件（InvestSummaryCard, TrendChart…）
│   ├── composables/      # 组合式函数（金额格式化, 隐私控制）
│   ├── stores/           # Pinia 状态管理（时间范围）
│   └── api/              # Axios 请求封装
├── Dockerfile
├── docker-compose.yml
└── deploy.sh             # 一键部署脚本
```

**后端架构**：Router → Service → Repository → Database 四层分离  
**前端架构**：v-for 驱动卡片 + 共享组件 + Pinia 状态管理

---

## 📊 数据库

SQLite 单文件数据库，共 10 张核心表：

| 表名 | 用途 |
|------|------|
| `families` | 家庭组 |
| `users` | 用户（关联 family） |
| `asset_cash` | 现金资产 |
| `asset_deposit` | 定期存款 |
| `asset_fund` | 基金持仓 |
| `asset_stock` | 股票持仓 |
| `asset_bond` | 债券 |
| `asset_precious_metal` | 贵金属 |
| `liabilities` | 负债 |
| `net_worth_snapshots` | 净值快照 |
| `user_settings` | 用户偏好 |

---

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI + uvicorn |
| **数据库** | SQLite（aiosqlite 异步驱动） |
| **认证** | JWT + PBKDF2-SHA256 |
| **前端框架** | Vue 3 + Vite |
| **UI 组件** | Element Plus |
| **图表** | ECharts 5 |
| **状态管理** | Pinia |
| **行情数据** | akshare（基金/贵金属）+ Tushare（股票） |
| **部署** | Docker 多阶段构建 + Docker Compose |

---

## 📸 截图

> 部署后访问 `http://your-nas-ip:8000`

| 仪表盘 | 资产管理 |
|--------|---------|
| 家庭总资产卡片 + 成员卡片 + 净值趋势 | 表格管理 + 隐私隐藏 + 数据导出 |

---

## 🗺️ 路线图

- [x] 多资产类型管理
- [x] 净值快照 + 趋势图
- [x] 家庭协作模式
- [x] 隐私隐藏
- [x] 行情自动刷新
- [x] 数据导出 (Excel/CSV/JSON)
- [x] Docker 部署
- [ ] 首次启动自动种子管理员
- [ ] 手机端 PWA 支持
- [ ] 定期存款到期提醒
- [ ] 更多行情数据源

---

## 🤝 贡献

欢迎提 Issue 和 PR！MIT License，随意 Fork。

---

## 📄 License

[MIT](LICENSE) © 2026 zhangxingren
