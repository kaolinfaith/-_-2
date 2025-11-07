import configparser
import os
from config import AppConfig
from errors import ConfigError, FileNotFoundError


class ConfigParser:

    def __init__(self):
        self.parser = configparser.ConfigParser()

    def parse_file(self, file_path: str) -> AppConfig:
        try:
            # Проверка существования файла
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Конфигурационный файл не найден: {file_path}")

            read_files = self.parser.read(file_path)
            if not read_files:
                raise ConfigError(f"Не удалось прочитать файл: {file_path}")

            return self._create_config()

        except configparser.Error as e:
            raise ConfigError(f"Ошибка парсинга INI-файла: {e}")
        except Exception as e:
            raise ConfigError(f"Неожиданная ошибка при чтении конфигурации: {e}")

    def _create_config(self) -> AppConfig:

        package_name = self._get_string('Application', 'package_name', '')
        repository_url = self._get_string('Application', 'repository_url', '')
        test_repo_mode = self._get_string('Application', 'test_repo_mode', 'local')
        output_image = self._get_string('Application', 'output_image', 'dependency_graph.png')
        ascii_tree_mode = self._get_boolean('Application', 'ascii_tree_mode', False)
        max_depth = self._get_int('Application', 'max_depth', 3)
        filter_substring = self._get_string('Application', 'filter_substring', '')

        return AppConfig(
            package_name=package_name,
            repository_url=repository_url,
            test_repo_mode=test_repo_mode,
            output_image=output_image,
            ascii_tree_mode=ascii_tree_mode,
            max_depth=max_depth,
            filter_substring=filter_substring
        )

    def _get_string(self, section: str, option: str, default: str) -> str:

        try:
            return self.parser.get(section, option, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def _get_int(self, section: str, option: str, default: int) -> int:

        try:
            return self.parser.getint(section, option, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def _get_boolean(self, section: str, option: str, default: bool) -> bool:

        try:
            return self.parser.getboolean(section, option, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default