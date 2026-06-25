"""用户设置同步 API — 隐藏资产等偏好跨设备同步"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["settings"])


class SettingUpdate(BaseModel):
    value: Any


@router.get("/settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    with get_db() as db:
        rows = db.execute(
            "SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    result = {}
    for row in rows:
        import json
        try:
            result[row["setting_key"]] = json.loads(row["setting_value"])
        except (json.JSONDecodeError, TypeError):
            result[row["setting_key"]] = row["setting_value"]
    return result


@router.put("/settings/{setting_key}")
def put_setting(
    setting_key: str,
    body: SettingUpdate,
    current_user: dict = Depends(get_current_user),
):
    import json
    user_id = int(current_user["sub"])
    value_str = json.dumps(body.value, ensure_ascii=False)
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM user_settings WHERE user_id = ? AND setting_key = ?",
            (user_id, setting_key),
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE user_settings SET setting_value = ? WHERE user_id = ? AND setting_key = ?",
                (value_str, user_id, setting_key),
            )
        else:
            db.execute(
                "INSERT INTO user_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?)",
                (user_id, setting_key, value_str),
            )
    return {"ok": True, "key": setting_key}
