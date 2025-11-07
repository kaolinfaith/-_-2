from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """Класс для хранения конфигурации приложения"""
    package_name: str
    repository_url: str
    test_repo_mode: str
    output_image: str
    ascii_tree_mode: bool
    max_depth: int
    filter_substring: str

    def to_dict(self) -> dict:
        """Преобразование конфигурации в словарь для вывода"""
        return {
            'package_name': self.package_name,
            'repository_url': self.repository_url,
            'test_repo_mode': self.test_repo_mode,
            'output_image': self.output_image,
            'ascii_tree_mode': self.ascii_tree_mode,
            'max_depth': self.max_depth,
            'filter_substring': self.filter_substring
        }