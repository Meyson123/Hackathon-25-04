import sqlite3
import os
import random
import bcrypt
from datetime import datetime, timedelta
DB_PATH = os.path.join(os.path.dirname(__file__), 'mediahub.db')

# Данные для генерации
TITLES = [
    "Запуск нового продукта: что нужно знать",
    "Итоги квартала: рост и достижения",
    "Как мы оптимизировали рабочие процессы",
    "Встреча с партнёрами: ключевые моменты",
    "Обновление платформы: новые возможности",
    "Стратегия развития на следующий год",
    "Кейс: успешная маркетинговая кампания",
    "Тренды индустрии: прогноз экспертов",
    "Внутренний хакатон: результаты и выводы",
    "Гайд по эффективной коммуникации в команде"
]

CONTENTS = [
    "В этой статье мы рассмотрим основные аспекты запуска нового продукта на рынок. "
    "Наша команда провела масштабную работу по анализу целевой аудитории и конкурентного окружения. "
    "Результаты превзошли ожидания: конверсия выросла на 25% по сравнению с предыдущим кварталом.",

    "Подводя итоги прошедшего квартала, можно отметить значительный прогресс во всех ключевых метриках. "
    "Выручка увеличилась на 18%, количество активных пользователей выросло на 30%. "
    "Особую роль в этом сыграла внедрённая система аналитики и автоматизации процессов.",

    "Оптимизация рабочих процессов стала одной из приоритетных задач нашего отдела. "
    "Мы внедрили новые инструменты для управления проектами и автоматизации рутинных операций. "
    "Это позволило сократить время на выполнение задач на 40% и повысить удовлетворённость команды.",

    "На недавней встрече с ключевыми партнёрами были обсуждены планы совместного развития. "
    "Стороны договорились о расширении сотрудничества в области маркетинга и разработки новых продуктов. "
    "Ожидается, что первые результаты будут видны уже в следующем квартале.",

    "Мы рады представить масштабное обновление нашей платформы. "
    "Среди новых функций: улучшенный интерфейс, расширенные возможности аналитики, "
    "интеграция с популярными сервисами и повышенная безопасность данных пользователей.",

    "Стратегия развития на следующий год включает три ключевых направления: "
    "расширение продуктовой линейки, выход на новые рынки и усиление команды. "
    "Бюджет на развитие увеличен на 35% по сравнению с текущим годом.",

    "В данном кейсе мы подробно разбираем успешную маркетинговую кампанию, "
    "которая принесла более 10 000 лидов за месяц. "
    "Ключевыми факторами успеха стали таргетированная реклама, контент-маркетинг и работа с инфлюенсерами.",

    "Эксперты нашей отрасли подготовили прогноз основных трендов на ближайшие годы. "
    "Среди них: развитие искусственного интеллекта, персонализация пользовательского опыта, "
    "рост значимости видеоконтента и усиление внимания к защите данных.",

    "Внутренний хакатон собрал более 50 участников из разных отделов компании. "
    "За 48 часов команды разработали 12 прототипов новых продуктов и функций. "
    "Три лучших проекта получили финансирование для дальнейшей разработки.",

    "Эффективная коммуникация — основа успешной команды. "
    "В этом гайде мы собрали проверенные практики: от проведения продуктивных встреч "
    "до использования асинхронной коммуникации в распределённых командах."
]

CATEGORIES = [
    ("Новости", "news", "#3b82f6"),
    ("Аналитика", "analytics", "#10b981"),
    ("Маркетинг", "marketing", "#f59e0b"),
    ("Разработка", "development", "#8b5cf6"),
    ("Дизайн", "design", "#ec4899"),
]

USERS = [
    ("admin", "admin@mediahub.ru", "Администратор", "admin", "active"),
    ("editor_ivan", "ivan@mediahub.ru", "Иван Петров", "editor", "active"),
    ("editor_maria", "maria@mediahub.ru", "Мария Сидорова", "editor", "active"),
    ("volunteer_alex", "alex@mediahub.ru", "Алексей Козлов", "volunteer", "active"),
]

STATUSES = ["draft", "scheduled", "published", "published", "published", "failed"]  # published чаще


def ensure_categories(conn):
    """Убедиться, что категории существуют"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO categories (name, slug, color) VALUES (?, ?, ?)",
            CATEGORIES
        )
        conn.commit()
        print(f"Создано {len(CATEGORIES)} категорий")


def ensure_users(conn):
    """Убедиться, что пользователи существуют"""
    cursor = conn.cursor()
    
    test_users = [
        ("admin@mediahub.ru", "Администратор", "admin"),
        ("ivan@mediahub.ru", "Иван Петров", "editor"),
        ("maria@mediahub.ru", "Мария Сидорова", "editor"),
        ("alexey@mediahub.ru", "Алексей Козлов", "editor"),
        ("volunteer1@mediahub.ru", "Волонтёр 1", "editor"),
    ]
    
    created = 0
    for email, full_name, role in test_users:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                (email, password_hash, full_name, role)
            )
            created += 1
    
    if created > 0:
        conn.commit()
        print(f"Создано {created} пользователей")
    else:
        print("Все пользователи уже существуют")

def seed_posts():
    """Заполнить базу данных 10 случайными постами"""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        ensure_categories(conn)
        ensure_users(conn)
        
        cursor = conn.cursor()
        
        # Получаем ID категорий и пользователей
        cursor.execute("SELECT id FROM categories")
        category_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Проверяем, есть ли уже посты
        cursor.execute("SELECT COUNT(*) FROM posts")
        existing_count = cursor.fetchone()[0]
        
        posts_to_create = 10 - existing_count
        if posts_to_create <= 0:
            print(f"В базе уже есть {existing_count} постов (нужно 10). Пропускаем.")
            return
        
        print(f"В базе {existing_count} постов. Добавляем ещё {posts_to_create}...")
        
        # Генерируем посты
        posts = []
        now = datetime.now()
        
        for i in range(posts_to_create):
            title = TITLES[i % len(TITLES)]
            content = CONTENTS[i % len(CONTENTS)]
            status = random.choice(STATUSES)
            category_id = random.choice(category_ids)
            author_id = random.choice(user_ids)
            
            # Даты
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
            published_at = created_at + timedelta(hours=random.randint(1, 48)) if status == "published" else None
            scheduled_at = now + timedelta(days=random.randint(1, 14)) if status == "scheduled" else None
            updated_at = created_at + timedelta(hours=random.randint(1, 12))
            
            posts.append((
                title,
                content,
                status,
                category_id,
                None,  # template_id
                author_id,
                scheduled_at.strftime("%Y-%m-%d %H:%M:%S") if scheduled_at else None,
                published_at.strftime("%Y-%m-%d %H:%M:%S") if published_at else None,
                created_at.strftime("%Y-%m-%d %H:%M:%S"),
                updated_at.strftime("%Y-%m-%d %H:%M:%S")
            ))
        
        cursor.executemany(
            """INSERT INTO posts 
               (title, content, status, category_id, template_id, author_id, 
                scheduled_at, published_at, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",            posts
        )
        conn.commit()
        print(f"Успешно создано 10 постов!")
        
        # Выводим статистику
        cursor.execute("SELECT status, COUNT(*) FROM posts GROUP BY status")
        for status, count in cursor.fetchall():
            print(f"  - {status}: {count}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_posts()
