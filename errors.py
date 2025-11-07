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