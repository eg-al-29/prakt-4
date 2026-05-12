"""
Вариант 1: Классический паттерн «Одиночка» для конфигурации и аудита.
Проблемы: глобальное состояние, сложность тестирования, утечка состояния между тестами.
"""

import threading
import yaml
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuditRecord:
    """Запись в журнале аудита."""
    sender: str
    recipient: str
    request_id: str
    channel: str
    status: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConfigurationSingleton:
    """
    Классический одиночка с ленивой инициализацией и потокобезопасностью.
    Проблема: статический глобальный доступ отовсюду.
    """
    _instance: Optional['ConfigurationSingleton'] = None
    _lock = threading.Lock()

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Приватный конструктор."""
        self._config = config_data or {}

    @classmethod
    def get_instance(cls, config_path: str = "config.yaml") -> 'ConfigurationSingleton':
        """Получить единственный экземпляр конфигурации."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls._load_config(config_path)
        return cls._instance

    @classmethod
    def _load_config(cls, config_path: str) -> 'ConfigurationSingleton':
        """Загрузить конфигурацию из файла."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return cls(data.get('application', {}))
        except FileNotFoundError:
            # Для тестов: если файл не найден, используем пустую конфигурацию
            return cls({})

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации."""
        return self._config.get(key, default)

    @classmethod
    def reset(cls) -> None:
        """
        Сброс экземпляра (только для тестов).
        Это уродливый хак, который показывает проблему глобального состояния.
        """
        cls._instance = None


class AuditorSingleton:
    """
    Одиночка для аудита уведомлений.
    Глобальный доступ создаёт скрытые зависимости.
    """
    _instance: Optional['AuditorSingleton'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Приватный конструктор."""
        self._records: List[AuditRecord] = []

    @classmethod
    def get_instance(cls) -> 'AuditorSingleton':
        """Получить единственный экземпляр аудитора."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record_notification(
        self,
        sender: str,
        recipient: str,
        request_id: str,
        channel: str,
        status: str
    ) -> None:
        """Записать факт отправки уведомления."""
        record = AuditRecord(
            sender=sender,
            recipient=recipient,
            request_id=request_id,
            channel=channel,
            status=status
        )
        self._records.append(record)

    def get_records(self) -> List[AuditRecord]:
        """Получить все записи аудита."""
        return self._records.copy()

    @classmethod
    def reset(cls) -> None:
        """Сброс экземпляра (только для тестов)."""
        cls._instance = None


class NotificationService:
    """
    Сервис уведомлений, зависит от одиночек через глобальный доступ.
    Это плохая архитектура, но такова была исходная задача.
    """

    def send_notification(
        self,
        recipient: str,
        request_id: str,
        message: str
    ) -> bool:
        """Отправить уведомление."""
        config = ConfigurationSingleton.get_instance()
        auditor = AuditorSingleton.get_instance()

        provider = config.get('notification_provider', 'email')
        enable_audit = config.get('enable_audit', False)

        # Имитация отправки
        success = True

        # Фиксируем в аудите если включён
        if enable_audit:
            auditor.record_notification(
                sender='system',
                recipient=recipient,
                request_id=request_id,
                channel=provider,
                status='sent' if success else 'failed'
            )

        return success
