from .user_schema import UserProfile


class UserService:
    def get_user(self, user_id: int) -> UserProfile:
        return UserProfile(user_id=user_id, nickname="Mini User")
