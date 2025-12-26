#!/usr/bin/env python3
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("Task Manager запущен!")
    print("Доступ по адресу: http://localhost:5000")
    print("Администратор: admin / admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)