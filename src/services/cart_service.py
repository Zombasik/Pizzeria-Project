"""
Сервис для работы с корзиной
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import Cart, Product


class CartService:
    """Сервис для работы с корзиной покупок"""

    def __init__(self, session: Session):
        self.session = session

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Cart:
        """Добавить товар в корзину"""
        # Проверяем, есть ли уже такой товар в корзине
        cart_item = self.session.query(Cart).filter(
            and_(Cart.user_id == user_id, Cart.product_id == product_id)
        ).first()

        if cart_item:
            # Увеличиваем количество
            cart_item.quantity += quantity
        else:
            # Создаем новую запись
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            self.session.add(cart_item)

        self.session.commit()
        self.session.refresh(cart_item)
        return cart_item

    def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        """Удалить товар из корзины"""
        cart_item = self.session.query(Cart).filter(
            and_(Cart.user_id == user_id, Cart.product_id == product_id)
        ).first()

        if cart_item:
            self.session.delete(cart_item)
            self.session.commit()
            return True
        return False

    def update_quantity(self, user_id: int, product_id: int, quantity: int) -> Optional[Cart]:
        """Обновить количество товара в корзине"""
        cart_item = self.session.query(Cart).filter(
            and_(Cart.user_id == user_id, Cart.product_id == product_id)
        ).first()

        if cart_item:
            if quantity <= 0:
                self.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
            self.session.commit()
            return cart_item if quantity > 0 else None
        return None

    def get_user_cart(self, user_id: int) -> List[Dict]:
        """Получить содержимое корзины пользователя"""
        cart_items = self.session.query(Cart, Product).join(
            Product, Cart.product_id == Product.id
        ).filter(Cart.user_id == user_id).all()

        result = []
        for cart_item, product in cart_items:
            result.append({
                'cart_id': cart_item.id,
                'product_id': product.id,
                'product_name': product.name,
                'product_price': product.price,
                'quantity': cart_item.quantity,
                'total': product.price * cart_item.quantity
            })
        return result

    def get_cart_total(self, user_id: int) -> float:
        """Получить общую сумму корзины"""
        cart_items = self.get_user_cart(user_id)
        return sum(item['total'] for item in cart_items)

    def clear_cart(self, user_id: int) -> bool:
        """Очистить корзину пользователя"""
        cart_items = self.session.query(Cart).filter_by(user_id=user_id).all()
        for item in cart_items:
            self.session.delete(item)
        self.session.commit()
        return True

    def get_cart_items_count(self, user_id: int) -> int:
        """Получить количество товаров в корзине"""
        return self.session.query(Cart).filter_by(user_id=user_id).count()