import sys
import os
from config import AppConfig
from parser import ConfigParser
from validator import ConfigValidator
from errors import ConfigError, ValidationError, FileNotFoundError, InvalidValueError


class DependencyAnalyzer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None

    def run(self):

        try:
            print("Dependency Analyzer")
            self._load_configuration()
            self._validate_configuration()
            self._print_configuration()
            self._demonstrate_error_handling()
            self._execute_analysis()

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
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            return 5

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
        print("ПАРАМЕТРЫ КОНФИГУРАЦИИ (ключ-значение):")

        config_dict = self.config.to_dict()
        for key, value in config_dict.items():
            print(f"{key:25}: {value}")

    def _demonstrate_error_handling(self):
        print("\n Демонстрация обработки ошибок...")


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

    def _execute_analysis(self):
        print("\nЗапуск анализа зависимостей...")
        print(f"   Анализируем пакет: {self.config.package_name}")
        print(f"   Репозиторий: {self.config.repository_url}")
        print(f"   Режим: {self.config.test_repo_mode}")
        print(f"   Выходной файл: {self.config.output_image}")
        print(f"   Режим ASCII-дерева: {self.config.ascii_tree_mode}")
        print(f"   Макс. глубина: {self.config.max_depth}")
        print(f"   Фильтр: '{self.config.filter_substring}'")
        print("\n(Здесь будет реализована основная логика анализа зависимостей)")


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