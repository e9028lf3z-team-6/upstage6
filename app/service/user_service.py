import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.exceptions import EmailNotAllowedNameExistsError

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime

class UserId:
    next_id = 1


class UserService:
    def __init__(self):
        self._users_memory_db: Dict[int, User] = {}

    def _valid_email(self, email: str) -> bool:
        logger.info(f"email valid check: {email}")
        if email == "admin@example.com":
            raise EmailNotAllowedNameExistsError(email)
        return True

    def create_user(self, name: str, email: str) -> User:
        if not self._valid_email(email):
            raise ValueError("Invalid email format")
        # save 추가
        user = User(
            id=UserId.next_id,
            name=name,
            email=email,
            created_at=datetime.now()
        )
        self._users_memory_db[UserId.next_id] = user
        UserId.next_id += 1
        return user
