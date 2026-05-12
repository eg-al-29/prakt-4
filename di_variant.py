"""
Вариант 2: Альтернатива одиночке через внедрение зависимостей.
Одиночка остаётся «единственным на приложение» по жизненному циклу,
но достигается это через управление в контейнере, а не через глобальный доступ.

Преимущества:
- Тестируемость: каждый тест может получить свой экземпляр
- Гибкость: легко подменить реализацию
- Явные зависимости: видны в сигнатуре конструктора
"""

import threading
from typing import Optional, Dict, Any, List, Protocol
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


class IConfiguration(Protocol):
    """Интерфейс конфигурации."""

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации."""
        ...


class Configuration:
    """
    Конфигурация — простой класс (не одиночка).
    Единственность на приложение обеспечивается контейнером,
    а не глобальным статическим доступом.
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Конструктор принимает данные конфигурации."""
        self._config = config_data or {}

    @staticmethod
    def load_from_file(config_path: str) -> 'Configuration':
        """Загрузить конфигурацию из файла."""
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return Configuration(data.get('application', {}))
        except FileNotFoundError:
            return Configuration({})

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации."""
        return self._config.get(key, default)


class IAuditor(Protocol):
    """Интерфейс аудитора."""

    def record_notification(
        self,
        sender: str,
        recipient: str,
        request_id: str,
        channel: str,
        status: str
    ) -> None:
        """Записать факт отправки уведомления."""
        ...

    def get_records(self) -> List[AuditRecord]:
        """Получить все записи аудита."""
        ...


class Auditor:
    """
    Аудитор уведомлений — простой класс, не одиночка.
    Внедряется через конструктор, где нужна его функциональность.
    """

    def __init__(self):
        """Конструктор."""
        self._records: List[AuditRecord] = []

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


class NotificationService:
    """
    Сервис уведомлений с явными зависимостями.
    Все зависимости передаются через конструктор.
    """

    def __init__(self, config: Configuration, auditor: Optional[Auditor] = None):
        """
        Конструктор с явными зависимостями.

        Args:
            config: Конфигурация приложения
            auditor: Аудитор уведомлений (опционально)
        """
        self._config = config
        self._auditor = auditor

    def send_notification(
        self,
        recipient: str,
        request_id: str,
        message: str
    ) -> bool:
        """Отправить уведомление."""
        provider = self._config.get('notification_provider', 'email')
        enable_audit = self._config.get('enable_audit', False)

        # Имитация отправки
        success = True

        # Фиксируем в аудите если включён и аудитор настроен
        if enable_audit and self._auditor:
            self._auditor.record_notification(
                sender='system',
                recipient=recipient,
                request_id=request_id,
                channel=provider,
                status='sent' if success else 'failed'
            )

        return success


class DIContainer:
    """
    Простой контейнер внедрения зависимостей.
    Гарантирует, что каждый компонент создаётся один раз на приложение
    (управление жизненным циклом «Singleton»).
    """

    def __init__(self):
        """Инициализировать контейнер."""
        self._singletons: Dict[str, Any] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """Зарегистрировать одиночный экземпляр."""
        self._singletons[name] = instance

    def get(self, name: str) -> Any:
        """Получить экземпляр по имени."""
        if name not in self._singletons:
            raise KeyError(f"Component '{name}' not registered in container")
        return self._singletons[name]

    def get_or_create(self, name: str, factory) -> Any:
        """Получить или создать экземпляр."""
        if name not in self._singletons:
            self._singletons[name] = factory()
        return self._singletons[name]


def create_container() -> DIContainer:
    """Фабрика для создания контейнера с полной конфигурацией приложения."""
    container = DIContainer()

    # Создаём компоненты в определённом порядке
    config = Configuration.load_from_file("config.yaml")
    auditor = Auditor()
    notification_service = NotificationService(config, auditor)

    # Регистрируем в контейнере
    container.register_singleton('config', config)
    container.register_singleton('auditor', auditor)
    container.register_singleton('notification_service', notification_service)

    return container
