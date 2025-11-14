import sys
import os
from config import AppConfig
from parser import ConfigParser
from validator import ConfigValidator
from maven_parser import MavenDependencyParser
from package_utils import PackageUtils
from graph import DependencyGraph
from test_repository import TestDependencyGraph, TestRepositoryParser
from errors import ConfigError, ValidationError, FileNotFoundError, InvalidValueError, DependencyError, NetworkError, \
    GraphError, CycleDetectedError, TestRepositoryError


class DependencyAnalyzer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.dependency_parser = None
        self.graph = None

    def run(self):
        try:
            print("Dependency Analyzer - Этап 3")
            self._load_configuration()
            self._validate_configuration()
            self._print_configuration()

            # Выбираем режим работы
            if self.config.test_repo_mode == 'test':
                self._process_test_repository()
            else:
                self._process_real_repository()

            self._demonstrate_error_handling()
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
        except (GraphError, CycleDetectedError, TestRepositoryError) as e:
            print(f"Ошибка построения графа: {e}", file=sys.stderr)
            return 6
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            return 7

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



    def _process_real_repository(self):
        """Обработка реального Maven репозитория"""
        print("\nРЕЖИМ: РЕАЛЬНЫЙ MAVEN РЕПОЗИТОРИЙ")

        # Получаем прямые зависимости (этап 2)
        dependencies = self._get_package_dependencies()
        self._print_dependencies(dependencies)

        # Строим полный граф (этап 3)
        self._build_dependency_graph()

    def _process_test_repository(self):
        """Обработка тестового репозитория"""
        print("\nРЕЖИМ: ТЕСТОВЫЙ РЕПОЗИТОРИЙ")

        if not os.path.exists(self.config.repository_url):
            raise TestRepositoryError(f"Тестовый репозиторий не найден: {self.config.repository_url}")

        # Парсим корневой пакет из тестового репозитория
        root_package = self.config.package_name.split(':')[
            0] if ':' in self.config.package_name else self.config.package_name

        # Строим тестовый граф
        test_graph = TestDependencyGraph(
            self.config.repository_url,
            self.config.max_depth,
            self.config.filter_substring
        )

        graph_data = test_graph.build_graph(root_package)
        test_graph.print_graph()

        # Демонстрация различных случаев
        self._demonstrate_test_cases()

    def _demonstrate_test_cases(self):
        """Демонстрация различных случаев работы с тестовым репозиторием"""
        print("ДЕМОНСТРАЦИЯ РАЗЛИЧНЫХ СЛУЧАЕВ")

        test_cases = [
            {"root": "A", "max_depth": 2, "filter": ""},
            {"root": "B", "max_depth": 3, "filter": "E"},
            {"root": "D", "max_depth": 4, "filter": ""},  # Циклическая зависимость
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\nТестовый случай {i}:")
            print(f"   Корень: {case['root']}")
            print(f"   Макс. глубина: {case['max_depth']}")
            print(f"   Фильтр: '{case['filter']}'")

            try:
                test_graph = TestDependencyGraph(
                    self.config.repository_url,
                    case['max_depth'],
                    case['filter']
                )
                graph_data = test_graph.build_graph(case['root'])
                print(f"   Успешно построен граф с {len(graph_data)} пакетами")
            except CycleDetectedError as e:
                print(f"   Обнаружена циклическая зависимость: {e}")
            except Exception as e:
                print(f"   Ошибка: {e}")

    def _get_package_dependencies(self):
        """Получает зависимости пакета (этап 2)"""
        print(f"\nПолучение зависимостей для пакета: {self.config.package_name}")

        self.dependency_parser = MavenDependencyParser(self.config.repository_url)

        group_id, artifact_id, version = PackageUtils.parse_package_name(self.config.package_name)
        PackageUtils.validate_maven_coordinates(group_id, artifact_id, version)

        resolved_version = self.dependency_parser.resolve_version(group_id, artifact_id, version)
        print(f"Используемая версия: {resolved_version}")

        dependencies = self.dependency_parser.get_dependencies(group_id, artifact_id, resolved_version)
        print(f"Найдено прямых зависимостей: {len(dependencies)}")

        return dependencies

    def _print_dependencies(self, dependencies: list):
        """Выводит зависимости (этап 2)"""

        print("ПРЯМЫЕ ЗАВИСИМОСТИ (Этап 2)")

        output = PackageUtils.format_dependency_output(dependencies)
        print(output)

    def _build_dependency_graph(self):
        """Строит полный граф зависимостей (этап 3)"""

        print("ПОСТРОЕНИЕ ПОЛНОГО ГРАФА ЗАВИСИМОСТЕЙ (Этап 3)")

        self.graph = DependencyGraph(
            self.config.repository_url,
            self.config.max_depth,
            self.config.filter_substring
        )

        try:
            graph_data = self.graph.build_graph(self.config.package_name)
            self.graph.print_graph()
        except CycleDetectedError as e:
            print(f"Обнаружена циклическая зависимость: {e}")
            print("Граф построен частично из-за циклических зависимостей")
            self.graph.print_graph()

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