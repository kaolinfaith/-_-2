import sys
import os
from config import AppConfig
from parser import ConfigParser
from validator import ConfigValidator
from maven_parser import MavenDependencyParser
from package_utils import PackageUtils
from errors import ConfigError, ValidationError, FileNotFoundError, InvalidValueError, DependencyError, NetworkError


class DependencyAnalyzer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.dependency_parser = None

    def run(self):
        try:
            print("Dependency Analyzer")
            self._load_configuration()
            self._validate_configuration()
            self._print_configuration()
            self._initialize_dependency_parser()

            # Этап 2: Получение и вывод зависимостей
            dependencies = self._get_package_dependencies()
            self._print_dependencies(dependencies)

            self._demonstrate_error_handling()
            self._execute_analysis(dependencies)

            print("Приложение успешно завершило работу!")
            return 0

        except FileNotFoundError as e:
            print(f"Ошибка файла: {e}", file=sys.stderr)
            return 1
        except ConfigError as e:
            print(f"Ошибка конфигурации: {e}", file=sys.stderr)
            return 2
        except ValidationError as e:
            print(f"Ошибка валидации: {e}", file=sys.stderr)
            return 3
        except InvalidValueError as e:
            print(f"Неверное значение параметра: {e}", file=sys.stderr)
            return 4
        except (DependencyError, NetworkError) as e:
            print(f"Ошибка получения зависимостей: {e}", file=sys.stderr)
            return 5
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            return 6

    def _load_configuration(self):
        print("Загрузка конфигурации...")
        parser = ConfigParser()
        self.config = parser.parse_file(self.config_path)
        print("Конфигурация успешно загружена")

    def _validate_configuration(self):
        print("Валидация параметров...")
        ConfigValidator.validate(self.config)
        print("Все параметры прошли валидацию")

    def _print_configuration(self):
        print("\nПАРАМЕТРЫ КОНФИГУРАЦИИ (ключ-значение):")

        config_dict = self.config.to_dict()
        for key, value in config_dict.items():
            print(f"{key:25}: {value}")

        print("=" * 50)

    def _initialize_dependency_parser(self):
        """Инициализирует парсер зависимостей"""
        print("\nИнициализация парсера Maven зависимостей...")
        self.dependency_parser = MavenDependencyParser(self.config.repository_url)
        print("Парсер успешно инициализирован")

    def _get_package_dependencies(self) -> list:
        """
        Получает зависимости указанного пакета

        Returns:
            list: Список зависимостей
        """
        print(f"\nПолучение зависимостей для пакета: {self.config.package_name}")

        try:
            # Парсим имя пакета
            group_id, artifact_id, version = PackageUtils.parse_package_name(self.config.package_name)
            PackageUtils.validate_maven_coordinates(group_id, artifact_id, version)

            print(f"GroupId: {group_id}, ArtifactId: {artifact_id}, Version: {version or 'latest'}")

            # Получаем актуальную версию если нужно
            resolved_version = self.dependency_parser.resolve_version(group_id, artifact_id, version)
            print(f"Используемая версия: {resolved_version}")

            # Получаем зависимости
            dependencies = self.dependency_parser.get_dependencies(group_id, artifact_id, resolved_version)

            print(f"Найдено зависимостей: {len(dependencies)}")
            return dependencies

        except Exception as e:
            raise DependencyError(f"Не удалось получить зависимости для {self.config.package_name}: {e}")

    def _print_dependencies(self, dependencies: list):
        """Выводит зависимости на экран (требование этапа 2)"""
        print("РЕЗУЛЬТАТЫ АНАЛИЗА ЗАВИСИМОСТЕЙ")

        output = PackageUtils.format_dependency_output(dependencies)
        print(output)


    def _demonstrate_error_handling(self):
        print("\nДемонстрация обработки ошибок...")

        test_errors = [
            ("Пустое имя пакета", AppConfig("", "url", "local", "test.png", False, 3, "")),
            ("Отрицательная глубина", AppConfig("test", "url", "local", "test.png", False, -1, "")),
            ("Неверный режим", AppConfig("test", "url", "invalid_mode", "test.png", False, 3, "")),
            ("Неверное расширение", AppConfig("test", "url", "local", "test.txt", False, 3, "")),
        ]

        for error_name, test_config in test_errors:
            try:
                ConfigValidator.validate(test_config)
            except (ValidationError, InvalidValueError) as e:
                print(f"   Обработана ошибка '{error_name}': {e}")
            except Exception as e:
                print(f"   Необработанная ошибка '{error_name}': {e}")

    def _execute_analysis(self, dependencies: list):
        print("\nЗапуск анализа зависимостей...")
        print(f"   Анализируем пакет: {self.config.package_name}")
        print(f"   Репозиторий: {self.config.repository_url}")
        print(f"   Режим: {self.config.test_repo_mode}")
        print(f"   Выходной файл: {self.config.output_image}")
        print(f"   Режим ASCII-дерева: {self.config.ascii_tree_mode}")
        print(f"   Макс. глубина: {self.config.max_depth}")
        print(f"   Фильтр: '{self.config.filter_substring}'")
        print(f"   Найдено прямых зависимостей: {len(dependencies)}")


def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <config_file.ini>")
        print("Пример: python main.py config.ini")
        sys.exit(1)

    config_path = sys.argv[1]
    app = DependencyAnalyzer(config_path)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())