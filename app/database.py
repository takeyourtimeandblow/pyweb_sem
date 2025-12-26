import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path='task_manager.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращает строки как словари
        return conn
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для работы с курсором"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with self.get_cursor() as cursor:
            # Создание таблицы пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание таблицы задач
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'new',
                    priority TEXT DEFAULT 'medium',
                    due_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Создание индексов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
            
            # Проверяем, есть ли администратор
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 1')
            if cursor.fetchone()['count'] == 0:
                # Создаем администратора по умолчанию
                import hashlib
                import secrets
                
                admin_password = 'admin123'
                salt = secrets.token_hex(16)
                password_hash = hashlib.sha256((admin_password + salt).encode()).hexdigest()
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'admin@example.com', f'{salt}${password_hash}', 1, 1))
    
    def execute_query(self, query, params=()):
        """Выполнение запроса с параметрами"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor
    
    def fetch_one(self, query, params=()):
        """Получение одной записи"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetch_all(self, query, params=()):
        """Получение всех записей"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def insert(self, table, data):
        """Вставка записи в таблицу"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        with self.get_cursor() as cursor:
            cursor.execute(query, list(data.values()))
            return cursor.lastrowid
    
    def update(self, table, data, where):
        """Обновление записи в таблице"""
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        where_clause = ' AND '.join([f'{key} = ?' for key in where.keys()])
        query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        
        with self.get_cursor() as cursor:
            params = list(data.values()) + list(where.values())
            cursor.execute(query, params)
            return cursor.rowcount
    
    def delete(self, table, where):
        """Удаление записи из таблицы"""
        where_clause = ' AND '.join([f'{key} = ?' for key in where.keys()])
        query = f'DELETE FROM {table} WHERE {where_clause}'
        
        with self.get_cursor() as cursor:
            cursor.execute(query, list(where.values()))
            return cursor.rowcount

# Глобальный экземпляр базы данных
db = Database()