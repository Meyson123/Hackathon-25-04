-- Схема базы данных для проекта "Медиахаб"
-- Стек: SQLite 3

-- 1. Пользователи
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT CHECK(role IN ('admin', 'editor', 'observer')) DEFAULT 'editor',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Категории контента
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#3b82f6', -- HEX код для фронтенда
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Шаблоны постов
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    content_template TEXT NOT NULL, -- Текст с переменными типа {title}, {date}
    variables TEXT, -- JSON строка со списком доступных переменных
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. Посты
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    status TEXT CHECK(status IN ('draft', 'scheduled', 'published', 'failed')) DEFAULT 'draft',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    scheduled_at DATETIME, -- Когда опубликовать
    published_at DATETIME, -- Когда фактически опубликован
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Медиафайлы
CREATE TABLE media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_type TEXT, -- image/jpeg, video/mp4 и т.д.
    file_size INTEGER,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Аккаунты социальных сетей
CREATE TABLE social_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL, -- 'vk', 'telegram'
    account_name TEXT,
    external_id TEXT, -- ID в самой соцсети
    access_token TEXT,
    is_active INTEGER DEFAULT 1, -- 1 = true, 0 = false
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. Публикации (связь поста с конкретной соцсетью)
CREATE TABLE publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    social_account_id INTEGER REFERENCES social_accounts(id) ON DELETE CASCADE,
    external_post_id TEXT, -- ID поста в соцсети после публикации
    status TEXT CHECK(status IN ('scheduled', 'published', 'failed')) DEFAULT 'scheduled',
    error_message TEXT,
    published_at DATETIME
);

-- 8. Аналитика (метрики)
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publication_id INTEGER REFERENCES publications(id) ON DELETE CASCADE,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate REAL -- ER в %
);

-- Индексы для ускорения поиска
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_scheduled_at ON posts(scheduled_at);
CREATE INDEX idx_analytics_publication_id ON analytics(publication_id);
