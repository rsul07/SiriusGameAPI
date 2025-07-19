from fastapi import APIRouter, Depends, HTTPException, status
from auth.dependencies import get_current_user
from db.users import UserOrm
from events.repository import EventRepository
from events.schemas import SScoreAdd

router = APIRouter(prefix="/scores", tags=["Scores"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_score(
        score_data: SScoreAdd,
        current_user: UserOrm = Depends(get_current_user)
):
    try:
        await EventRepository.add_score(current_user.id, score_data)
        return {"ok": True}
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
