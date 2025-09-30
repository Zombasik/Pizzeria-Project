import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import Base, Product, Order, OrderItem, Cart, TelegramUser, AdminToken
from config import SECRET_KEY, DATABASE_URL

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id, username=None, first_name=None):
        self.id = user_id
        self.username = username
        self.first_name = first_name


@login_manager.user_loader
def load_user(user_id):
    telegram_user = db.session.query(TelegramUser).filter_by(user_id=int(user_id)).first()
    if telegram_user and telegram_user.is_admin:
        return User(telegram_user.user_id, telegram_user.username, telegram_user.first_name)
    return None


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return super(MyAdminIndexView, self).index()

    def is_accessible(self):
        return current_user.is_authenticated


class ProductModelView(ModelView):
    column_list = ['id', 'name', 'description', 'price', 'available', 'category', 'image']
    column_searchable_list = ['name', 'description', 'category']
    column_filters = ['price', 'name', 'category', 'available']
    column_editable_list = ['price', 'name', 'available']
    form_columns = ['name', 'description', 'price', 'category', 'available', 'image']

    column_labels = {
        'id': 'ID',
        'name': 'Название',
        'description': 'Описание',
        'price': 'Цена',
        'image': 'Изображение',
        'available': 'В наличии',
        'category': 'Категория'
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class OrderModelView(ModelView):
    column_list = ['id', 'user_id', 'username', 'phone', 'address', 'total_price', 'status', 'created_at']
    column_searchable_list = ['username', 'phone', 'address', 'status']
    column_filters = ['status', 'created_at', 'total_price']
    column_editable_list = ['status']
    form_columns = ['user_id', 'username', 'phone', 'address', 'total_price', 'status']

    column_labels = {
        'id': 'ID',
        'user_id': 'ID пользователя',
        'username': 'Имя пользователя',
        'phone': 'Телефон',
        'address': 'Адрес',
        'total_price': 'Общая сумма',
        'status': 'Статус',
        'created_at': 'Дата создания'
    }

    column_choices = {
        'status': [
            ('pending', 'Ожидает'),
            ('processing', 'В обработке'),
            ('preparing', 'Готовится'),
            ('delivering', 'Доставляется'),
            ('completed', 'Завершен'),
            ('cancelled', 'Отменен')
        ]
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class OrderItemModelView(ModelView):
    column_list = ['id', 'order_id', 'product_id', 'quantity', 'price']
    column_filters = ['order_id', 'product_id']
    form_columns = ['order_id', 'product_id', 'quantity', 'price']

    column_labels = {
        'id': 'ID',
        'order_id': 'ID заказа',
        'product_id': 'ID товара',
        'quantity': 'Количество',
        'price': 'Цена'
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class TelegramUserModelView(ModelView):
    column_list = ['id', 'user_id', 'username', 'first_name', 'last_name', 'phone', 'created_at', 'is_banned']
    column_searchable_list = ['username', 'first_name', 'last_name', 'phone']
    column_filters = ['is_banned', 'created_at']
    column_editable_list = ['is_banned', 'phone']
    form_columns = ['user_id', 'username', 'first_name', 'last_name', 'phone', 'is_banned']

    column_labels = {
        'id': 'ID',
        'user_id': 'Telegram ID',
        'username': 'Username',
        'first_name': 'Имя',
        'last_name': 'Фамилия',
        'phone': 'Телефон',
        'created_at': 'Дата регистрации',
        'is_banned': 'Заблокирован'
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class CartModelView(ModelView):
    column_list = ['id', 'user_id', 'product_id', 'quantity']
    column_filters = ['user_id', 'product_id']
    form_columns = ['user_id', 'product_id', 'quantity']

    column_labels = {
        'id': 'ID',
        'user_id': 'ID пользователя',
        'product_id': 'ID товара',
        'quantity': 'Количество'
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


admin = Admin(app, name='Pizza Bot Admin', template_mode='bootstrap4', index_view=MyAdminIndexView())
admin.add_view(ProductModelView(Product, db.session, name='Продукты'))
admin.add_view(OrderModelView(Order, db.session, name='Заказы'))
admin.add_view(OrderItemModelView(OrderItem, db.session, name='Позиции заказов'))
admin.add_view(TelegramUserModelView(TelegramUser, db.session, name='Пользователи'))
admin.add_view(CartModelView(Cart, db.session, name='Корзина'))


@app.route('/auth/<token>')
def auth_by_token(token):
    from datetime import datetime

    # Проверяем токен в базе данных
    admin_token = db.session.query(AdminToken).filter_by(token=token).first()

    if not admin_token:
        return '<h1>❌ Неверный токен авторизации</h1>', 401

    # Проверяем срок действия токена
    if admin_token.expires_at < datetime.utcnow():
        db.session.delete(admin_token)
        db.session.commit()
        return '<h1>⏰ Токен истек. Запросите новый в боте командой /admin</h1>', 401

    # Находим пользователя
    telegram_user = db.session.query(TelegramUser).filter_by(user_id=admin_token.user_id).first()

    if not telegram_user or not telegram_user.is_admin:
        return '<h1>❌ У вас нет прав администратора</h1>', 403

    # Авторизуем пользователя
    user = User(telegram_user.user_id, telegram_user.username, telegram_user.first_name)
    login_user(user, remember=True)

    # Удаляем использованный токен
    db.session.delete(admin_token)
    db.session.commit()

    return redirect(url_for('admin.index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    from flask import render_template_string

    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
                color: #333;
            }
            .btn-login {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                width: 100%;
                padding: 0.75rem;
                font-size: 1rem;
                font-weight: 500;
            }
            .btn-login:hover {
                background: linear-gradient(135deg, #5a67d8 0%, #6b4299 100%);
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2 class="login-header">🍕 Pizza Bot Admin</h2>
            <div class="alert alert-info">
                <h5>📱 Авторизация через Telegram</h5>
                <p>Для входа в админ-панель:</p>
                <ol>
                    <li>Откройте бота в Telegram</li>
                    <li>Отправьте команду <code>/admin</code></li>
                    <li>Получите ссылку для входа</li>
                    <li>Перейдите по ссылке</li>
                </ol>
            </div>
            <div class="text-center mt-3">
                <p class="text-muted">Только администраторы могут получить доступ</p>
            </div>
        </div>
    </body>
    </html>
    ''')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.cli.command('list-admins')
def list_admins():
    """Показать список администраторов"""
    with app.app_context():
        admins = db.session.query(TelegramUser).filter_by(is_admin=True).all()
        if admins:
            print("\n📋 Список администраторов:")
            for admin in admins:
                print(f"ID: {admin.user_id}, Username: @{admin.username or 'нет'}, "
                      f"Имя: {admin.first_name} {admin.last_name or ''}")
        else:
            print("\n❌ Администраторов не найдено")
            print("Добавьте администраторов через бота командой /setadmin")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)