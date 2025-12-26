import hashlib
import secrets
from flask_login import UserMixin
from .database import db

class User(UserMixin):
    """Класс пользователя для Flask-Login"""
    
    def __init__(self, id, username, email, password_hash, is_admin=False, is_active=True, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._is_admin = bool(is_admin)
        self._is_active = bool(is_active)  # Используем _is_active вместо is_active
        self.created_at = created_at
    
    @property
    def is_active(self):
        """Свойство is_active (только для чтения)"""
        return self._is_active
    
    @property
    def is_admin(self):
        """Свойство is_admin (только для чтения)"""
        return self._is_admin
    
    @staticmethod
    def hash_password(password):
        """Хеширование пароля с солью"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f'{salt}${password_hash}'
    
    def check_password(self, password):
        """Проверка пароля"""
        if not self.password_hash:
            return False
        
        try:
            salt, stored_hash = self.password_hash.split('$')
            test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return test_hash == stored_hash
        except:
            return False
    
    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self._is_admin,
            'is_active': self._is_active,
            'created_at': self.created_at
        }
    
    @staticmethod
    def get(user_id):
        """Получение пользователя по ID"""
        result = db.fetch_one('SELECT * FROM users WHERE id = ?', (user_id,))
        if result:
            # Преобразуем целочисленные значения в булевы
            result['is_admin'] = bool(result['is_admin'])
            result['is_active'] = bool(result['is_active'])
            return User(**result)
        return None
    
    @staticmethod
    def get_by_username(username):
        """Получение пользователя по имени"""
        result = db.fetch_one('SELECT * FROM users WHERE username = ?', (username,))
        if result:
            # Преобразуем целочисленные значения в булевы
            result['is_admin'] = bool(result['is_admin'])
            result['is_active'] = bool(result['is_active'])
            return User(**result)
        return None
    
    @staticmethod
    def get_by_email(email):
        """Получение пользователя по email"""
        result = db.fetch_one('SELECT * FROM users WHERE email = ?', (email,))
        if result:
            result['is_admin'] = bool(result['is_admin'])
            result['is_active'] = bool(result['is_active'])
            return User(**result)
        return None
    
    @staticmethod
    def create(username, email, password, is_admin=False):
        """Создание нового пользователя"""
        password_hash = User.hash_password(password)
        
        user_id = db.insert('users', {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'is_admin': 1 if is_admin else 0,
            'is_active': 1
        })
        
        return User.get(user_id)
    
    @staticmethod
    def get_all():
        """Получение всех пользователей"""
        results = db.fetch_all('SELECT * FROM users ORDER BY username')
        users = []
        for row in results:
            row['is_admin'] = bool(row['is_admin'])
            row['is_active'] = bool(row['is_active'])
            users.append(User(**row))
        return users
    
    def update(self, **kwargs):
        """Обновление данных пользователя"""
        allowed_fields = ['username', 'email', 'password_hash', 'is_admin', 'is_active']
        update_data = {}
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key in ['is_admin', 'is_active']:
                    update_data[key] = 1 if value else 0
                else:
                    update_data[key] = value
        
        if update_data:
            db.update('users', update_data, {'id': self.id})
            
            # Обновляем объект
            for key, value in update_data.items():
                if key == 'password_hash':
                    self.password_hash = value
                elif key == 'is_admin':
                    self._is_admin = bool(value)
                elif key == 'is_active':
                    self._is_active = bool(value)
                else:
                    setattr(self, key, value)
    
    def change_password(self, new_password):
        """Смена пароля"""
        new_password_hash = self.hash_password(new_password)
        self.update(password_hash=new_password_hash)
    
    def __repr__(self):
        return f'<User {self.username}>'