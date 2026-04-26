"""
Модуль для синхронизации мероприятий с Google Calendar API (публичный календарь)
"""
import os
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleCalendarSync:
    """Класс для синхронизации событий с Google Calendar (публичный)"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.api_key = os.getenv("GOOGLE_CALENDAR_API_KEY")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        
        if not self.api_key:
            raise ValueError("GOOGLE_CALENDAR_API_KEY не найден в переменных окружения")
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Создает подключение к базе данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_events_from_google(self, 
                                 time_min: Optional[str] = None,
                                 time_max: Optional[str] = None,
                                 max_results: int = 250) -> List[Dict]:
        """
        Получает события из Google Calendar API
        
        Args:
            time_min: Начало периода в формате ISO 8601
            time_max: Конец периода в формате ISO 8601
            max_results: Максимальное количество событий
            
        Returns:
            Список событий из Google Calendar
        """
        # Если период не указан, берем события на год вперед
        if not time_min:
            time_min = datetime.now().isoformat() + 'Z'
        if not time_max:
            time_max = (datetime.now() + timedelta(days=365)).isoformat() + 'Z'
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events"
        
        params = {
            'key': self.api_key,
            'timeMin': time_min,
            'timeMax': time_max,
            'maxResults': max_results,
            'singleEvents': 'true',
            'orderBy': 'startTime'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении событий из Google Calendar: {e}")
            return []
    
    def parse_event(self, google_event: Dict) -> Dict:
        """
        Парсит событие из формата Google Calendar в формат БД
        
        Args:
            google_event: Событие из Google Calendar API
            
        Returns:
            Словарь с данными события для БД
        """
        event_id = google_event.get('id', '')
        title = google_event.get('summary', 'Без названия')
        description = google_event.get('description', '')
        location = google_event.get('location', '')
        
        # Определяем дату и время начала/конца
        start_data = google_event.get('start', {})
        end_data = google_event.get('end', {})
        
        # Проверяем, событие на весь день или с конкретным временем
        all_day = 'date' in start_data
        
        if all_day:
            # Событие на весь день
            start_datetime = start_data.get('date', '')
            end_datetime = end_data.get('date', '')
        else:
            # Событие с конкретным временем
            start_datetime = start_data.get('dateTime', '')
            end_datetime = end_data.get('dateTime', '')
        
        return {
            'google_event_id': event_id,
            'title': title,
            'description': description,
            'location': location,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'all_day': 1 if all_day else 0
        }
    
    def save_event_to_db(self, event_data: Dict) -> bool:
        """
        Сохраняет или обновляет событие в базе данных
        
        Args:
            event_data: Данные события
            
        Returns:
            True если успешно, иначе False
        """
        conn = self.get_db_connection()
        try:
            # Проверяем, существует ли событие
            existing = conn.execute(
                "SELECT id FROM events WHERE google_event_id = ?",
                (event_data['google_event_id'],)
            ).fetchone()
            
            if existing:
                # Обновляем существующее событие
                conn.execute("""
                    UPDATE events 
                    SET title = ?, description = ?, location = ?,
                        start_datetime = ?, end_datetime = ?, all_day = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE google_event_id = ?
                """, (
                    event_data['title'],
                    event_data['description'],
                    event_data['location'],
                    event_data['start_datetime'],
                    event_data['end_datetime'],
                    event_data['all_day'],
                    event_data['google_event_id']
                ))
                logger.info(f"Обновлено событие: {event_data['title']}")
            else:
                # Создаем новое событие
                conn.execute("""
                    INSERT INTO events 
                    (google_event_id, title, description, location, start_datetime, end_datetime, all_day)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data['google_event_id'],
                    event_data['title'],
                    event_data['description'],
                    event_data['location'],
                    event_data['start_datetime'],
                    event_data['end_datetime'],
                    event_data['all_day']
                ))
                logger.info(f"Добавлено новое событие: {event_data['title']}")
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении события в БД: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def sync_events(self, time_min: Optional[str] = None, 
                    time_max: Optional[str] = None) -> Dict[str, int]:
        """
        Синхронизирует события из Google Calendar с базой данных
        
        Args:
            time_min: Начало периода
            time_max: Конец периода
            
        Returns:
            Словарь со статистикой синхронизации
        """
        logger.info("Начинаем синхронизацию с Google Calendar...")
        
        # Получаем события из Google Calendar
        google_events = self.fetch_events_from_google(time_min, time_max)
        
        stats = {
            'total': len(google_events),
            'added': 0,
            'updated': 0,
            'failed': 0
        }
        
        for google_event in google_events:
            try:
                event_data = self.parse_event(google_event)
                
                # Проверяем, существует ли событие
                conn = self.get_db_connection()
                existing = conn.execute(
                    "SELECT id FROM events WHERE google_event_id = ?",
                    (event_data['google_event_id'],)
                ).fetchone()
                conn.close()
                
                if existing:
                    stats['updated'] += 1
                else:
                    stats['added'] += 1
                
                # Сохраняем в БД
                if self.save_event_to_db(event_data):
                    continue
                else:
                    stats['failed'] += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке события: {e}")
                stats['failed'] += 1
        
        logger.info(f"Синхронизация завершена: {stats}")
        return stats
    
    def get_events_for_month(self, year: int, month: int) -> List[Dict]:
        """
        Получает события за указанный месяц
        
        Args:
            year: Год
            month: Месяц (1-12)
            
        Returns:
            Список событий
        """
        conn = self.get_db_connection()
        try:
            # Формируем начало и конец месяца
            start_date = datetime(year, month, 1).strftime('%Y-%m-%d 00:00:00')
            if month == 12:
                end_date = datetime(year + 1, 1, 1).strftime('%Y-%m-%d 00:00:00')
            else:
                end_date = datetime(year, month + 1, 1).strftime('%Y-%m-%d 00:00:00')
            
            rows = conn.execute("""
                SELECT * FROM events 
                WHERE start_datetime >= ? AND start_datetime < ?
                ORDER BY start_datetime
            """, (start_date, end_date)).fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_events_for_date(self, date: str) -> List[Dict]:
        """
        Получает события на конкретную дату
        
        Args:
            date: Дата в формате YYYY-MM-DD
            
        Returns:
            Список событий
        """
        conn = self.get_db_connection()
        try:
            start_datetime = f"{date} 00:00:00"
            end_datetime = f"{date} 23:59:59"
            
            rows = conn.execute("""
                SELECT * FROM events 
                WHERE start_datetime >= ? AND start_datetime <= ?
                ORDER BY start_datetime
            """, (start_datetime, end_datetime)).fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()


def sync_calendar_events(db_path: str) -> Dict[str, int]:
    """
    Функция для запуска синхронизации (используется в роутах)
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        Статистика синхронизации
    """
    try:
        sync = GoogleCalendarSync(db_path)
        return sync.sync_events()
    except Exception as e:
        logger.error(f"Ошибка при синхронизации: {e}")
        return {'total': 0, 'added': 0, 'updated': 0, 'failed': 1}


def init_calendar(db_path: str) -> bool:
    """
    Инициализация и синхронизация календаря при запуске сервера
    
    Args:
        db_path: Путь к базе данных
        
    Returns:
        True если успешно, иначе False
    """
    try:
        logger.info("🔄 Инициализация Google Calendar...")
        stats = sync_calendar_events(db_path)
        
        if stats['failed'] == 0:
            logger.info(f"✅ Календарь успешно синхронизирован: {stats['added']} новых, {stats['updated']} обновлено")
            return True
        else:
            logger.warning(f"⚠️ Синхронизация завершена с ошибками: {stats['failed']} неудач")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации календаря: {e}")
        return False
