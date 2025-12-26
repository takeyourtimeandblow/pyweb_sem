from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from .auth import User
from .models import Task
from .database import db

def init_routes(app):
    """Инициализация маршрутов приложения"""
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('tasks'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('tasks'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = 'remember' in request.form
            
            user = User.get_by_username(username)
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Аккаунт деактивирован', 'error')
                    return redirect(url_for('login'))
                
                login_user(user, remember=remember)
                flash('Вход выполнен успешно', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('tasks'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('tasks'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            
            # Валидация
            if not username or not email or not password:
                flash('Все обязательные поля должны быть заполнены', 'error')
                return redirect(url_for('register'))
            
            if password != password_confirm:
                flash('Пароли не совпадают', 'error')
                return redirect(url_for('register'))
            
            if len(password) < 6:
                flash('Пароль должен содержать не менее 6 символов', 'error')
                return redirect(url_for('register'))
            
            # Проверка уникальности
            if User.get_by_username(username):
                flash('Имя пользователя уже занято', 'error')
                return redirect(url_for('register'))
            
            # Проверка email
            existing_user = db.fetch_one('SELECT id FROM users WHERE email = ?', (email,))
            if existing_user:
                flash('Email уже зарегистрирован', 'error')
                return redirect(url_for('register'))
            
            # Создание пользователя
            try:
                user = User.create(username, email, password)
                flash('Регистрация выполнена успешно. Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Ошибка при регистрации: {str(e)}', 'error')
                return redirect(url_for('register'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы', 'success')
        return redirect(url_for('login'))
    
    @app.route('/tasks')
    @login_required
    def tasks():
        # Параметры фильтрации
        status = request.args.get('status')
        priority = request.args.get('priority')
        page = request.args.get('page', 1, type=int)
        
        # Получение задач
        if current_user.is_admin:
            tasks_data = Task.get_all_tasks(
                status=status, 
                priority=priority, 
                page=page, 
                per_page=9
            )
        else:
            tasks_data = Task.get_user_tasks(
                user_id=current_user.id,
                status=status,
                priority=priority,
                page=page,
                per_page=9
            )
        
        return render_template('tasks.html', 
                             tasks=tasks_data['tasks'],
                             pagination=tasks_data,
                             status=status,
                             priority=priority)
    
    @app.route('/task/new', methods=['GET', 'POST'])
    @login_required
    def create_task():
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            status = request.form.get('status', 'new')
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            
            # Валидация
            if not title:
                flash('Название задачи обязательно', 'error')
                return redirect(url_for('create_task'))
            
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Неверный формат даты', 'error')
                    return redirect(url_for('create_task'))
            
            # Создание задачи
            task = Task.create(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                user_id=current_user.id
            )
            
            flash('Задача успешно создана', 'success')
            return redirect(url_for('tasks'))
        
        return render_template('task_form.html', task=None)
    
    @app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_task(task_id):
        task = Task.get(task_id)
        
        if not task:
            flash('Задача не найдена', 'error')
            return redirect(url_for('tasks'))
        
        # Проверка прав доступа
        if not current_user.is_admin and task.user_id != current_user.id:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('tasks'))
        
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            status = request.form.get('status', 'new')
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            
            # Валидация
            if not title:
                flash('Название задачи обязательно', 'error')
                return redirect(url_for('edit_task', task_id=task_id))
            
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Неверный формат даты', 'error')
                    return redirect(url_for('edit_task', task_id=task_id))
            
            # Обновление задачи
            task.update(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date
            )
            
            flash('Задача успешно обновлена', 'success')
            return redirect(url_for('tasks'))
        
        return render_template('task_form.html', task=task)
    
    @app.route('/task/<int:task_id>/delete', methods=['POST'])
    @login_required
    def delete_task(task_id):
        task = Task.get(task_id)
        
        if not task:
            flash('Задача не найдена', 'error')
            return redirect(url_for('tasks'))
        
        # Проверка прав доступа
        if not current_user.is_admin and task.user_id != current_user.id:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('tasks'))
        
        task.delete()
        flash('Задача успешно удалена', 'success')
        return redirect(url_for('tasks'))

    @app.route('/task/<int:task_id>')
    @login_required
    def view_task(task_id):
        """Просмотр задачи"""
        task = Task.get(task_id)
        
        if not task:
            flash('Задача не найдена', 'error')
            return redirect(url_for('tasks'))
        
        # Проверка прав доступа
        if not current_user.is_admin and task.user_id != current_user.id:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('tasks'))
        
        # Передаем текущую дату для расчета просроченных задач
        return render_template('task_detail.html', task=task, now=datetime.now())
    
    @app.route('/profile')
    @login_required
    def profile():
        # Статистика пользователя
        if current_user.is_admin:
            total_tasks = db.fetch_one('SELECT COUNT(*) as count FROM tasks')['count']
            total_users = db.fetch_one('SELECT COUNT(*) as count FROM users')['count']
        else:
            total_tasks = db.fetch_one(
                'SELECT COUNT(*) as count FROM tasks WHERE user_id = ?',
                (current_user.id,)
            )['count']
            total_users = 1
        
        return render_template('profile.html',
                             user=current_user,
                             total_tasks=total_tasks,
                             total_users=total_users)
    
        # Административные маршруты
    @app.route('/admin/users')
    @login_required
    def admin_users():
        """Список пользователей (для администраторов)"""
        if not current_user.is_admin:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('tasks'))
        
        users = User.get_all()
        return render_template('admin/users.html', users=users)
    
    @app.route('/admin/tasks')
    @login_required
    def admin_all_tasks():
        """Все задачи (для администраторов)"""
        if not current_user.is_admin:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('tasks'))
        
        # Получение параметров фильтрации
        status = request.args.get('status')
        priority = request.args.get('priority')
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', 1, type=int)
        
        # Получение всех задач
        tasks_data = Task.get_all_tasks(
            status=status, 
            priority=priority, 
            user_id=user_id,
            page=page, 
            per_page=12
        )
        
        # Получение всех пользователей для фильтра
        users = User.get_all()
        
        return render_template('admin/tasks.html',
                             tasks=tasks_data['tasks'],
                             pagination=tasks_data,
                             users=users,
                             status=status,
                             priority=priority,
                             selected_user_id=user_id)
    
    # API маршруты
    @app.route('/api/tasks')
    @login_required
    def api_tasks():
        """API: Получение задач"""
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        if current_user.is_admin:
            tasks = Task.get_all_tasks(status=status, priority=priority, per_page=100)
        else:
            tasks = Task.get_user_tasks(
                user_id=current_user.id,
                status=status,
                priority=priority,
                per_page=100
            )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks['tasks']],
            'total': tasks['total']
        })
    
    @app.route('/api/task/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def api_task(task_id):
        """API: Работа с конкретной задачей"""
        task = Task.get(task_id)
        
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        # Проверка прав доступа
        if not current_user.is_admin and task.user_id != current_user.id:
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        if request.method == 'GET':
            return jsonify({'task': task.to_dict()})
        
        elif request.method == 'PUT':
            data = request.json
            
            # Валидация данных
            allowed_fields = ['title', 'description', 'status', 'priority', 'due_date']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if 'due_date' in update_data and update_data['due_date']:
                try:
                    update_data['due_date'] = datetime.strptime(
                        update_data['due_date'], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    return jsonify({'error': 'Неверный формат даты'}), 400
            
            task.update(**update_data)
            return jsonify({'message': 'Задача обновлена', 'task': task.to_dict()})
        
        elif request.method == 'DELETE':
            task.delete()
            return jsonify({'message': 'Задача удалена'})
    
    @app.route('/api/docs')
    def api_docs():
        """Документация API"""
        return render_template('api_docs.html')
    
    # Обработчик загрузки пользователя для Flask-Login
    @app.login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)