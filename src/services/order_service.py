"""
Сервис для работы с заказами
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models import Order, OrderItem, Product


class OrderService:
    """Сервис для работы с заказами"""

    def __init__(self, session: Session):
        self.session = session

    def create_order(self, order_data: dict, items: List[dict]) -> Order:
        """Создать новый заказ с позициями"""
        # Вычисляем общую стоимость заказа
        total_price = sum(item_data['price'] * item_data['quantity'] for item_data in items)

        # Добавляем total_price в данные заказа
        order_data['total_price'] = total_price

        # Создаем заказ
        order = Order(**order_data)
        self.session.add(order)
        self.session.flush()  # Получаем ID заказа

        # Добавляем позиции заказа
        for item_data in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            self.session.add(order_item)

        self.session.commit()
        self.session.refresh(order)
        return order

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        return self.session.query(Order).filter_by(id=order_id).first()

    def get_orders_by_status(self, status: str) -> List[Order]:
        """Получить заказы по статусу"""
        return self.session.query(Order).filter_by(status=status).order_by(
            Order.created_at.desc()
        ).all()

    def get_user_orders(self, user_id: int) -> List[Order]:
        """Получить заказы пользователя"""
        return self.session.query(Order).filter_by(user_id=user_id).order_by(
            Order.created_at.desc()
        ).all()

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        order = self.get_order_by_id(order_id)
        if order:
            order.status = status
            self.session.commit()
            return True
        return False

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Получить позиции заказа"""
        return self.session.query(OrderItem).filter_by(order_id=order_id).all()

    def get_order_details(self, order_id: int) -> Optional[dict]:
        """Получить детали заказа с продуктами"""
        order = self.get_order_by_id(order_id)
        if not order:
            return None

        items = self.session.query(OrderItem, Product).join(
            Product, OrderItem.product_id == Product.id
        ).filter(OrderItem.order_id == order_id).all()

        return {
            'order': order,
            'items': [
                {
                    'product': product,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total': item.price * item.quantity
                }
                for item, product in items
            ]
        }