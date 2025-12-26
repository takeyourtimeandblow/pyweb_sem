from flask import Flask
from flask_login import LoginManager

# Инициализация Flask-Login
login_manager = LoginManager()

def create_app():
    """Создание Flask приложения"""
    app = Flask(__name__)
    
    # Конфигурация
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['ITEMS_PER_PAGE'] = 9
    
    # Инициализация Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Инициализация базы данных
    from .database import db
    # База данных инициализируется автоматически при импорте
    
    # Инициализация маршрутов
    from .routes import init_routes
    init_routes(app)
    
    return app