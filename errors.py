class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass

class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass

class FileNotFoundError(ConfigError):
    """Исключение для отсутствующих файлов"""
    pass

class InvalidValueError(ValidationError):
    """Исключение для неверных значений параметров"""
    pass

class DependencyError(Exception):
    """Исключение для ошибок получения зависимостей"""
    pass

class NetworkError(DependencyError):
    """Исключение для сетевых ошибок"""
    pass

class PackageNotFoundError(DependencyError):
    """Исключение когда пакет не найден"""
    pass

# Новые исключения для этапа 3
class GraphError(Exception):
    """Исключение для ошибок построения графа"""
    pass

class CycleDetectedError(GraphError):
    """Исключение при обнаружении циклических зависимостей"""
    pass

class TestRepositoryError(GraphError):
    """Исключение для ошибок тестового репозитория"""
    pass