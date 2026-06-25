"""用户注册与登录路由"""

import time
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from app.database import get_db
from app.auth import hash_password, verify_password, create_token, get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 登录频率限制：同一 IP 每分钟最多 5 次尝试
_login_attempts: dict[str, list[float]] = {}


def _gen_invite_code(length=8):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(body: RegisterRequest):
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        role = "admin" if count == 0 else "user"

        # 注册即创建家庭
        code = _gen_invite_code()
        db.execute("INSERT INTO families (name, invite_code) VALUES (?, ?)", (f"{body.username}的家庭", code))
        family_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        db.execute(
            "INSERT INTO users (username, password_hash, role, family_id) VALUES (?, ?, ?, ?)",
            (body.username, hash_password(body.password), role, family_id),
        )
        db.commit()

        user = db.execute("SELECT id, role, family_id FROM users WHERE username = ?", (body.username,)).fetchone()
        token = create_token(user["id"], body.username, user["role"])
        return {"token": token, "user": {"id": user["id"], "username": body.username, "role": user["role"], "family_id": user["family_id"]}}


@router.post("/login")
def login(body: LoginRequest, request: Request):
    # 登录频率限制：同一 IP 每分钟最多 5 次尝试
    ip = request.client.host
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < 60]
    if len(attempts) >= 5:
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")
    _login_attempts.setdefault(ip, []).append(now)

    with get_db() as db:
        user = db.execute("SELECT id, username, password_hash, role, family_id FROM users WHERE username = ?", (body.username,)).fetchone()
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

        # 登录成功，清理该 IP 的旧记录
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < 60]

        token = create_token(user["id"], user["username"], user["role"])
        return {"token": token, "user": {"id": user["id"], "username": user["username"], "role": user["role"], "family_id": user["family_id"]}}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    with get_db() as db:
        user = db.execute("SELECT id, username, role, display_name, family_id FROM users WHERE id=?", (int(current_user["sub"]),)).fetchone()
    return {"id": user["id"], "username": user["username"], "role": user["role"], "display_name": user["display_name"] or "", "family_id": user["family_id"]}


class UpdateProfileRequest(BaseModel):
    display_name: str = Field("", max_length=32)


@router.put("/me")
def update_me(body: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    with get_db() as db:
        db.execute("UPDATE users SET display_name=? WHERE id=?", (body.display_name.strip(), int(current_user["sub"])))
        db.commit()
    return {"ok": True, "display_name": body.display_name.strip()}


@router.get("/users")
def list_users(admin: dict = Depends(require_admin)):
    with get_db() as db:
        rows = db.execute("SELECT id, username, role, family_id, created_at FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]
