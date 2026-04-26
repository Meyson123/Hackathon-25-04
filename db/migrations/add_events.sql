-- Таблица мероприятий из Google Calendar
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_event_id TEXT UNIQUE NOT NULL,  -- ID события из Google Calendar
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    all_day INTEGER DEFAULT 0,  -- 1 = событие на весь день
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_events_start_datetime ON events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_events_end_datetime ON events(end_datetime);
CREATE INDEX IF NOT EXISTS idx_events_google_event_id ON events(google_event_id);
