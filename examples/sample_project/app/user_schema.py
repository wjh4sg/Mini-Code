from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: int
    nickname: str
