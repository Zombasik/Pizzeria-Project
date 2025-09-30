"""
Сервис для работы с пользователями
"""
from typing import Optional
from sqlalchemy.orm import Session
from src.database.models import TelegramUser


class UserService:
    """Сервис для работы с пользователями"""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_user(self, user_data: dict) -> TelegramUser:
        """Получить или создать пользователя"""
        user = self.session.query(TelegramUser).filter_by(
            user_id=user_data['user_id']
        ).first()

        if not user:
            user = TelegramUser(**user_data)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

        return user

    def update_user(self, user_id: int, **kwargs) -> Optional[TelegramUser]:
        """Обновить данные пользователя"""
        user = self.session.query(TelegramUser).filter_by(user_id=user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            self.session.commit()
            return user
        return None

    def ban_user(self, user_id: int) -> bool:
        """Заблокировать пользователя"""
        return self.update_user(user_id, is_banned=True) is not None

    def unban_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        return self.update_user(user_id, is_banned=False) is not None

    def make_admin(self, user_id: int) -> bool:
        """Сделать пользователя администратором"""
        return self.update_user(user_id, is_admin=True) is not None

    def is_banned(self, user_id: int) -> bool:
        """Проверить, заблокирован ли пользователь"""
        user = self.session.query(TelegramUser).filter_by(user_id=user_id).first()
        return user.is_banned if user else False