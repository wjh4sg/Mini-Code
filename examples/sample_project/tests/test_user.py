from app.user_service import UserService


def test_get_user_has_nickname():
    user = UserService().get_user(1)
    assert user.nickname == "Mini User"
