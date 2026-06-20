from fastapi import APIRouter

from .user_service import UserService


router = APIRouter(prefix="/user")
service = UserService()


@router.get("/{user_id}")
def get_user(user_id: int):
    return service.get_user(user_id)
