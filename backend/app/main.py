"""FastAPI 应用入口"""

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import init_db
from app.routers import auth, assets, liabilities, export, networth, family, precious_metals, settings

app = FastAPI(title="WealthHome", version="1.0.0")

cors_origins_raw = os.getenv("CORS_ORIGINS", "")
cors_origins = cors_origins_raw.split(",") if cors_origins_raw else ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 禁止缓存静态资源（开发阶段确保每次刷新都加载最新文件）
class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith(('.html', '.js', '.css', '.svg', '.json')):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

app.add_middleware(NoCacheStaticMiddleware)

app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(liabilities.router)
app.include_router(export.router)
app.include_router(networth.router)
app.include_router(family.router)
app.include_router(precious_metals.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    try:
        from app.core.database import get_db
        with get_db() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "ok", "database": "disconnected"}


# 生产模式：托管 Vue 前端构建产物
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """SPA fallback：非 /api 路径返回 index.html"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            resp = FileResponse(index)
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
            return resp
        raise HTTPException(status_code=404)


@app.on_event("startup")
def startup():
    init_db()
    _seed_default_admin()


def _seed_default_admin():
    """首次部署时自动创建管理员账号（仅当用户表为空时）"""
    from app.core.database import get_db
    from app.core.auth import hash_password
    import secrets, string

    with get_db() as db:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return  # 已有用户，跳过种子

        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "")

        if not admin_pass:
            admin_pass = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        password_hash = hash_password(admin_pass)
        invite_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

        db.execute("INSERT INTO families (name, invite_code) VALUES ('我的家庭', ?)", (invite_code,))
        family_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        db.execute(
            "INSERT INTO users (username, password_hash, role, display_name, family_id) VALUES (?, ?, 'admin', '管理员', ?)",
            (admin_user, password_hash, family_id),
        )

        from app.core.config import settings
        db_path = settings.db_path

    if not os.getenv("ADMIN_PASSWORD"):
        print(f"\n{'='*60}")
        print(f"  WealthHome 首次启动 — 管理员账号已创建")
        print(f"  用户名: {admin_user}")
        print(f"  密码:   {admin_pass}")
        print(f"  ⚠️  请立即登录并修改密码！")
        print(f"{'='*60}\n")
    else:
        print(f"WealthHome: 管理员账号 {admin_user} 已创建")
