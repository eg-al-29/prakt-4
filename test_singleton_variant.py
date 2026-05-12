"""
Тесты для варианта 1 (Одиночка).

Демонстрируют проблемы:
1. Утечка состояния между тестами
2. Сложность подмены источника конфигурации
3. Скрытые зависимости
"""

import pytest
import tempfile
import os
from singleton_variant import (
    ConfigurationSingleton,
    AuditorSingleton,
    NotificationService
)


class TestConfigurationSingletonIsolation:
    """
    Тест на независимость между тестами.
    ПРОБЛЕМА: состояние одиночки утекает между тестами.
    """

    def setup_method(self):
        """Сброс перед каждым тестом."""
        ConfigurationSingleton.reset()
        AuditorSingleton.reset()

    def test_first_configuration(self):
        """Первый тест: настраиваем конфигурацию."""
        config = ConfigurationSingleton.get_instance("config.yaml")
        assert config.get('notification_provider') == 'email'
        assert config.get('enable_audit') == True

    def test_second_configuration(self):
        """Второй тест: проверяем, что он получает ту же конфигурацию."""
        config = ConfigurationSingleton.get_instance("config.yaml")
        # Без reset() между тестами здесь могла бы быть утечка состояния
        assert config is ConfigurationSingleton.get_instance("config.yaml")


class TestConfigurationSubstitution:
    """
    Тест на подмену источника конфигурации.
    ПРОБЛЕМА: сложно подменять конфигурацию в одиночке.
    """

    def setup_method(self):
        """Сброс перед каждым тестом."""
        ConfigurationSingleton.reset()
        AuditorSingleton.reset()

    def test_substitute_configuration_with_file(self):
        """Создать временный файл конфигурации для теста."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("application:\n  notification_provider: sms\n  enable_audit: false\n")
            temp_path = f.name

        try:
            config = ConfigurationSingleton.get_instance(temp_path)
            assert config.get('notification_provider') == 'sms'
            assert config.get('enable_audit') == False
        finally:
            os.unlink(temp_path)
            ConfigurationSingleton.reset()

    def test_substitute_configuration_with_mock(self):
        """
        Попытка подменить конфигурацию в памяти.
        Это требует прямого доступа к _instance и выглядит уродливо.
        """
        test_config = ConfigurationSingleton({'notification_provider': 'telegram'})
        ConfigurationSingleton._instance = test_config

        config = ConfigurationSingleton.get_instance()
        assert config.get('notification_provider') == 'telegram'
        ConfigurationSingleton.reset()


class TestAuditorWithSingleton:
    """
    Тест на аудит с использованием одиночки.
    ПРОБЛЕМА: состояние аудитора утекает между тестами.
    """

    def setup_method(self):
        """Сброс перед каждым тестом."""
        ConfigurationSingleton.reset()
        AuditorSingleton.reset()

    def test_notification_audit_enabled(self):
        """Отправка уведомления с включённым аудитом."""
        service = NotificationService()
        result = service.send_notification('student@example.com', 'req-001', 'Test message')

        assert result == True

        auditor = AuditorSingleton.get_instance()
        records = auditor.get_records()
        assert len(records) == 1
        assert records[0].recipient == 'student@example.com'
        assert records[0].status == 'sent'

    def test_auditor_state_leak_between_tests(self):
        """
        Демонстрация утечки состояния (ANTI-PATTERN).
        Если не вызвать reset(), записи из предыдущего теста останутся.
        """
        # Это не проблема благодаря setup_method, но показывает откуда она может взяться
        service = NotificationService()
        service.send_notification('another@example.com', 'req-002', 'Another message')

        auditor = AuditorSingleton.get_instance()
        records = auditor.get_records()
        # В этом тесте только одна запись благодаря reset() в setup_method
        assert len(records) == 1


class TestThreadSafetyOfSingleton:
    """Тест на потокобезопасность инициализации одиночки."""

    def setup_method(self):
        """Сброс перед каждым тестом."""
        ConfigurationSingleton.reset()
        AuditorSingleton.reset()

    def test_concurrent_initialization(self):
        """Имитация параллельной инициализации."""
        import threading

        instances = []
        lock = threading.Lock()

        def get_instance():
            config = ConfigurationSingleton.get_instance("config.yaml")
            with lock:
                instances.append(config)

        threads = [threading.Thread(target=get_instance) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Все потоки получили один и тот же экземпляр
        assert all(inst is instances[0] for inst in instances)
        assert len(set(id(inst) for inst in instances)) == 1
