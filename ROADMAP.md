# Роадмап и структура сайта «Медиахаб для молодёжного центра»

## 1. Карта сайта (Site Map)

```
Медиахаб
├── Главная страница (Landing)
│   ├── Анонсы мероприятий
│   ├── Лента новостей
│   ├── Календарь событий
│   └── Быстрая регистрация волонтёра
│
├── /auth - Авторизация
│   ├── Вход
│   ├── Регистрация
│   └── Восстановление пароля
│
├── /dashboard - Панель управления (для авторизованных)
│   │
│   ├── /smm - Панель SMM-менеджера
│   │   ├── /calendar - Календарь контента
│   │   ├── /posts - Управление постами
│   │   │   ├── Создание поста
│   │   │   ├── Редактирование
│   │   │   ├── Шаблоны
│   │   │   └── Модерация (посты волонтёров)
│   │   ├── /events - График мероприятий
│   │   │   ├── Создание мероприятия
│   │   │   ├── Редактирование
│   │   │   └── Архив событий
│   │   ├── /analytics - Аналитика
│   │   │   ├── Обзор дашборда
│   │   │   ├── Статистика просмотров
│   │   │   ├── Отчёт активности пользователей
│   │   │   └── Экспорт отчётов
│   │   ├── /comments - Модерация комментариев
│   │   │   ├── Очередь модерации
│   │   │   ├── Ответы на комментарии
│   │   │   └── История действий
│   │   ├── /polls - Опросы и голосования
│   │   │   ├── Создать опрос
│   │   │   ├── Активные опросы
│   │   │   ├── Результаты
│   │   │   └── Конкурсы
│   │   ├── /seo - Настройки SEO
│   │   │   ├── Мета-теги страниц
│   │   │   ├── Open Graph
│   │   │   └── Sitemap
│   │   └── /settings - Настройки
│   │       ├── Контактная информация
│   │       └── Правила сайта
│   │
│   ├── /admin - Панель администратора
│   │   ├── /users - Управление пользователями
│   │   │   ├── Список пользователей
│   │   │   ├── Назначение ролей
│   │   │   ├── Блокировка/удаление
│   │   │   └── Выдача доступа менеджерам
│   │   ├── /events - Редакция графика мероприятий
│   │   │   ├── Все мероприятия
│   │   │   ├── Создание/редактирование
│   │   │   └── Удаление
│   │   ├── /categories - Управление категориями
│   │   │   ├── Список категорий
│   │   │   ├── Создание категории
│   │   │   └── Управление тегами
│   │   ├── /analytics - Аналитика сайта
│   │   │   ├── Общая статистика
│   │   │   ├── Посетители
│   │   │   ├── Популярные страницы
│   │   │   └── Отчёт активности пользователей
│   │   ├── /access - Управление доступом
│   │   │   ├── Роли и права
│   │   │   ├── Логи доступа
│   │   │   └── API ключи
│   │   └── /settings - Настройки сайта
│   │       ├── Контактная информация
│   │       ├── Правила сайта
│   │       ├── Общие настройки
│   │       └── Интеграции
│   │
│   └── /volunteer - Панель волонтёра
│       ├── /profile - Профиль волонтёра
│       │   ├── Личные данные
│       │   ├── История активности
│       │   ├── Достижения и бейджи
│       │   └── Настройки уведомлений
│       ├── /events - Мероприятия
│       │   ├── Доступные мероприятия
│       │   ├── Мои мероприятия
│       │   ├── Присоединиться к событию
│       │   └── Календарь участия
│       ├── /content - Создание контента
│       │   ├── Загрузить фото/видео
│       │   ├── Загрузить документы
│       │   ├── Создать пост
│       │   ├── Черновики
│       │   └── На модерации
│       ├── /leaderboard - Лидерборд
│       │   ├── Рейтинг волонтёров
│       │   ├── Моя позиция
│       │   ├── История изменений
│       │   └── Награды
│       └── /notifications - Уведомления
│           ├── Системные уведомления
│           ├── Уведомления о мероприятиях
│           └── Уведомления о контенте
│
├── /events - Публичные мероприятия
│   ├── Календарь событий
│   ├── Карта мероприятий
│   ├── Детальная страница мероприятия
│   └── Архив прошедших
│
├── /news - Новости
│   ├── Лента новостей
│   ├── Категории
│   └── Детальная страница новости
│
├── /volunteers - Волонтёрство
│   ├── Стать волонтёром
│   ├── О программе
│   ├── Лидерборд
│   └── FAQ
│
├── /about - О нас
│   ├── О молодёжном центре
│   ├── Команда
│   ├── Контакты
│   └── Правила сайта
│
└── /404 - Страница не найдена
```

---

## 2. Матрица доступа по ролям

| Функционал | Волонтёр | SMM-менеджер | Администратор |
|------------|----------|--------------|---------------|
| **Просмотр контента** | ✅ | ✅ | ✅ |
| **Создание постов** | ✅ (ограничено) | ✅ | ✅ |
| **Редактирование постов** | ⚠️ (с разрешения) | ✅ | ✅ |
| **Удаление постов** | ❌ | ✅ (свои) | ✅ |
| **Публикация постов** | ❌ | ✅ | ✅ |
| **Модерация контента** | ❌ | ✅ | ✅ |
| **Календарь мероприятий** | ✅ (просмотр) | ✅ (редакция) | ✅ (редакция) |
| **Присоединение к событиям** | ✅ | ✅ | ✅ |
| **Загрузка медиафайлов** | ✅ | ✅ | ✅ |
| **Аналитика просмотров** | ❌ | ✅ | ✅ |
| **Аналитика сайта** | ❌ | ❌ | ✅ |
| **Модерация комментариев** | ❌ | ✅ | ✅ |
| **Ответы на комментарии** | ✅ (свои) | ✅ | ✅ |
| **Создание опросов** | ❌ | ✅ | ✅ |
| **Проведение конкурсов** | ❌ | ✅ | ✅ |
| **Настройка SEO** | ❌ | ✅ | ❌ |
| **Обновление контактов** | ❌ | ✅ | ✅ |
| **Обновление правил** | ❌ | ✅ | ✅ |
| **Управление пользователями** | ❌ | ❌ | ✅ |
| **Назначение ролей** | ❌ | ❌ | ✅ |
| **Удаление пользователей** | ❌ | ❌ | ✅ |
| **Управление категориями** | ❌ | ❌ | ✅ |
| **Управление тегами** | ❌ | ❌ | ✅ |
| **Выдача доступа** | ❌ | ❌ | ✅ |
| **Лидерборд** | ✅ (просмотр) | ✅ (просмотр) | ✅ (просмотр+редакция) |
| **Достижения/уровни** | ✅ | ✅ | ✅ |

---

## 3. Детальное описание ролей

### 3.1. SMM-менеджер

**Основные задачи:**

#### 📅 График мероприятий
- Создание и редактирование мероприятий
- Установка даты, времени, места
- Загрузка афиш и материалов
- Управление статусами (анонс, идёт, завершено)
- Архивирование прошедших событий

#### ✏️ Редакция постов
- Создание постов по шаблонам
- Редактирование черновиков
- Планирование публикации
- Кросс-постинг в соцсети
- Модерация постов волонтёров

#### 📊 Аналитика просмотров
- Просмотр статистики по постам
- Анализ вовлечённости
- Отчёты за период
- Экспорт в PDF/Excel

#### 💬 Модерация комментариев
- Очередь комментариев на модерацию
- Одобрение/отклонение
- Ответы на комментарии
- Блокировка пользователей

#### 📦 Архивирование событий
- Перенос завершённых мероприятий в архив
- Хранение материалов
- Быстрый доступ к истории

#### 🗳️ Опросы и голосования
- Создание опросов
- Настройка вариантов ответов
- Просмотр результатов
- Проведение конкурсов

#### 📈 Отчёт активности пользователей
- Статистика по пользователям
- Активность за период
- Топ активных участников
- Графики динамики

#### 🔍 Настройка SEO
- Мета-теги (title, description)
- Open Graph для соцсетей
- Sitemap.xml
- Robots.txt

#### 📞 Обновление контактов
- Телефоны
- Email
- Адрес
- Социальные сети

#### 📜 Правила сайта
- Редактирование правил
- Политика конфиденциальности
- Условия использования

---

### 3.2. Администратор

**Основные задачи:**

#### 📅 Редакция графика мероприятий
- Полный контроль над мероприятиями
- Создание/редактирование/удаление
- Управление доступом

#### 📊 Аналитика сайта
- Общая статистика посещений
- Популярные страницы
- Источники трафика
- Поведение пользователей
- Отчёт активности пользователей

#### 🔐 Выдача доступа для менеджеров
- Создание аккаунтов SMM-менеджеров
- Назначение прав доступа
- Управление API ключами

#### 🏷️ Управление категориями и тегами
- Создание категорий
- Редактирование названий
- Управление цветами
- Создание тегов
- Объединение/удаление

#### 👥 Управление пользователями
- Список всех пользователей
- Просмотр профилей
- Блокировка/разблокировка
- Удаление аккаунтов
- История действий

#### 🎭 Назначение ролей
- Изменение ролей пользователей
- Волонтёр → SMM-менеджер
- SMM-менеджер → Администратор
- Отзыв прав доступа

#### 📈 Отчёт активности пользователей
- Комплексная аналитика
- Сравнение периодов
- Экспорт данных
- Кастомные отчёты

#### 📞 Обновление контактной информации
- Редактирование контактов
- Добавление новых
- Удаление устаревших

#### 📜 Правила сайта
- Полный контроль над правилами
- Версионирование изменений
- Публикация обновлений

---

### 3.3. Волонтёр

**Основные задачи:**

#### 🎯 Присоединение к мероприятиям
- Просмотр доступных событий
- Регистрация на участие
- Календарь моих мероприятий
- Отмена участия

#### 📸 Загрузка медиафайлов
- Фото с мероприятий
- Видео материалы
- Документы
- Массовая загрузка

#### ✍️ Создание постов
- Короткие описания
- Отчёты с мероприятий
- Импровизации
- Использование шаблонов

#### ⭐ Система уровней
- Начальный уровень (0-50 баллов)
- Продвинутый (51-200 баллов)
- Опытный (201-500 баллов)
- Эксперт (500+ баллов)

**Привилегии по уровням:**
- **Начальный:** Создание постов (на модерации)
- **Продвинутый:** Редактирование своих постов
- **Опытный:** Публикация без модерации
- **Эксперт:** Создание шаблонов, наставничество

#### ✏️ Редактирование постов
- Редактирование своих постов
- Запрос разрешения на редактирование
- История изменений
- Версионирование

#### 🏆 Лидерборд
- Рейтинг волонтёров
- Моя позиция
- История изменений
- Награды и достижения

**Система баллов:**
- +10 баллов за участие в мероприятии
- +5 баллов за загрузку фото
- +15 баллов за создание поста
- +20 баллов за одобренный пост
- +5 баллов за ответ на комментарий
- +50 баллов за конкурс/опрос

---

## 4. Роадмап разработки

### Фаза 1: Фундамент (День 1)
- [ ] Настройка проекта (Next.js + FastAPI)
- [ ] База данных и миграции
- [ ] Система авторизации и ролей
- [ ] Базовый UI фреймворк

### Фаза 2: Панель SMM-менеджера (День 1-2)
- [ ] Календарь контента
- [ ] CRUD постов
- [ ] Система шаблонов
- [ ] Загрузка медиафайлов
- [ ] Модерация контента

### Фаза 3: Панель волонтёра (День 2)
- [ ] Профиль волонтёра
- [ ] Присоединение к мероприятиям
- [ ] Создание контента
- [ ] Система уровней
- [ ] Лидерборд

### Фаза 4: Панель администратора (День 2-3)
- [ ] Управление пользователями
- [ ] Назначение ролей
- [ ] Управление категориями
- [ ] Аналитика сайта
- [ ] Настройки

### Фаза 5: Интеграции (День 3)
- [ ] VK API
- [ ] Telegram Bot API
- [ ] Автопубликация
- [ ] Сбор статистики

### Фаза 6: Дополнительный функционал (День 3-4)
- [ ] Опросы и конкурсы
- [ ] Модерация комментариев
- [ ] SEO настройки
- [ ] Уведомления

### Фаза 7: Публичная часть (День 4)
- [ ] Главная страница
- [ ] Календарь мероприятий
- [ ] Лента новостей
- [ ] Страница волонтёрства

### Фаза 8: Полировка (День 4)
- [ ] Тестирование сценариев
- [ ] Моковые данные
- [ ] Документация
- [ ] Презентация

---

## 5. Приоритеты MVP

### Критически важно (P0):
1. Авторизация и роли
2. CRUD постов (SMM)
3. Календарь контента
4. Присоединение к мероприятиям (Волонтёр)
5. Загрузка медиафайлов
6. Базовая аналитика

### Важно (P1):
7. Система шаблонов
8. Модерация контента
9. Лидерборд
10. Управление пользователями (Админ)
11. Опросы
12. Комментарии

### Желательно (P2):
13. SEO настройки
14. Уведомления
15. Экспорт отчётов
16. Интеграции с соцсетями

---

## 6. Техническая архитектура

### Frontend (Next.js 14)
```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── smm/
│   │   │   ├── calendar/
│   │   │   │   └── page.tsx
│   │   │   ├── posts/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── create/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx
│   │   │   ├── events/
│   │   │   │   └── page.tsx
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx
│   │   │   ├── comments/
│   │   │   │   └── page.tsx
│   │   │   ├── polls/
│   │   │   │   └── page.tsx
│   │   │   ├── seo/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   ├── admin/
│   │   │   ├── users/
│   │   │   │   └── page.tsx
│   │   │   ├── events/
│   │   │   │   └── page.tsx
│   │   │   ├── categories/
│   │   │   │   └── page.tsx
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx
│   │   │   ├── access/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   └── volunteer/
│   │       ├── profile/
│   │       │   └── page.tsx
│   │       ├── events/
│   │       │   └── page.tsx
│   │       ├── content/
│   │       │   └── page.tsx
│   │       ├── leaderboard/
│   │       │   └── page.tsx
│   │       └── notifications/
│   │           └── page.tsx
│   ├── events/
│   │   └── page.tsx
│   ├── news/
│   │   └── page.tsx
│   ├── volunteers/
│   │   └── page.tsx
│   ├── about/
│   │   └── page.tsx
│   ├── page.tsx
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── calendar.tsx
│   │   └── ...
│   ├── dashboard/
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── ...
│   ├── smm/
│   │   ├── post-form.tsx
│   │   ├── post-card.tsx
│   │   └── ...
│   ├── volunteer/
│   │   ├── profile-card.tsx
│   │   └── ...
│   └── admin/
│       ├── user-table.tsx
│       └── ...
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   └── utils.ts
├── hooks/
│   ├── useAuth.ts
│   └── usePosts.ts
├── types/
│   ├── user.ts
│   ├── post.ts
│   └── event.ts
└── styles/
    └── globals.css
```

### Backend (FastAPI + Python)
```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── event.py
│   │   ├── category.py
│   │   ├── comment.py
│   │   ├── poll.py
│   │   └── analytics.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── event.py
│   │   └── ...
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── posts.py
│   │   │   ├── events.py
│   │   │   ├── categories.py
│   │   │   ├── comments.py
│   │   │   ├── polls.py
│   │   │   ├── analytics.py
│   │   │   └── social.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── config.py
│   │   └── permissions.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── post_service.py
│   │   ├── event_service.py
│   │   ├── social_service.py
│   │   ├── analytics_service.py
│   │   └── notification_service.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── scheduled_tasks.py
│   └── utils/
│       ├── __init__.py
│       ├── templates.py
│       └── helpers.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_posts.py
│   └── ...
├── requirements.txt
├── alembic.ini
└── .env.example
```

### Database Schema
```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'volunteer',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    points INTEGER DEFAULT 0,
    level VARCHAR(50) DEFAULT 'beginner',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    category_id INTEGER REFERENCES categories(id),
    author_id INTEGER REFERENCES users(id),
    template_id INTEGER REFERENCES templates(id),
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date TIMESTAMP NOT NULL,
    location VARCHAR(255),
    image_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'announced',
    max_participants INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event Participants
CREATE TABLE event_participants (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'registered',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, user_id)
);

-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Templates
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content_template TEXT NOT NULL,
    variables JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    parent_id INTEGER REFERENCES comments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Polls
CREATE TABLE polls (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    ends_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Poll Options
CREATE TABLE poll_options (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(id),
    text VARCHAR(255) NOT NULL,
    votes_count INTEGER DEFAULT 0
);

-- Poll Votes
CREATE TABLE poll_votes (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(id),
    option_id INTEGER REFERENCES poll_options(id),
    user_id INTEGER REFERENCES users(id),
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(poll_id, user_id)
);

-- Social Publications
CREATE TABLE social_publications (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    platform VARCHAR(50) NOT NULL,
    platform_post_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    published_at TIMESTAMP,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    platform VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievements
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    points INTEGER DEFAULT 0,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. API Endpoints

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
```

### Users
```
GET    /api/v1/users
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}
DELETE /api/v1/users/{id}
PATCH  /api/v1/users/{id}/role
GET    /api/v1/users/{id}/activity
```

### Posts
```
GET    /api/v1/posts
POST   /api/v1/posts
GET    /api/v1/posts/{id}
PATCH  /api/v1/posts/{id}
DELETE /api/v1/posts/{id}
POST   /api/v1/posts/{id}/publish
POST   /api/v1/posts/{id}/schedule
GET    /api/v1/posts/calendar
```

### Events
```
GET    /api/v1/events
POST   /api/v1/events
GET    /api/v1/events/{id}
PATCH  /api/v1/events/{id}
DELETE /api/v1/events/{id}
POST   /api/v1/events/{id}/join
DELETE /api/v1/events/{id}/leave
GET    /api/v1/events/{id}/participants
```

### Categories
```
GET    /api/v1/categories
POST   /api/v1/categories
GET    /api/v1/categories/{id}
PATCH  /api/v1/categories/{id}
DELETE /api/v1/categories/{id}
```

### Templates
```
GET    /api/v1/templates
POST   /api/v1/templates
GET    /api/v1/templates/{id}
PATCH  /api/v1/templates/{id}
DELETE /api/v1/templates/{id}
POST   /api/v1/templates/{id}/render
```

### Comments
```
GET    /api/v1/posts/{post_id}/comments
POST   /api/v1/posts/{post_id}/comments
GET    /api/v1/comments/pending
PATCH  /api/v1/comments/{id}/approve
PATCH  /api/v1/comments/{id}/reject
DELETE /api/v1/comments/{id}
```

### Polls
```
GET    /api/v1/polls
POST   /api/v1/polls
GET    /api/v1/polls/{id}
PATCH  /api/v1/polls/{id}
DELETE /api/v1/polls/{id}
POST   /api/v1/polls/{id}/vote
GET    /api/v1/polls/{id}/results
```

### Analytics
```
GET    /api/v1/analytics/dashboard
GET    /api/v1/analytics/posts
GET    /api/v1/analytics/users
GET    /api/v1/analytics/export
```

### Social Media
```
POST   /api/v1/social/publish
GET    /api/v1/social/status/{id}
GET    /api/v1/social/stats
```

### Leaderboard
```
GET    /api/v1/leaderboard
GET    /api/v1/leaderboard/me
```

---

## Заключение

Данный роадмап обеспечивает полную структуру веб-приложения «Медиахаб для молодёжного центра» с чётким разделением по ролям, приоритетами разработки и технической архитектурой.