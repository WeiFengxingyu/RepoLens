class UserRepository:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, str]] = {}

    def save_profile(self, user_id: str, profile: dict[str, str]) -> dict[str, str]:
        saved = {"id": user_id, "display_name": profile.get("display_name", ""), "email": profile.get("email", "")}
        self.users[user_id] = saved
        return saved

    def get_user(self, user_id: str) -> dict[str, str]:
        return self.users.get(user_id, {"id": user_id, "display_name": "Unknown", "email": ""})
