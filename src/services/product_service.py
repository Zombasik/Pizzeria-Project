"""
Сервис для работы с продуктами
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models import Product


class ProductService:
    """Сервис для работы с продуктами"""

    def __init__(self, session: Session):
        self.session = session

    def get_all_products(self, available_only: bool = False) -> List[Product]:
        """Получить все продукты"""
        query = self.session.query(Product)
        if available_only:
            query = query.filter_by(available=True)
        return query.order_by(Product.category, Product.name).all()

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получить продукт по ID"""
        return self.session.query(Product).filter_by(id=product_id).first()

    def create_product(self, product_data: dict) -> Product:
        """Создать новый продукт"""
        product = Product(**product_data)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Обновить продукт"""
        product = self.get_product_by_id(product_id)
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            self.session.commit()
            return product
        return None

    def delete_product(self, product_id: int) -> bool:
        """Удалить продукт"""
        product = self.get_product_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False

    def toggle_availability(self, product_id: int) -> Optional[bool]:
        """Переключить доступность продукта"""
        product = self.get_product_by_id(product_id)
        if product:
            product.available = not product.available
            self.session.commit()
            return product.available
        return None

    def get_products_by_category(self, category: str) -> List[Product]:
        """Получить продукты по категории"""
        return self.session.query(Product).filter_by(
            category=category, available=True
        ).all()

    def get_categories(self) -> List[str]:
        """Получить список всех категорий"""
        categories = self.session.query(Product.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]