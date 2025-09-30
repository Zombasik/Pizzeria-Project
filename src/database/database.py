"""
Менеджер базы данных
"""
from sqlalchemy.orm import Session
from typing import Optional
from .models import (
    get_engine, get_session_factory, create_tables,
    Product, TelegramUser, Order, OrderItem, Cart, AdminToken
)


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, database_url: str):
        self.engine = get_engine(database_url)
        self.session_factory = get_session_factory(self.engine)
        create_tables(self.engine)

    def get_session(self) -> Session:
        """Получить сессию для работы с БД"""
        return self.session_factory()

    def close_session(self, session: Session):
        """Закрыть сессию"""
        session.close()

    # Методы для работы с пользователями
    def get_user(self, user_id: int) -> Optional[TelegramUser]:
        """Получить пользователя по ID"""
        with self.get_session() as session:
            return session.query(TelegramUser).filter_by(user_id=user_id).first()

    def create_user(self, user_data: dict) -> TelegramUser:
        """Создать нового пользователя"""
        with self.get_session() as session:
            user = TelegramUser(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    # Методы для работы с продуктами
    def get_products(self, available_only: bool = False) -> list[Product]:
        """Получить список продуктов"""
        with self.get_session() as session:
            query = session.query(Product)
            if available_only:
                query = query.filter_by(available=True)
            return query.all()

    def get_product(self, product_id: int) -> Optional[Product]:
        """Получить продукт по ID"""
        with self.get_session() as session:
            return session.query(Product).filter_by(id=product_id).first()

    # Методы для работы с заказами
    def create_order(self, order_data: dict) -> Order:
        """Создать новый заказ"""
        with self.get_session() as session:
            order = Order(**order_data)
            session.add(order)
            session.commit()
            session.refresh(order)
            return order

    def get_orders_by_status(self, status: str) -> list[Order]:
        """Получить заказы по статусу"""
        with self.get_session() as session:
            return session.query(Order).filter_by(status=status).all()

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        with self.get_session() as session:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.status = status
                session.commit()
                return True
            return False