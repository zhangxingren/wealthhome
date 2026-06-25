<p align="center">
  <h1 align="center">WealthHome</h1>
  <p align="center"><strong>个人与家庭财务一站式管理平台</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.x-brightgreen" alt="Vue">
  <img src="https://img.shields.io/badge/docker-ready-blue" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 项目简介

WealthHome 是一款自托管（Self-Hosted）的家庭资产净值追踪工具。支持现金、定期存款、基金、股票、债权、贵金属、负债等多资产类型管理，内置净值快照与趋势图表、家庭协作、隐私模式，Docker 一键部署。

### 核心特性

| 特性 | 说明 |
|------|------|
| **多资产类型** | 现金 / 活期、定期存款、基金（份额+净值）、股票（份额+市价）、债权（面值+利率）、贵金属（金/银/铂/钯） |
| **负债管理** | 贷款、信用卡等负债统一记录，资产负债一目了然 |
| **净值快照** | 手动记录净值快照，自动汇总各类合计，ECharts 趋势图 |
| **家庭协作** | 邀请码加入家庭组，家庭总资产汇总，按成员/类别独立的隐私控制 |
| **隐私模式** | 一键切换 `***` 显示；按资产类别和成员粒度隐藏；设置云端持久化 + 本地兜底 |
| **行情刷新** | 集成 akshare / Tushare，实时刷新基金净值、股票价格、贵金属价格 |
| **数据导出** | Excel 分类导出，带样式表头，按资产类别分 Sheet |
| **JWT 认证** | 用户注册 / 登录，安全鉴权 |
| **SPA 单页应用** | 生产模式 FastAPI 直接托管 Vue 构建产物，零 Nginx 依赖 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · aiosqlite · PyJWT |
| 前端 | Vue 3 · Vite · Element Plus · ECharts · Pinia · Vue Router |
| 数据库 | SQLite（单文件零配置） |
| 部署 | Docker · Docker Compose（多阶段构建） |

---

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 1. 克隆仓库

```bash
git clone https://github.com/zhangxingren/wealthhome.git
cd wealthhome
```

### 2. 启动服务

```bash
docker compose up -d
```

首次启动自动构建镜像，并创建 SQLite 数据库。

### 3. 访问应用

打开 `http://localhost:8000`，首次访问进入注册页面。

### 4. 环境变量

通过 `docker-compose.yml` 或 `.env` 配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（**必填**） | 无，未设置则拒绝启动 |
| `DB_PATH` | SQLite 数据库路径 | `/app/data/wealthhome.db` |
| `TUSHARE_TOKEN` | Tushare API Token（行情刷新） | 空 |
| `MARKET_REFRESH_INTERVAL` | 行情自动刷新间隔（分钟，0 关闭） | `0` |

### 5. 停止与更新

```bash
# 停止
docker compose down

# 更新后重建
git pull
docker compose up -d --build
```

---

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：`http://localhost:8000/docs`

### 前端

```bash
cd frontend
npm install
npm run dev
```

Vite dev server 默认运行于 `http://localhost:5173`。

---

## 项目结构

```
wealthhome/
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI 入口，CORS、静态文件托管
│       ├── auth.py                 # JWT 认证（PBKDF2 + HMAC-SHA256）
│       ├── config.py               # 环境变量配置
│       ├── database.py             # SQLite 初始化与连接管理
│       └── routers/
│           ├── assets.py           # 资产管理 CRUD
│           ├── liabilities.py      # 负债管理
│           ├── networth.py         # 净值快照与实时计算
│           ├── family.py           # 家庭组管理
│           ├── precious_metals.py  # 贵金属（金/银/铂/钯）
│           ├── export.py           # Excel 分类导出
│           └── settings.py         # 用户设置云同步
├── frontend/
│   └── src/
│       ├── views/                  # 页面组件
│       ├── components/             # 公共组件
│       ├── composables/            # 组合式函数（隐私、金额格式化）
│       ├── api/                    # Axios 请求封装
│       └── router/                 # 路由（Hash 模式 + 登录守卫）
├── Dockerfile                      # 多阶段构建
├── docker-compose.yml              # 生产部署编排
└── README.md
```

---

## License

本项目基于 [MIT License](LICENSE) 开源。
