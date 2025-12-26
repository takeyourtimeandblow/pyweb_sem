from datetime import datetime

class Task:
    """Класс задачи"""
    
    STATUS_CHOICES = ['new', 'in_progress', 'completed']
    PRIORITY_CHOICES = ['low', 'medium', 'high']
    
    def __init__(self, id, title, description, status, priority, due_date, 
                 created_at, updated_at, user_id):
        self.id = id
        self.title = title
        self.description = description or ''
        self.status = status
        self.priority = priority
        self.due_date = self._parse_date(due_date)  # Парсим дату
        self.created_at = self._parse_datetime(created_at)  # Парсим datetime
        self.updated_at = self._parse_datetime(updated_at)  # Парсим datetime
        self.user_id = user_id
    
    def _parse_date(self, date_str):
        """Парсинг строки даты в объект datetime.date"""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            return date_str
        except (ValueError, TypeError):
            return None
    
    def _parse_datetime(self, datetime_str):
        """Парсинг строки datetime в объект datetime.datetime"""
        if not datetime_str:
            return None
        try:
            if isinstance(datetime_str, str):
                # Пробуем разные форматы
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
                    try:
                        return datetime.strptime(datetime_str, fmt)
                    except ValueError:
                        continue
            return datetime_str
        except (ValueError, TypeError):
            return None
    
    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'user_id': self.user_id
        }
    
    @staticmethod
    def create(title, description, status, priority, due_date, user_id):
        """Создание новой задачи"""
        from .database import db
        
        # Форматируем дату для базы данных
        due_date_str = due_date.strftime('%Y-%m-%d') if due_date else None
        
        task_id = db.insert('tasks', {
            'title': title,
            'description': description,
            'status': status,
            'priority': priority,
            'due_date': due_date_str,
            'user_id': user_id
        })
        
        return Task.get(task_id)
    
    @staticmethod
    def get(task_id):
        """Получение задачи по ID"""
        from .database import db
        
        result = db.fetch_one('SELECT * FROM tasks WHERE id = ?', (task_id,))
        if result:
            return Task(**result)
        return None
    
    def update(self, **kwargs):
        """Обновление задачи"""
        from .database import db
        
        allowed_fields = ['title', 'description', 'status', 'priority', 'due_date']
        update_data = {}
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'due_date':
                    # Форматируем дату для базы данных
                    update_data[key] = value.strftime('%Y-%m-%d') if value else None
                else:
                    update_data[key] = value
        
        if update_data:
            update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update('tasks', update_data, {'id': self.id})
            
            # Обновляем объект
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(self, key, value)
    
    def delete(self):
        """Удаление задачи"""
        from .database import db
        db.delete('tasks', {'id': self.id})
    
    @staticmethod
    def get_user_tasks(user_id, status=None, priority=None, page=1, per_page=10):
        """Получение задач пользователя с фильтрацией и пагинацией"""
        from .database import db
        
        query = 'SELECT * FROM tasks WHERE user_id = ?'
        params = [user_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        query += ' ORDER BY created_at DESC'
        
        # Получаем все задачи для пагинации
        all_tasks = db.fetch_all(query, params)
        
        # Пагинация
        start = (page - 1) * per_page
        end = start + per_page
        paginated_tasks = all_tasks[start:end]
        
        return {
            'tasks': [Task(**task) for task in paginated_tasks],
            'total': len(all_tasks),
            'pages': (len(all_tasks) + per_page - 1) // per_page,
            'current_page': page
        }
    
    @staticmethod
    def get_all_tasks(status=None, priority=None, user_id=None, page=1, per_page=10):
        """Получение всех задач (для администратора)"""
        from .database import db
        
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY created_at DESC'
        
        # Получаем все задачи для пагинации
        all_tasks = db.fetch_all(query, params)
        
        # Пагинация
        start = (page - 1) * per_page
        end = start + per_page
        paginated_tasks = all_tasks[start:end]
        
        return {
            'tasks': [Task(**task) for task in paginated_tasks],
            'total': len(all_tasks),
            'pages': (len(all_tasks) + per_page - 1) // per_page,
            'current_page': page
        }
    
    def get_author(self):
        """Получение автора задачи"""
        from .auth import User
        return User.get(self.user_id)