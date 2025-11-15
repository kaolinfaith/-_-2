import os
import re
from typing import Dict, List, Set
from errors import TestRepositoryError, FileNotFoundError


class TestRepositoryParser:
    """Парсер для тестовых репозиториев"""

    def __init__(self, repository_path: str):
        self.repository_path = repository_path
        self.dependency_cache = {}
        self.all_packages_cache = None

    def get_all_packages(self) -> List[str]:
        """Возвращает все пакеты из тестового репозитория"""
        if self.all_packages_cache is not None:
            return self.all_packages_cache

        packages = set()
        try:
            with open(self.repository_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package_part = line.split(':')[0].strip()
                        if package_part and package_part.isupper():
                            packages.add(package_part)

            self.all_packages_cache = sorted(list(packages))
            return self.all_packages_cache

        except Exception as e:
            raise TestRepositoryError(f"Ошибка чтения списка пакетов: {e}")

    def get_dependencies(self, package_name: str) -> List[Dict]:
        """
        Получает зависимости из тестового репозитория

        Args:
            package_name: Имя пакета в формате A, B, C и т.д.

        Returns:
            List[Dict]: Список зависимостей
        """
        if not os.path.exists(self.repository_path):
            raise FileNotFoundError(f"Тестовый репозиторий не найден: {self.repository_path}")

        # Кэшируем результаты для производительности
        if package_name in self.dependency_cache:
            return self.dependency_cache[package_name]

        try:
            with open(self.repository_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем зависимости для указанного пакета
            pattern = rf"^{package_name}:\s*([A-Z,\s]+)$"
            match = re.search(pattern, content, re.MULTILINE)

            if not match:
                # Если пакет не найден, возвращаем пустой список
                self.dependency_cache[package_name] = []
                return []

            dependencies_str = match.group(1).strip()
            dependencies = [dep.strip() for dep in dependencies_str.split(',') if dep.strip()]

            # Преобразуем в стандартный формат
            result = []
            for dep in dependencies:
                result.append({
                    'groupId': 'test',
                    'artifactId': dep,
                    'version': '1.0.0',
                    'scope': 'compile'
                })

            self.dependency_cache[package_name] = result
            return result

        except Exception as e:
            raise TestRepositoryError(f"Ошибка чтения тестового репозитория: {e}")

    def validate_repository_format(self) -> bool:
        """Проверяет формат тестового репозитория"""
        try:
            with open(self.repository_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Игнорируем комментарии
                    if not re.match(r"^[A-Z]:\s*[A-Z,\s]*$", line):
                        raise TestRepositoryError(
                            f"Неверный формат в строке {line_num}: {line}"
                        )
            return True

        except Exception as e:
            raise TestRepositoryError(f"Ошибка валидации тестового репозитория: {e}")


class TestDependencyGraph:
    """Граф зависимостей для тестового режима"""

    def __init__(self, repository_path: str, max_depth: int = 3, filter_substring: str = ""):
        self.parser = TestRepositoryParser(repository_path)
        self.max_depth = max_depth
        self.filter_substring = filter_substring.lower()
        self.visited = set()
        self.dependency_tree = {}

    def build_graph(self, root_package: str) -> Dict:
        """Строит граф для тестового репозитория"""
        try:
            self.parser.validate_repository_format()

            self.visited.clear()
            self.dependency_tree.clear()

            print(f"Построение тестового графа для: {root_package}")
            print(f"Максимальная глубина: {self.max_depth}")
            print(f"Фильтр подстрок: '{self.filter_substring}'")

            self._bfs_recursive([root_package], current_depth=0)

            return self.dependency_tree

        except Exception as e:
            raise TestRepositoryError(f"Ошибка построения тестового графа: {e}")

    def _bfs_recursive(self, packages: List[str], current_depth: int, path: List[str] = None):
        """Рекурсивный BFS для тестового режима"""
        if current_depth >= self.max_depth:
            return

        if path is None:
            path = []

        next_level_packages = []

        for package in packages:
            if package in self.visited:
                if package in path:
                    cycle_path = " -> ".join(path + [package])
                    print(f"⚠️ Обнаружена циклическая зависимость: {cycle_path}")
                    raise CycleDetectedError(f"Циклическая зависимость: {cycle_path}")
                continue

            self.visited.add(package)

            # Пропускаем по фильтру
            if self.filter_substring and self.filter_substring in package.lower():
                print(f"↪️ Пропущен пакет по фильтру: {package}")
                continue

            try:
                dependencies = self.parser.get_dependencies(package)

                # Фильтруем зависимости
                filtered_deps = [
                    dep for dep in dependencies
                    if not self.filter_substring or self.filter_substring not in dep['artifactId'].lower()
                ]

                self.dependency_tree[package] = filtered_deps

                for dep in filtered_deps:
                    next_level_packages.append(dep['artifactId'])

                print(f"📦 Обработан {package} (глубина {current_depth}): {len(filtered_deps)} зависимостей")

            except Exception as e:
                print(f"⚠️ Ошибка при обработке пакета {package}: {e}")
                self.dependency_tree[package] = []

        # Рекурсивный вызов для следующего уровня
        if next_level_packages:
            for pkg in next_level_packages:
                new_path = path + [package] if package not in path else path.copy()
                try:
                    self._bfs_recursive([pkg], current_depth + 1, new_path)
                except CycleDetectedError:
                    continue

    def print_graph(self):
        """Выводит тестовый граф"""
        if not self.dependency_tree:
            print("Тестовый граф пуст")
            return

        print("\n" + "=" * 60)
        print("ТЕСТОВЫЙ ГРАФ ЗАВИСИМОСТЕЙ")
        print("=" * 60)

        for package, dependencies in self.dependency_tree.items():
            print(f"\n📦 {package}")
            for dep in dependencies:
                print(f"   └── {dep['artifactId']}")

        stats = self.get_statistics()
        print(f"\n📊 Статистика:")
        print(f"   Всего пакетов: {stats['total_packages']}")
        print(f"   Всего зависимостей: {stats['total_dependencies']}")
        print(f"   Макс. глубина: {stats['max_depth_reached']}")
        print(f"   Фильтр: '{stats['filtered_by_substring']}'")
        print("=" * 60)

    def get_statistics(self) -> Dict:
        """Статистика для тестового графа"""
        total_packages = len(self.dependency_tree)
        total_dependencies = sum(len(deps) for deps in self.dependency_tree.values())

        return {
            'total_packages': total_packages,
            'total_dependencies': total_dependencies,
            'max_depth_reached': self.max_depth,
            'filtered_by_substring': self.filter_substring
        }