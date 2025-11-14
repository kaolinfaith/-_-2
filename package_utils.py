import re
from typing import Tuple, Optional
from errors import InvalidValueError


class PackageUtils:
    """Утилиты для работы с Maven пакетами"""

    @staticmethod
    def parse_package_name(package_name: str) -> Tuple[str, str, str]:
        """
        Парсит имя пакета в формате groupId:artifactId:version

        Args:
            package_name: Строка в формате groupId:artifactId[:version]

        Returns:
            Tuple: (group_id, artifact_id, version)

        Raises:
            InvalidValueError: Если формат неверный
        """
        parts = package_name.split(':')

        if len(parts) < 2 or len(parts) > 3:
            raise InvalidValueError(
                "Неверный формат имени пакета. Ожидается: groupId:artifactId[:version]"
            )

        group_id = parts[0]
        artifact_id = parts[1]
        version = parts[2] if len(parts) == 3 else None

        if not group_id or not artifact_id:
            raise InvalidValueError("GroupId и ArtifactId не могут быть пустыми")

        return group_id, artifact_id, version

    @staticmethod
    def validate_maven_coordinates(group_id: str, artifact_id: str, version: str = None):
        """Валидирует Maven координаты"""
        if not re.match(r'^[a-zA-Z0-9_.-]+$', group_id):
            raise InvalidValueError(f"Недопустимый GroupId: {group_id}")

        if not re.match(r'^[a-zA-Z0-9_.-]+$', artifact_id):
            raise InvalidValueError(f"Недопустимый ArtifactId: {artifact_id}")

        if version and not re.match(r'^[a-zA-Z0-9_.-]+$', version):
            raise InvalidValueError(f"Недопустимая версия: {version}")

    @staticmethod
    def format_dependency_output(dependencies: list) -> str:
        """Форматирует вывод зависимостей для отображения"""
        if not dependencies:
            return "Прямые зависимости не найдены"

        output = ["Прямые зависимости:"]
        for i, dep in enumerate(dependencies, 1):
            scope_info = f" (scope: {dep['scope']})" if dep.get('scope') and dep['scope'] != 'compile' else ""
            version_info = f" version: {dep['version']}" if dep.get('version') else " version: не указана"
            output.append(f"{i}. {dep['groupId']}:{dep['artifactId']}{version_info}{scope_info}")

        return '\n'.join(output)