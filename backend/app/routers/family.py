"""家庭管理 — 加入/查看/退出家庭"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/family", tags=["家庭"])


class JoinRequest(BaseModel):
    invite_code: str = Field(..., min_length=4, max_length=16)


@router.get("")
def get_family(user=Depends(get_current_user)):
    uid = int(user["sub"])
    with get_db() as db:
        user_row = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
        if not user_row or not user_row["family_id"]:
            raise HTTPException(status_code=404, detail="未加入家庭")

        fam = db.execute("SELECT * FROM families WHERE id=?", (user_row["family_id"],)).fetchone()
        members = db.execute(
            "SELECT id, username, role, display_name, created_at FROM users WHERE family_id=? ORDER BY id",
            (user_row["family_id"],)
        ).fetchall()

    return {
        "family": dict(fam),
        "members": [dict(m) for m in members],
    }


@router.post("/join")
def join_family(body: JoinRequest, user=Depends(get_current_user)):
    uid = int(user["sub"])
    with get_db() as db:
        fam = db.execute("SELECT id, name FROM families WHERE invite_code=?", (body.invite_code.upper(),)).fetchone()
        if not fam:
            raise HTTPException(status_code=404, detail="邀请码无效")

        current = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
        if current["family_id"] == fam["id"]:
            raise HTTPException(status_code=409, detail="你已在该家庭中")

        db.execute("UPDATE users SET family_id=? WHERE id=?", (fam["id"], uid))

    return {"message": f"已加入「{fam['name']}」", "family_id": fam["id"], "family_name": fam["name"]}


@router.get("/members")
def list_members(user=Depends(get_current_user)):
    uid = int(user["sub"])
    with get_db() as db:
        user_row = db.execute("SELECT family_id FROM users WHERE id=?", (uid,)).fetchone()
        if not user_row or not user_row["family_id"]:
            return {"members": []}

        members = db.execute(
            "SELECT id, username, role, display_name, created_at FROM users WHERE family_id=? ORDER BY id",
            (user_row["family_id"],)
        ).fetchall()
    return {"members": [dict(m) for m in members]}
