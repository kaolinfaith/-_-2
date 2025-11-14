from config import AppConfig
from errors import ValidationError, InvalidValueError
import os
import re


class ConfigValidator:

    @staticmethod
    def validate(config: AppConfig):
        ConfigValidator._validate_package_name(config.package_name)
        ConfigValidator._validate_repository_url(config.repository_url)
        ConfigValidator._validate_test_repo_mode(config.test_repo_mode)
        ConfigValidator._validate_output_image(config.output_image)
        ConfigValidator._validate_max_depth(config.max_depth)
        ConfigValidator._validate_filter_substring(config.filter_substring)

    @staticmethod
    def _validate_package_name(package_name: str):
        """Валидация имени пакета в формате Maven (groupId:artifactId:version)"""
        if not package_name:
            raise ValidationError("Имя пакета не может быть пустым")

        if not isinstance(package_name, str):
            raise InvalidValueError("Имя пакета должно быть строкой")

        if len(package_name) > 200:
            raise InvalidValueError("Имя пакета слишком длинное (максимум 200 символов)")

        parts = package_name.split(':')
        if len(parts) < 2 or len(parts) > 3:
            raise InvalidValueError(
                "Неверный формат имени пакета. Ожидается: groupId:artifactId[:version]"
            )

        # Проверяем каждую часть на допустимые символы
        for i, part in enumerate(parts):
            if not part:
                part_names = ["GroupId", "ArtifactId", "Version"]
                raise InvalidValueError(f"{part_names[i]} не может быть пустым")

            # Более мягкая проверка символов для Maven координат
            if not re.match(r'^[a-zA-Z0-9_.\-]+$', part):
                raise InvalidValueError(
                    f"Часть пакета '{part}' содержит недопустимые символы. "
                    f"Допустимы только буквы, цифры, точки, дефисы и подчеркивания"
                )

    @staticmethod
    def _validate_repository_url(repository_url: str):
        if not repository_url:
            raise ValidationError("URL репозитория или путь к файлу не может быть пустым")
        if not isinstance(repository_url, str):
            raise InvalidValueError("URL репозитория должен быть строкой")

        if repository_url.startswith('http'):
            if not re.match(r'^https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/.*)?$', repository_url):
                raise InvalidValueError(f"Неверный формат URL: {repository_url}")
        # Для локальных путей проверяем существование только если режим local
        elif repository_url.startswith('/') or repository_url.startswith('./'):
            if not os.path.exists(repository_url):
                raise InvalidValueError(f"Локальный путь не существует: {repository_url}")

    @staticmethod
    def _validate_test_repo_mode(test_repo_mode: str):
        valid_modes = ['local', 'remote', 'test']
        if test_repo_mode not in valid_modes:
            raise InvalidValueError(f"Неверный режим работы. Допустимые значения: {', '.join(valid_modes)}")

    @staticmethod
    def _validate_output_image(output_image: str):
        if not output_image:
            raise ValidationError("Имя выходного файла не может быть пустым")

        if not isinstance(output_image, str):
            raise InvalidValueError("Имя выходного файла должно быть строкой")

        valid_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.pdf']
        if not any(output_image.lower().endswith(ext) for ext in valid_extensions):
            raise InvalidValueError(f"Неподдерживаемое расширение файла. Допустимые: {', '.join(valid_extensions)}")

    @staticmethod
    def _validate_max_depth(max_depth: int):
        if not isinstance(max_depth, int):
            raise InvalidValueError("Максимальная глубина должна быть целым числом")

        if max_depth < 0:
            raise InvalidValueError("Максимальная глубина не может быть отрицательной")

        if max_depth > 100:
            raise InvalidValueError("Максимальная глубина слишком большая (максимум 100)")

    @staticmethod
    def _validate_filter_substring(filter_substring: str):
        if not isinstance(filter_substring, str):
            raise InvalidValueError("Подстрока для фильтрации должна быть строкой")
        if len(filter_substring) > 50:
            raise InvalidValueError("Подстрока для фильтрации слишком длинная (максимум 50 символов)")