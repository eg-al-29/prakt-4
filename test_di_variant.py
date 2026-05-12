"""
Тесты для варианта 2 (Внедрение зависимостей).

Демонстрируют преимущества:
1. Каждый тест имеет свои экземпляры
2. Легко подменять конфигурацию
3. Явные зависимости
4. Независимость тестов без хаков
"""

import pytest
from di_variant import (
    Configuration,
    Auditor,
    NotificationService,
    DIContainer,
    create_container
)


class TestConfigurationDI:
    """Тесты конфигурации с внедрением зависимостей."""

    def test_configuration_from_dict(self):
        """Создание конфигурации напрямую из словаря."""
        config = Configuration({
            'notification_provider': 'sms',
            'enable_audit': True
        })

        assert config.get('notification_provider') == 'sms'
        assert config.get('enable_audit') == True

    def test_configuration_with_defaults(self):
        """Получение значений по умолчанию."""
        config = Configuration({'notification_provider': 'email'})

        assert config.get('notification_provider') == 'email'
        assert config.get('enable_audit', False) == False
        assert config.get('non_existent', 'default') == 'default'

    def test_configuration_load_from_file(self):
        """Загрузка конфигурации из файла."""
        config = Configuration.load_from_file("config.yaml")

        assert config.get('notification_provider') == 'email'
        assert config.get('enable_audit') == True

    def test_configuration_missing_file(self):
        """Загрузка при отсутствии файла."""
        config = Configuration.load_from_file("non_existent.yaml")

        # Должна вернуться пустая конфигурация
        assert config.get('notification_provider') is None


class TestAuditorDI:
    """Тесты аудитора с внедрением зависимостей."""

    def test_auditor_records_notification(self):
        """Запись уведомления в аудит."""
        auditor = Auditor()

        auditor.record_notification(
            sender='system',
            recipient='student@example.com',
            request_id='req-001',
            channel='email',
            status='sent'
        )

        records = auditor.get_records()
        assert len(records) == 1
        assert records[0].recipient == 'student@example.com'
        assert records[0].status == 'sent'

    def test_auditor_independence(self):
        """
        Каждый тест получает свой аудитор.
        РЕШЕНИЕ проблемы утечки состояния!
        """
        auditor1 = Auditor()
        auditor2 = Auditor()

        auditor1.record_notification(
            sender='system',
            recipient='student1@example.com',
            request_id='req-001',
            channel='email',
            status='sent'
        )

        auditor2.record_notification(
            sender='system',
            recipient='student2@example.com',
            request_id='req-002',
            channel='email',
            status='sent'
        )

        # Каждый аудитор имеет только свои записи
        assert len(auditor1.get_records()) == 1
        assert len(auditor2.get_records()) == 1
        assert auditor1.get_records()[0].recipient == 'student1@example.com'
        assert auditor2.get_records()[0].recipient == 'student2@example.com'


class TestNotificationServiceDI:
    """Тесты сервиса уведомлений с внедрением зависимостей."""

    def test_notification_with_audit(self):
        """Отправка уведомления с аудитом."""
        config = Configuration({
            'notification_provider': 'email',
            'enable_audit': True
        })
        auditor = Auditor()
        service = NotificationService(config, auditor)

        result = service.send_notification(
            'student@example.com',
            'req-001',
            'Test message'
        )

        assert result == True
        records = auditor.get_records()
        assert len(records) == 1
        assert records[0].recipient == 'student@example.com'

    def test_notification_without_audit(self):
        """Отправка уведомления без аудита."""
        config = Configuration({
            'notification_provider': 'sms',
            'enable_audit': False
        })
        auditor = Auditor()
        service = NotificationService(config, auditor)

        result = service.send_notification(
            'student@example.com',
            'req-001',
            'Test message'
        )

        assert result == True
        # Аудитор не получал записи
        assert len(auditor.get_records()) == 0

    def test_notification_without_auditor(self):
        """Отправка уведомления без подключённого аудитора."""
        config = Configuration({
            'notification_provider': 'email',
            'enable_audit': True
        })
        # Не передаём аудитор
        service = NotificationService(config, None)

        result = service.send_notification(
            'student@example.com',
            'req-001',
            'Test message'
        )

        assert result == True

    def test_easy_substitution_of_config(self):
        """
        РЕШЕНИЕ проблемы подмены конфигурации!
        Тривиально подменять конфигурацию через конструктор.
        """
        test_config = Configuration({
            'notification_provider': 'telegram',
            'enable_audit': True
        })
        auditor = Auditor()
        service = NotificationService(test_config, auditor)

        service.send_notification('user@example.com', 'req-001', 'msg')

        records = auditor.get_records()
        assert records[0].channel == 'telegram'


class TestDIContainer:
    """Тесты контейнера внедрения зависимостей."""

    def test_container_register_and_get(self):
        """Регистрация и получение компонента."""
        container = DIContainer()
        config = Configuration({'notification_provider': 'email'})

        container.register_singleton('config', config)

        retrieved = container.get('config')
        assert retrieved is config

    def test_container_same_instance(self):
        """Контейнер гарантирует один и тот же экземпляр."""
        container = DIContainer()
        config = Configuration({'notification_provider': 'email'})

        container.register_singleton('config', config)

        inst1 = container.get('config')
        inst2 = container.get('config')

        assert inst1 is inst2

    def test_container_missing_component(self):
        """Ошибка при получении незарегистрированного компонента."""
        container = DIContainer()

        with pytest.raises(KeyError):
            container.get('non_existent')

    def test_full_application_container(self):
        """Создание полного контейнера приложения."""
        container = create_container()

        config = container.get('config')
        auditor = container.get('auditor')
        service = container.get('notification_service')

        assert config is not None
        assert auditor is not None
        assert service is not None

        # Каждый get возвращает один и тот же экземпляр
        assert config is container.get('config')
        assert auditor is container.get('auditor')


class TestDIContainerIntegration:
    """Интеграционные тесты с контейнером."""

    def test_isolated_tests_with_separate_containers(self):
        """
        РЕШЕНИЕ проблемы изоляции тестов!
        Каждый тест создаёт свой контейнер.
        """
        # Тест 1
        container1 = create_container()
        service1 = container1.get('notification_service')
        auditor1 = container1.get('auditor')

        service1.send_notification('user1@example.com', 'req-001', 'msg1')
        assert len(auditor1.get_records()) == 1

        # Тест 2
        container2 = create_container()
        service2 = container2.get('notification_service')
        auditor2 = container2.get('auditor')

        service2.send_notification('user2@example.com', 'req-002', 'msg2')

        # Ни одна запись из теста 1 не попала в тест 2!
        assert len(auditor2.get_records()) == 1
        assert auditor2.get_records()[0].recipient == 'user2@example.com'

    def test_multiple_notifications_in_one_container(self):
        """Несколько уведомлений в одном контексте приложения."""
        container = create_container()
        service = container.get('notification_service')
        auditor = container.get('auditor')

        service.send_notification('user1@example.com', 'req-001', 'msg1')
        service.send_notification('user2@example.com', 'req-002', 'msg2')
        service.send_notification('user3@example.com', 'req-003', 'msg3')

        records = auditor.get_records()
        assert len(records) == 3
