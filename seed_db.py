import json
from datetime import datetime, timedelta
from database import SessionLocal, engine
from models import Base, User, Category, Template, Post, SocialAccount, Publication, Analytics

def seed_data():
    db = SessionLocal()
    try:
        # 1. Создаем пользователя (админ)
        admin = User(
            email="admin@mediahub.ru",
            password_hash="hash_here", # В реальном приложении здесь будет bcrypt
            full_name="Иван Иванов",
            role="admin"
        )
        db.add(admin)
        
        # 2. Категории
        cat_event = Category(name="Мероприятия", slug="events", color="#3b82f6")
        cat_grant = Category(name="Гранты", slug="grants", color="#10b981")
        cat_news = Category(name="Новости", slug="news", color="#f59e0b")
        db.add_all([cat_event, cat_grant, cat_news])
        
        # 3. Шаблоны
        tpl_announcement = Template(
            name="Анонс мероприятия",
            content_template="📢 {title}\n\n📅 {date}\n📍 {location}\n\n{description}",
            variables=json.dumps(["title", "date", "location", "description"])
        )
        db.add(tpl_announcement)
        
        # 4. Соцсети
        vk_acc = SocialAccount(platform="vk", account_name="Молодежный Центр ВК", is_active=True)
        tg_acc = SocialAccount(platform="telegram", account_name="МЦ Телеграм", is_active=True)
        db.add_all([vk_acc, tg_acc])
        
        db.commit() # Сохраняем, чтобы получить ID

        # 5. Посты
        post1 = Post(
            title="Хакатон 2024",
            content="Приглашаем всех на весенний хакатон!",
            status="published",
            category_id=cat_event.id,
            author_id=admin.id,
            published_at=datetime.utcnow() - timedelta(days=2)
        )
        
        post2 = Post(
            title="Грантовый конкурс",
            content="Успей подать заявку на грант до конца месяца.",
            status="scheduled",
            category_id=cat_grant.id,
            author_id=admin.id,
            scheduled_at=datetime.utcnow() + timedelta(days=1)
        )
        db.add_all([post1, post2])
        db.commit()

        # 6. Публикации и Аналитика для первого поста
        pub_vk = Publication(
            post_id=post1.id,
            social_account_id=vk_acc.id,
            status="published",
            published_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(pub_vk)
        db.commit()

        analytics = Analytics(
            publication_id=pub_vk.id,
            views=1250,
            reactions=85,
            comments=12,
            shares=5,
            engagement_rate=7.5
        )
        db.add(analytics)
        
        db.commit()
        print("Тестовые данные успешно добавлены!")

    except Exception as e:
        print(f"Ошибка при заполнении: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
