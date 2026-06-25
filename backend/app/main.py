"""FastAPI 应用入口"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
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

app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(liabilities.router)
app.include_router(export.router)
app.include_router(networth.router)
app.include_router(family.router)
app.include_router(precious_metals.router)
app.include_router(settings.router)

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
            return FileResponse(index)
        raise HTTPException(status_code=404)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    try:
        from app.database import get_db
        with get_db() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "ok", "database": "disconnected"}
