import sqlite3
import os
import bcrypt

def init_db():
    """Инициализация базы данных"""
    db_path = os.path.join(os.path.dirname(__file__), 'mediahub.db')
    schema_path = os.path.join(os.path.dirname(__file__), 'db_schema.sql')

    if not os.path.exists(schema_path):
        print(f"Ошибка: Файл {schema_path} не найден.")
        return

    try:
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()

        conn.executescript(schema)
        conn.commit()

        # Проверка созданных таблиц
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"База данных '{db_path}' успешно инициализирована.")
        print("Созданные таблицы:")
        for table in tables:
            print(f" - {table[0]}")

        # Создание тестового администратора
        create_admin_user(conn)

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if conn:
            conn.close()

def create_admin_user(conn):
    """Создание тестового администратора"""
    try:
        # Создание тестового админа должно быть явным действием (только для dev).
        if os.getenv("CREATE_TEST_ADMIN", "0") != "1":
            return

        # Проверяем, существует ли уже админ
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()

        if existing_admin:
            print("Администратор уже существует.")
            return

        # Хеширование пароля (берём из окружения, без дефолта)
        password = os.getenv("TEST_ADMIN_PASSWORD")
        if not password:
            raise RuntimeError("TEST_ADMIN_PASSWORD is required when CREATE_TEST_ADMIN=1")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Создание администратора
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, role, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "admin@mediahub.ru", hashed_password, "Администратор", "admin", "active")
        )
        conn.commit()
        print("Тестовый администратор создан: логин admin")

    except Exception as e:
        print(f"Ошибка при создании администратора: {e}")
        conn.rollback()

if __name__ == "__main__":
    init_db()
