# Практика 4: Паттерн «Одиночка» и альтернативы

## Описание

Учебный проект, демонстрирующий инженерные проблемы классического паттерна «Одиночка» и альтернативный подход через внедрение зависимостей.

Проект реализует систему уведомлений студентам с компонентами конфигурации и аудита.

## Структура проекта

```
prakt-4/
├── config.yaml                  # Конфигурация приложения
├── singleton_variant.py         # Вариант 1: Классический одиночка
├── di_variant.py               # Вариант 2: Внедрение зависимостей
├── test_singleton_variant.py   # Тесты для варианта 1 (3 теста)
├── test_di_variant.py          # Тесты для варианта 2 (6+ тестов)
├── COMPARISON.md               # Сравнительная анализ
└── README.md                   # Этот файл
```

## Запуск тестов

### Требования

```bash
pip install pytest pyyaml
```

### Выполнение всех тестов

```bash
pytest -v
```

### Выполнение тестов для конкретного варианта

```bash
# Тесты одиночки
pytest test_singleton_variant.py -v

# Тесты внедрения зависимостей
pytest test_di_variant.py -v
```

### Покрытие с детализацией

```bash
pytest -v --tb=short
```

## Основные компоненты

### Вариант 1: Классический одиночка (singleton_variant.py)

**ConfigurationSingleton** — одиночка с ленивой инициализацией для чтения конфигурации.

```python
config = ConfigurationSingleton.get_instance()
provider = config.get('notification_provider')
```

**AuditorSingleton** — одиночка для аудита отправленных уведомлений.

**Проблемы:**
- Глобальное состояние
- Скрытые зависимости (компоненты сами обращаются к одиночкам)
- Утечка состояния между тестами (требуется reset())
- Сложность подмены в тестах

### Вариант 2: Внедрение зависимостей (di_variant.py)

**Configuration** — простой класс для хранения конфигурации.

**Auditor** — простой класс для записи аудита.

**NotificationService** — сервис, получающий зависимости через конструктор.

```python
config = Configuration.load_from_file('config.yaml')
auditor = Auditor()
service = NotificationService(config, auditor)
service.send_notification('user@example.com', 'req-001', 'message')
```

**DIContainer** — простой контейнер для управления жизненным циклом компонентов.

**Преимущества:**
- Явные зависимости
- Каждый тест получает свои экземпляры
- Лёгкая подмена в тестах
- Отсутствие скрытого состояния

## Набор тестов

### test_singleton_variant.py (5 тестов)

1. **TestConfigurationSingletonIsolation** — проверка изоляции состояния (требуется reset())
2. **TestConfigurationSubstitution** — подмена конфигурации (требуется прямой доступ к _instance)
3. **TestAuditorWithSingleton** — использование одиночки для аудита с утечкой состояния
4. **TestThreadSafetyOfSingleton** — потокобезопасность инициализации

### test_di_variant.py (11 тестов)

1. **TestConfigurationDI** — создание конфигурации из данных
2. **TestAuditorDI** — полная независимость экземпляров аудитора
3. **TestNotificationServiceDI** — сервис с явными зависимостями
4. **TestDIContainer** — регистрация и получение компонентов
5. **TestDIContainerIntegration** — полная изоляция тестов без хаков

## Результаты тестирования

```
test_singleton_variant.py::TestConfigurationSingletonIsolation::test_first_configuration PASSED
test_singleton_variant.py::TestConfigurationSingletonIsolation::test_second_configuration PASSED
test_singleton_variant.py::TestConfigurationSubstitution::test_substitute_configuration_with_file PASSED
test_singleton_variant.py::TestConfigurationSubstitution::test_substitute_configuration_with_mock PASSED
test_singleton_variant.py::TestAuditorWithSingleton::test_notification_audit_enabled PASSED
test_singleton_variant.py::TestAuditorWithSingleton::test_auditor_state_leak_between_tests PASSED
test_singleton_variant.py::TestThreadSafetyOfSingleton::test_concurrent_initialization PASSED

test_di_variant.py::TestConfigurationDI::test_configuration_from_dict PASSED
test_di_variant.py::TestConfigurationDI::test_configuration_with_defaults PASSED
test_di_variant.py::TestConfigurationDI::test_configuration_load_from_file PASSED
test_di_variant.py::TestConfigurationDI::test_configuration_missing_file PASSED
test_di_variant.py::TestAuditorDI::test_auditor_records_notification PASSED
test_di_variant.py::TestAuditorDI::test_auditor_independence PASSED
test_di_variant.py::TestNotificationServiceDI::test_notification_with_audit PASSED
test_di_variant.py::TestNotificationServiceDI::test_notification_without_audit PASSED
test_di_variant.py::TestNotificationServiceDI::test_notification_without_auditor PASSED
test_di_variant.py::TestNotificationServiceDI::test_easy_substitution_of_config PASSED
test_di_variant.py::TestDIContainer::test_container_register_and_get PASSED
test_di_variant.py::TestDIContainer::test_container_same_instance PASSED
test_di_variant.py::TestDIContainer::test_container_missing_component PASSED
test_di_variant.py::TestDIContainer::test_full_application_container PASSED
test_di_variant.py::TestDIContainerIntegration::test_isolated_tests_with_separate_containers PASSED
test_di_variant.py::TestDIContainerIntegration::test_multiple_notifications_in_one_container PASSED
```

## Важные выводы

Смотрите подробный анализ в [COMPARISON.md](COMPARISON.md).

**Короткий вывод:** Одиночка оправдан для управления инфраструктурой (пулы соединений, глобальные ресурсы), где *действительно* нужно одно и то же состояние. Для бизнес-компонентов (сервисы, конфигурация) предпочтительнее внедрение зависимостей с управлением жизненным циклом в контейнере.
