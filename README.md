<p align="center">
  <img src="https://img.shields.io/github/license/zhangxingren/wealthhome" alt="License">
  <img src="https://img.shields.io/github/stars/zhangxingren/wealthhome" alt="Stars">
  <img src="https://img.shields.io/github/v/release/zhangxingren/wealthhome" alt="Release">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.x-brightgreen" alt="Vue">
</p>


<h1 align="center">WealthHome</h1>


<p align="center"><strong>家庭财务一站式管理平台</strong></p>


<p align="center">自托管（Self-Hosted）的个人与家庭资产追踪工具——多资产类型管理、家庭协作、净值趋势、隐私保护，Docker 一键部署。</p>


<p align="center">
  <img src="https://img.shields.io/badge/Built%20by-AI-blueviolet" alt="Built by AI">
  <sub>本项目由 AI（腾讯 Marvis）辅助生成</sub>
</p>


---


## 功能特性


- **多资产类型管理**：现金 / 活期、定期存款、基金（份额 + 净值）、股票（份额 + 市价）、债权（面值 + 利率）、贵金属（黄金 / 白银 / 铂金 / 钯金，按克重 + 单价管理）
- **负债追踪**：贷款、信用卡等负债统一记录
- **净值快照与趋势**：手动记录净值快照，自动计算各类资产合计与总负债，ECharts 净值趋势图
- **家庭协作**：邀请码加入家庭组，家庭总资产汇总视图，按成员与类别独立的隐私隐藏控制
- **隐私模式**：一键切换，数字以 `***` 显示；支持按资产类别和家庭成员粒度隐藏；设置云端持久化 + 本地兜底
- **行情刷新**：集成 akshare / Tushare，支持实时刷新基金净值、股票价格、贵金属价格
- **数据导出**：Excel 分类导出，带样式表头，按资产类别分 Sheet
- **用户认证**：JWT 登录 / 注册
- **SPA 单页应用**：生产模式 FastAPI 直接托管 Vue 前端构建产物


## 技术栈


| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · aiosqlite · JWT |
| 前端 | Vue 3 · Vite · Element Plus · ECharts · Pinia · Vue Router |
| 数据库 | SQLite（文件存储，零配置） |
| 部署 | Docker · Docker Compose（多阶段构建） |


## 快速开始（Docker 部署）


### 前置要求


- **Docker** 20.10+
- **Docker Compose** 2.0+


### 1. 克隆仓库


```bash
git clone https://github.com/zhangxingren/wealthhome.git
cd wealthhome
```


### 2. 启动服务


```bash
docker compose up -d
```


首次启动会自动构建镜像（Node 构建前端 + Python 运行后端），并创建 SQLite 数据库。


### 3. 访问应用


浏览器打开 [**http://localhost:8000**](http://localhost:8000)，首次访问进入注册页面。


### 4. 环境变量


通过 `docker-compose.yml` 或 `.env` 文件配置：


| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | SQLite 数据库路径 | `/app/data/wealthhome.db` |
| `JWT_SECRET` | JWT 签名密钥，务必修改 | `your-jwt-secret-change-me` |
| `TUSHARE_TOKEN` | Tushare API Token（行情刷新） | （空） |
| `MARKET_REFRESH_INTERVAL` | 行情自动刷新间隔（分钟，0 为关闭） | `0` |


数据持久化在 Docker Volume `wealthhome_data` 中。


### 5. 停止与更新


停止服务
```bash
docker compose down
```


拉取最新代码后重新构建并启动
```bash
git pull
docker compose up -d --build
```


## 开发模式部署（Docker Compose Watch）


修改源码后自动同步，无需手动重建镜像：


```bash
docker compose -f docker-compose.dev.yml up --watch
```


## 本地开发（从零开始）


### 后端


```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


API 文档自动生成于 [http://localhost:8000/docs](http://localhost:8000/docs)


### 前端


```bash
cd frontend
npm install
npm run dev
```


Vite dev server 默认运行于 [http://localhost:5173](http://localhost:5173)，需配置代理转发 API 请求至后端 `:8000`。


## 项目结构


```
wealthhome/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，CORS、静态文件托管、SPA fallback
│   │   ├── auth.py              # JWT 认证逻辑
│   │   ├── config.py            # 环境变量配置
│   │   ├── database.py          # SQLite 初始化与连接管理
│   │   └── routers/
│   │       ├── assets.py        # 资产管理（现金 / 定期 / 基金 / 股票 / 债权 CRUD）
│   │       ├── liabilities.py   # 负债管理
│   │       ├── networth.py      # 净值快照与实时计算
│   │       ├── family.py        # 家庭组管理（创建 / 加入 / 退出 / 汇总）
│   │       ├── precious_metals.py  # 贵金属（黄金 / 白银 / 铂金 / 钯金）
│   │       ├── export.py        # Excel 分类导出
│   │       └── settings.py      # 用户设置设置云同步（隐私偏好等）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── router/index.js      # 路由配置（hash 模式 + 登录守卫）
│   │   ├── composables/
│   │   │   └── usePrivacy.js    # 隐私模式（全局状态 + 跨设备同步）
│   │   ├── views/               # 页面组件（Dashboard / Cash / Deposit / Fund / Stock / Bond / PreciousMetal / Liability / NetWorth / Family / Login）
│   │   └── api/                 # Axios API 请求封装
│   ├── package.json
│   └── vite.config.js
├── Dockerfile                   # 多阶段构建（Node 构建前端 + Python 运行后端）
├── docker-compose.yml           # 生产部署编排
└── README.md
```


## API 文档


FastAPI 自动生成 OpenAPI（Swagger）文档，启动后端后访问：


- Swagger UI：[http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc：[http://localhost:8000/redoc](http://localhost:8000/redoc)


## License


本项目基于 [MIT License](LICENSE) 开源。
