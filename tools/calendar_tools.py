from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Set, Dict, Any
from smolagents import Tool
import io
import sys


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Meeting:
    """Представляет одну встречу в календаре."""
    def __init__(
        self, 
        id: int, 
        topic: str, 
        organizer: str, 
        duration: int, 
        start_time: datetime, 
        priority: Priority = Priority.MEDIUM
    ):
        """Инициализирует объект Meeting.

        Args:
            id: Уникальный идентификатор встречи.
            topic: Тема встречи.
            organizer: Организатор встречи.
            duration: Длительность встречи в минутах.
            start_time: Время начала встречи (объект datetime).
            priority: Приоритет встречи (по умолчанию MEDIUM).
        """
        self.id = id
        self.topic = topic
        self.organizer = organizer
        self.duration = timedelta(minutes=duration)
        self.start_time = start_time
        self.priority = priority

    @property
    def end_time(self) -> datetime:
        """Вычисляет время окончания встречи."""
        return self.start_time + self.duration

    def __str__(self) -> str:

        return (f"Встреча #{self.id}: «{self.topic}»\n"
                f"Организатор: {self.organizer}\n"
                f"Начало: {self.start_time}, Конец: {self.end_time}, Длительность: {self.duration}\n"
                f"Приоритет: {self.priority.name}")


class Calendar:
    """Управляет списком встреч и настройками рабочего времени."""
    def __init__(self):
        """Инициализирует календарь."""
        self.meetings: List[Meeting] = []
        self.next_id: int = 1
        
        self.working_days: Set[int] = {0, 1, 2, 3, 4}
        
        self.work_start_hour: int = 9  
        self.work_end_hour: int = 18 

    def set_working_days(self, days: Set[int]) -> None:
        """Устанавливает рабочие дни недели.

        Args:
            days: Множество целых чисел, представляющих рабочие дни (0=Пн, 6=Вс).
        """
        self.working_days = days

    def set_working_hours(self, start_hour: int, end_hour: int) -> None:
        """Устанавливает рабочие часы.

        Args:
            start_hour: Час начала рабочего дня (0-23).
            end_hour: Час окончания рабочего дня (0-24).

        Raises:
            ValueError: Если указаны некорректные часы.
        """
        if 0 <= start_hour < end_hour <= 24:
            self.work_start_hour = start_hour
            self.work_end_hour = end_hour
        else:
            raise ValueError("Некорректные рабочие часы")

    def is_working_time(self, time: datetime) -> bool:
        """Проверяет, является ли указанное время рабочим.

        Args:
            time: Время для проверки (объект datetime).

        Returns:
            True, если время рабочее, иначе False.
        """
        if time.weekday() not in self.working_days:
            return False
            
        return self.work_start_hour <= time.hour < self.work_end_hour

    def add_meeting(
        self, 
        topic: str, 
        organizer: str, 
        duration: int, 
        start_time: datetime, 
        priority: Priority = Priority.MEDIUM
    ) -> bool:
        """Добавляет новую встречу, если время свободно.

        Args:
            topic: Тема встречи.
            organizer: Организатор встречи.
            duration: Длительность встречи в минутах.
            start_time: Желаемое время начала встречи.
            priority: Приоритет встречи.

        Returns:
            True, если встреча успешно добавлена, иначе False (если время занято).
        """
        # if start_time <= datetime.now():
        #     raise ValueError(f"Невозможно добавить встречу в прошлом. Укажите время в будущем. Сегодня {datetime.now().strftime('%Y-%m-%d')}")
            
        free = True
        for m in self.meetings:
            if start_time < m.end_time and m.start_time < (start_time + timedelta(minutes=duration)):
                free = False
                break
        
        if free:
            new_meeting = Meeting(self.next_id, topic, organizer, duration, start_time, priority)
            self.meetings.append(new_meeting)
            self.next_id += 1
            return True
        else:
            raise ValueError("Запрошенное время занято.")

    def remove_meeting(self, id: int) -> bool:
        """Удаляет встречу по её идентификатору.

        Args:
            id: Идентификатор встречи для удаления.

        Returns:
            True, если встреча найдена и удалена, иначе False.
        """
        for m in self.meetings:
            if m.id == id:
                self.meetings.remove(m)
                print(f"Встреча {id} удалена")
                return True
        print(f"Встреча {id} не найдена")
        return False

    def list_meetings(self) -> None:
        """Выводит список всех встреч в стандартный вывод."""
        if not self.meetings:
            print("Календарь пуст")
        for m in self.meetings:
            print(m)

    def find_next_free_slot(self, start_time: datetime, duration: timedelta) -> datetime:
        """Находит ближайший свободный временной слот заданной длительности, начиная с указанного времени, с учетом рабочего графика.

        Args:
            start_time: Время, с которого начинать поиск.
            duration: Требуемая длительность слота.

        Returns:
            Объект datetime, представляющий начало ближайшего свободного слота.
        """
        current_time = start_time
        
        if not self.is_working_time(current_time):
            current_time = self._next_working_time(current_time)
            
        sorted_meetings = sorted(self.meetings, key=lambda m: m.start_time)
        if not sorted_meetings:
             if current_time.hour < self.work_start_hour:
                 current_time = current_time.replace(hour=self.work_start_hour, minute=0, second=0, microsecond=0)
             return current_time
        
        while True:
            is_free = True
            potential_end_time = current_time + duration            
            for meeting in sorted_meetings:
                if current_time < meeting.end_time and meeting.start_time < potential_end_time:
                    is_free = False
                    current_time = meeting.end_time 
                    if not self.is_working_time(current_time):
                         current_time = self._next_working_time(current_time)
                    break
            
            if is_free:
                end_of_workday = datetime(
                    current_time.year, 
                    current_time.month, 
                    current_time.day, 
                    self.work_end_hour, 
                    0, 
                    0
                )
                if potential_end_time <= end_of_workday:
                    return current_time
                else:
                    current_time = self._next_working_time(current_time.replace(hour=self.work_end_hour))

    def get_conflicting_meetings(self, start_time: datetime, duration: timedelta) -> List[Meeting]:
        """Находит встречи, которые пересекаются с заданным временным интервалом.

        Args:
            start_time: Время начала интервала для проверки.
            duration: Длительность интервала для проверки.

        Returns:
            Список встреч, конфликтующих с указанным интервалом.
        """
        conflicts = []
        requested_end_time = start_time + duration
        for meeting in self.meetings:
            if start_time < meeting.end_time and meeting.start_time < requested_end_time:
                conflicts.append(meeting)
        return conflicts

    def _next_working_time(self, time: datetime) -> datetime:
        """Находит следующее рабочее время, начиная с указанного момента.

        Args:
            time: Время, от которого искать следующий рабочий момент.

        Returns:
            Объект datetime, представляющий начало следующего рабочего интервала.
        """
        current = time
        
        if current.hour >= self.work_end_hour:
            current = current.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        if current.hour < self.work_start_hour:
            current = current.replace(hour=self.work_start_hour, minute=0, second=0, microsecond=0)
        
        while current.weekday() not in self.working_days:
             current = current.replace(hour=self.work_start_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
        if current.hour < self.work_start_hour:
             current = current.replace(hour=self.work_start_hour, minute=0, second=0, microsecond=0)
             while current.weekday() not in self.working_days:
                  current = current + timedelta(days=1)
                  
        return current

    def get_state_string(self) -> str:
        """Возвращает строковое представление текущего состояния календаря."""
        if not self.meetings:
            return "Календарь пуст."
        
        sorted_meetings = sorted(self.meetings, key=lambda m: m.start_time)        
        meeting_lines = [str(m) for m in sorted_meetings]
        return "\n\n\n".join(meeting_lines)


class BaseCalendarTool(Tool):
    """Базовый класс для инструментов, работающих с объектом Calendar."""
    def __init__(self, calendar: Calendar):
        super().__init__()
        self.calendar = calendar


class AddMeetingTool(BaseCalendarTool):
    name = "add_meeting"
    description = "Добавляет новую встречу в календарь с указанными параметрами."
    inputs = {
        "topic": {
            "type": "string",
            "description": "Тема/название встречи.",
        },
        "organizer": {
            "type": "string",
            "description": "Организатор встречи.",
        },
        "duration": {
            "type": "integer",
            "description": "Длительность встречи в минутах.",
        },
        "date": {
            "type": "string",
            "description": "Дата встречи в формате 'ГГГГ-ММ-ДД'.",
        },
        "time": {
            "type": "string",
            "description": "Время начала встречи в формате 'ЧЧ:ММ'.",
        },
        "priority": {
            "type": "string",
            "description": "Приоритет встречи ('LOW', 'MEDIUM', или 'HIGH'). Агент должен определить подходящий приоритет на основе контекста встречи (тема, важность, участники). По умолчанию 'MEDIUM', если не указано.",
            "nullable": True
        }
    }
    output_type = "object"
    
    def forward(self, topic: str, organizer: str, duration: int, date: str, time: str, 
               priority: Optional[str] = None) -> Dict[str, Any]:
        """Обрабатывает добавление встречи.

        Возвращает словарь с результатом операции, включая детали конфликтов, если они есть.
        """
        result = {"success": False, "message": "", "data": None}
    
        priority_enum = Priority.MEDIUM
        if priority:
            try:
                priority_enum = Priority[priority.upper()]
            except KeyError:
                raise ValueError(f"Ошибка: Неверное значение приоритета '{priority}'. Используйте 'LOW', 'MEDIUM' или 'HIGH'.")

        try:
            start_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
                raise ValueError(f"Ошибка: Неверный формат даты '{date}' или времени '{time}'. Используйте 'ГГГГ-ММ-ДД' и 'ЧЧ:ММ'.")

        success = self.calendar.add_meeting(
            topic=topic,
            organizer=organizer,
            duration=duration,
            start_time=start_time,
            priority=priority_enum
        )
        if success:
            result["success"] = True
            result["message"] = f"Встреча '{topic}' успешно добавлена"
        else:
            conflicting_meetings = self.calendar.get_conflicting_meetings(
                start_time, timedelta(minutes=duration)
            )
            next_slot = self.calendar.find_next_free_slot(start_time, timedelta(minutes=duration))
            
            conflict_details = []
            for meeting in conflicting_meetings:
                conflict_details.append({
                    "id": meeting.id,
                    "topic": meeting.topic,
                    "organizer": meeting.organizer,
                    "start_time": meeting.start_time.isoformat(),
                    "end_time": meeting.end_time.isoformat(),
                    "priority": meeting.priority.name
                })

            conflict_topics = ', '.join([m['topic'] for m in conflict_details]) if conflict_details else 'Неизвестная встреча'
            raise ValueError(
                f"Не удалось добавить встречу в запрошенное время из-за конфликта(ов). "
                f"Конфликтующие встречи: {conflict_topics}. "
                f"Ближайший свободный слот: {next_slot.strftime('%Y-%m-%d %H:%M')}."
            )
        return result


class RemoveMeetingTool(BaseCalendarTool):
    name = "remove_meeting"
    description = "Удаляет встречу из календаря по её ID."
    inputs = {
        "meeting_id": {
            "type": "integer",
            "description": "ID встречи, которую нужно удалить.",
        }
    }
    output_type = "object"
    
    def forward(self, meeting_id: int) -> Dict[str, Any]:
        """Обрабатывает удаление встречи."""
        result = {"success": False, "message": "", "data": None}
        
        try:
            success = self.calendar.remove_meeting(meeting_id)
            if success:
                result["success"] = True
                result["message"] = f"Встреча {meeting_id} успешно удалена"
            else:
                result["message"] = f"Встреча {meeting_id} не найдена"
        
        except Exception as e:
            result["message"] = f"Произошла ошибка: {str(e)}"
        
        return result


class ListMeetingsTool(BaseCalendarTool):
    name = "list_meetings"
    description = "Выводит список всех встреч в календаре."
    inputs = {}
    output_type = "string"
    
    def forward(self) -> Dict[str, Any]:
        """Возвращает структурированный список всех встреч."""
        try:
            original_stdout = sys.stdout
            meetings_output = io.StringIO()
            sys.stdout = meetings_output
            
            self.calendar.list_meetings()            
            sys.stdout = original_stdout
            
            meetings_data = []
            if not self.calendar.meetings:
                 message = "Календарь пуст."
            else:
                 message = "Встречи успешно получены."
                 for meeting in self.calendar.meetings:
                     meetings_data.append({
                         "id": meeting.id,
                         "topic": meeting.topic,
                         "organizer": meeting.organizer,
                         "duration": int(meeting.duration.total_seconds() // 60), 
                         "start_time": meeting.start_time.isoformat(),
                         "end_time": meeting.end_time.isoformat(),
                         "priority": meeting.priority.name
                     })
            return meetings_output.getvalue().strip()
        except Exception as e:
            raise ValueError(f"Произошла ошибка: {str(e)}")


class FindFreeSlotTool(BaseCalendarTool):
    name = "find_free_slot"
    description = "Находит ближайший доступный свободный временной слот для встречи."
    inputs = {
        "duration": {
            "type": "integer",
            "description": "Требуемая длительность встречи в минутах.",
        },
        "date": {
            "type": "string",
            "description": "Дата, с которой начать поиск, в формате 'ГГГГ-ММ-ДД'.",
        },
        "time": {
            "type": "string",
            "description": "Время, с которого начать поиск, в формате 'ЧЧ:ММ'. Необязательно (если не указано, поиск начнется с начала рабочего дня указанной даты).",
            "nullable": True
        }
    }
    output_type = "object"
    
    def forward(self, duration: int, date: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Обрабатывает поиск свободного слота."""
        result = {"success": False, "message": "", "data": None}
        
        try:
            try:
                if time:
                    start_search_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                else:
                    start_search_dt = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                 result["message"] = f"Ошибка: Неверный формат даты '{date}' или времени '{time}'. Используйте 'ГГГГ-ММ-ДД' и 'ЧЧ:ММ'."
                 return result

            meeting_duration = timedelta(minutes=duration)
            next_slot = self.calendar.find_next_free_slot(start_search_dt, meeting_duration)
            
            result["success"] = True
            result["message"] = f"Найден ближайший свободный слот: {next_slot.strftime('%Y-%m-%d %H:%M')}"
            result["data"] = {"next_available_slot": next_slot.isoformat()}
        
        except Exception as e:
            result["message"] = f"Произошла ошибка: {str(e)}"
        
        return result


class IsTimeAvailableTool(BaseCalendarTool):
    name = "is_time_available"
    description = "Проверяет, доступен ли конкретный временной слот для встречи."
    inputs = {
        "duration": {
            "type": "integer",
            "description": "Длительность встречи в минутах для проверки.",
        },
        "date": {
            "type": "string",
            "description": "Дата для проверки в формате 'ГГГГ-ММ-ДД'.",
        },
        "time": {
            "type": "string",
            "description": "Время начала для проверки в формате 'ЧЧ:ММ'.",
        }
    }
    output_type = "object"
    
    def forward(self, duration: int, date: str, time: str) -> Dict[str, Any]:
        """Обрабатывает проверку доступности времени."""
        result = {"success": False, "message": "", "data": None}
        
        try:
            try:
                check_start_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            except ValueError:
                 result["message"] = f"Ошибка: Неверный формат даты '{date}' или времени '{time}'. Используйте 'ГГГГ-ММ-ДД' и 'ЧЧ:ММ'."
                 return result
            
            check_duration = timedelta(minutes=duration)
            check_end_time = check_start_time + check_duration

            is_start_working = self.calendar.is_working_time(check_start_time)
            end_of_workday = check_start_time.replace(hour=self.calendar.work_end_hour, minute=0, second=0, microsecond=0)
            is_end_within_working = (check_start_time.date() == check_end_time.date() and check_end_time <= end_of_workday)

            is_working_time_slot = is_start_working and is_end_within_working

            is_free = True
            conflicting_meetings = self.calendar.get_conflicting_meetings(check_start_time, check_duration)
            if conflicting_meetings:
                 is_free = False
            
            available = is_working_time_slot and is_free
            
            message = f"Временной слот с {check_start_time.strftime('%H:%M')} до {check_end_time.strftime('%H:%M')} "
            if available:
                result["success"] = True
                message += "доступен."
            else:
                result["success"] = False
                message += "не доступен."
                reasons = []
                if not is_working_time_slot:
                    reasons.append("нерабочее время")
                if not is_free:
                    conflict_topics = ', '.join([m.topic for m in conflicting_meetings])
                    reasons.append(f"конфликт с встречами: {conflict_topics}")
                message += f" Причины: {'; '.join(reasons)}."

            result["message"] = message
            result["data"] = {
                "available": available,
                "is_working_time": is_working_time_slot,
                "is_free_from_meetings": is_free,
                "conflicting_meetings": [
                    {
                         "id": m.id, "topic": m.topic, "start": m.start_time.isoformat(), 
                         "end": m.end_time.isoformat(), "priority": m.priority.name
                    } for m in conflicting_meetings
                ]
            }
        
        except Exception as e:
            result["message"] = f"Произошла ошибка: {str(e)}"
        
        return result


class SetWorkingDaysTool(BaseCalendarTool):
    name = "set_working_days"
    description = "Устанавливает, какие дни недели являются рабочими."
    inputs = {
        "working_days": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Список рабочих дней в виде целых чисел (0=Понедельник, 6=Воскресенье).",
        }
    }
    output_type = "object"
    
    def forward(self, working_days: List[int]) -> Dict[str, Any]:
        """Обрабатывает установку рабочих дней."""
        result = {"success": False, "message": "", "data": None}
        
        try:
            if not isinstance(working_days, list) or not all(isinstance(d, int) and 0 <= d <= 6 for d in working_days):
                 result["message"] = "Ошибка: 'working_days' должен быть списком целых чисел от 0 до 6."
                 return result
                 
            valid_days = set(working_days)
            self.calendar.set_working_days(valid_days)
            
            day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            sorted_days = sorted(list(valid_days)) 
            working_day_names = [day_names[day] for day in sorted_days]
            
            result["success"] = True
            result["message"] = f"Рабочие дни установлены: {', '.join(working_day_names)}"
            result["data"] = {"working_days": sorted_days}
        
        except Exception as e:
            result["message"] = f"Произошла ошибка: {str(e)}"
        
        return result


class SetWorkingHoursTool(BaseCalendarTool):
    name = "set_working_hours"
    description = "Устанавливает рабочие часы для каждого рабочего дня."
    inputs = {
        "work_start_hour": {
            "type": "integer",
            "description": "Час начала рабочего дня (0-23).",
        },
        "work_end_hour": {
            "type": "integer",
            "description": "Час окончания рабочего дня (1-24). Окончание не включается (например, 18 означает до 17:59).",
        }
    }
    output_type = "object"
    
    def forward(self, work_start_hour: int, work_end_hour: int) -> Dict[str, Any]:
        """Обрабатывает установку рабочих часов."""
        result = {"success": False, "message": "", "data": None}
        
        try:
            self.calendar.set_working_hours(work_start_hour, work_end_hour)
            
            result["success"] = True
            result["message"] = f"Рабочие часы установлены с {work_start_hour}:00 до {work_end_hour}:00"
            result["data"] = {
                "work_start_hour": work_start_hour,
                "work_end_hour": work_end_hour
            }
        
        except ValueError as e:
            result["message"] = str(e)
        except Exception as e:
            result["message"] = f"Произошла ошибка: {str(e)}"
        
        return result
    
class GetCurrentDateTool(Tool):
    name = "get_current_date"
    description = "Возвращает текущую дату в формате 'ГГГГ-ММ-ДД'."
    inputs = {}
    output_type = "string"
    
    def forward(self) -> Dict[str, Any]:
        """Возвращает текущую дату."""
        return datetime.now().strftime('%Y-%m-%d')


class CalendarToolset:
    """Предоставляет набор инструментов для работы с одним экземпляром календаря."""
    def __init__(self, calendar: Calendar):
        """Инициализирует набор инструментов с заданным календарем."""
        self.calendar = calendar
        self.tools = [
            AddMeetingTool(self.calendar),
            RemoveMeetingTool(self.calendar),
            ListMeetingsTool(self.calendar),
            FindFreeSlotTool(self.calendar),
            IsTimeAvailableTool(self.calendar),
            GetCurrentDateTool(self.calendar)
        ]
    
    def get_tools(self) -> List[Tool]:
        """Возвращает список доступных инструментов календаря."""
        return self.tools