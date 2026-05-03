"""通知渠道 API"""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_api_user
from app.models.models import User
from app.notifiers.registry import get_all_notifier_types

router = APIRouter(prefix="/notifiers", tags=["api-notifiers"])


@router.get("/types")
async def api_notifier_types(
    user: User = Depends(get_current_api_user),
):
    return get_all_notifier_types()