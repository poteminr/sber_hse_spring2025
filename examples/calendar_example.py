from datetime import datetime
from tools.calendar_tools import Calendar, Priority


CALENDAR_EXAMPLE = Calendar()


meetings_to_add = [
    ("Планирование спринта", "irina@sberbank.ru", 60, datetime(2025, 4, 28, 10, 0), Priority.HIGH),
    ("Синхронизация архитектуры", "roman@sberbank.ru", 45, datetime(2025, 4, 28, 13, 0), Priority.MEDIUM),
    ("Старт QA", "daria@sberbank.ru", 30, datetime(2025, 4, 29, 9, 30), Priority.MEDIUM),
    ("Обзор миграции данных", "svetlana@sberbank.ru", 60, datetime(2025, 4, 29, 11, 0), Priority.HIGH),
    ("UX‑воркшоп", "marina@sberbank.ru", 90, datetime(2025, 4, 30, 15, 0), Priority.MEDIUM),
    ("Рабочая группа по производительности API", "sergey@sberbank.ru", 60, datetime(2025, 5, 1, 10, 0), Priority.HIGH),
    ("Подготовка к аудиту безопасности", "ekaterina@sberbank.ru", 60, datetime(2025, 5, 2, 14, 0), Priority.HIGH),
    ("Демонстрация для стейкхолдеров", "anastasia@sberbank.ru", 90, datetime(2025, 5, 5, 11, 0), Priority.HIGH),
    ("Улучшения CI/CD", "alexey@sberbank.ru", 45, datetime(2025, 5, 6, 16, 0), Priority.MEDIUM),
    ("Обновление реестра рисков", "olga@sberbank.ru", 30, datetime(2025, 5, 8, 17, 0), Priority.MEDIUM),
]


for topic, organizer, duration, start_dt, prio in meetings_to_add:
    CALENDAR_EXAMPLE.add_meeting(topic, organizer, duration, start_dt, prio)    