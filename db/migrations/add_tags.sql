-- Миграция: Добавление системы тегов
-- Выполнить: sqlite3 db/mediahub.db < db/migrations/add_tags.sql

-- Создание таблицы тегов
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы связи постов с тегами
CREATE TABLE IF NOT EXISTS post_tags (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);

-- Вставка предопределённых тегов
INSERT OR IGNORE INTO tags (name) VALUES
    ('#ШестойБит'),
    ('#ШестойКод'),
    ('#ШеТехнологии'),
    ('#ШеПрограммист'),
    ('#ШеАйтишник'),
    ('#ШеХакатон'),
    ('#ШеРазработка'),
    ('#ШеПитон'),
    ('#МолодежьВКоде'),
    ('#ПрожаркаКода'),
    ('#ITМолодежка'),
    ('#КодДляСвоих'),
    ('#ШестьГигов'),
    ('#ШестойЯзыкПрограммирования'),
    ('#ХакатонШестогоОкруга'),
    ('#ШеБаг'),
    ('#ШеФикс'),
    ('#ШеДебаг'),
    ('#GitШе');
