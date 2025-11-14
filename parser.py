import configparser
import os
from config import AppConfig
from errors import ConfigError, FileNotFoundError


class ConfigParser:

    def __init__(self):
        self.parser = configparser.ConfigParser()

    def parse_file(self, file_path: str) -> AppConfig:
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Конфигурационный файл не найден: {file_path}")

            content = self._read_file_with_encoding(file_path)

            # Парсим содержимое как строку
            self.parser.read_string(content)

            # Проверяем, что файл был прочитан
            if not self.parser.sections():
                raise ConfigError(f"Не удалось прочитать файл или файл пустой: {file_path}")

            return self._create_config()

        except configparser.Error as e:
            raise ConfigError(f"Ошибка парсинга INI-файла: {e}")
        except Exception as e:
            raise ConfigError(f"Неожиданная ошибка при чтении конфигурации: {e}")

    def _read_file_with_encoding(self, file_path: str) -> str:
        """Читает файл, пробуя разные кодировки"""
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1', 'cp866', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    print(f"Файл успешно прочитан с кодировкой: {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue

        # Если ни одна кодировка не подошла, пробуем бинарное чтение с заменой ошибок
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
                print("Файл прочитан в бинарном режиме с заменой ошибок")
                return content
        except Exception as e:
            raise ConfigError(f"Не удалось прочитать файл ни в одной из кодировок: {e}")

    def _create_config(self) -> AppConfig:
        """Создает объект конфигурации из распарсенных данных"""
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
        """Безопасное получение строкового параметра"""
        try:
            value = self.parser.get(section, option, fallback=default)
            return value.strip() if isinstance(value, str) else default
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def _get_int(self, section: str, option: str, default: int) -> int:
        """Безопасное получение целочисленного параметра"""
        try:
            return self.parser.getint(section, option, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def _get_boolean(self, section: str, option: str, default: bool) -> bool:
        """Безопасное получение булевого параметра"""
        try:
            return self.parser.getboolean(section, option, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default