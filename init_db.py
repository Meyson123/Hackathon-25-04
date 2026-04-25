import sqlite3
import os

def init_db():
    db_path = 'mediahub.db'
    schema_path = 'database_schema.sql'
    
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
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
