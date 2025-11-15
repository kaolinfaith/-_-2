from typing import Dict, List, Set, Optional
from collections import deque
from errors import CycleDetectedError, GraphError
from maven_parser import MavenDependencyParser
from package_utils import PackageUtils


class DependencyGraph:
    """Класс для построения графа зависимостей с использованием BFS"""

    def __init__(self, repository_url: str, max_depth: int = 3, filter_substring: str = ""):
        self.parser = MavenDependencyParser(repository_url)
        self.max_depth = max_depth
        self.filter_substring = filter_substring.lower()
        self.visited = set()
        self.dependency_tree = {}

    def build_graph(self, root_package: str) -> Dict:
        """
        Строит граф зависимостей используя BFS с рекурсией

        Args:
            root_package: Корневой пакет в формате groupId:artifactId:version

        Returns:
            Dict: Граф зависимостей

        Raises:
            CycleDetectedError: При обнаружении циклических зависимостей
            GraphError: При других ошибках построения графа
        """
        try:
            self.visited.clear()
            self.dependency_tree.clear()

            group_id, artifact_id, version = PackageUtils.parse_package_name(root_package)
            resolved_version = self.parser.resolve_version(group_id, artifact_id, version)
            root_key = f"{group_id}:{artifact_id}:{resolved_version}"

            print(f"Построение графа зависимостей для: {root_key}")
            print(f"Максимальная глубина: {self.max_depth}")
            print(f"Фильтр подстрок: '{self.filter_substring}'")

            # Запускаем рекурсивный BFS
            self._bfs_recursive([root_key], current_depth=0)

            return self.dependency_tree

        except Exception as e:
            raise GraphError(f"Ошибка построения графа: {e}")

    def _bfs_recursive(self, packages: List[str], current_depth: int, path: List[str] = None):
        """
        Рекурсивный BFS для обхода зависимостей

        Args:
            packages: Список пакетов для обработки на текущем уровне
            current_depth: Текущая глубина обхода
            path: Текущий путь обхода для обнаружения циклов
        """
        if current_depth >= self.max_depth:
            return

        if path is None:
            path = []

        next_level_packages = []

        for package in packages:
            if package in self.visited:
                # Проверяем циклы
                if package in path:
                    cycle_path = " -> ".join(path + [package])
                    print(f"Обнаружена циклическая зависимость: {cycle_path}")
                    raise CycleDetectedError(f"Циклическая зависимость: {cycle_path}")
                continue

            self.visited.add(package)

            # Пропускаем пакеты по фильтру
            if self.filter_substring and self.filter_substring in package.lower():
                print(f"Пропущен пакет по фильтру: {package}")
                continue

            try:
                # Получаем зависимости текущего пакета
                group_id, artifact_id, version = PackageUtils.parse_package_name(package)
                dependencies = self.parser.get_dependencies(group_id, artifact_id, version)

                # Фильтруем зависимости и проверяем версии
                filtered_deps = []
                for dep in dependencies:
                    # Пропускаем зависимости с неразрешенными версиями
                    if not PackageUtils.is_version_resolved(dep['version']):
                        print(
                            f" Пропущена зависимость с неразрешенной версией: {dep['groupId']}:{dep['artifactId']}:{dep['version']}")
                        continue

                    # Применяем фильтр по подстроке
                    if not self.filter_substring or self.filter_substring not in f"{dep['groupId']}:{dep['artifactId']}".lower():
                        filtered_deps.append(dep)

                # Сохраняем в граф
                self.dependency_tree[package] = filtered_deps

                # Формируем список для следующего уровня
                for dep in filtered_deps:
                    dep_key = f"{dep['groupId']}:{dep['artifactId']}:{dep['version']}"
                    next_level_packages.append(dep_key)

                print(f"Обработан {package} (глубина {current_depth}): {len(filtered_deps)} зависимостей")

            except Exception as e:
                print(f"Ошибка при обработке пакета {package}: {e}")
                self.dependency_tree[package] = []

        # Рекурсивный вызов для следующего уровня
        if next_level_packages:
            for pkg in next_level_packages:
                new_path = path + [package] if package not in path else path.copy()
                try:
                    self._bfs_recursive([pkg], current_depth + 1, new_path)
                except CycleDetectedError:
                    # Продолжаем обход после обнаружения цикла
                    continue

    def get_statistics(self) -> Dict:
        """Возвращает статистику по графу"""
        total_packages = len(self.dependency_tree)
        total_dependencies = sum(len(deps) for deps in self.dependency_tree.values())

        return {
            'total_packages': total_packages,
            'total_dependencies': total_dependencies,
            'max_depth_reached': self.max_depth,
            'filtered_by_substring': self.filter_substring
        }

    def print_graph(self):
        """Выводит граф в читаемом формате"""
        if not self.dependency_tree:
            print("Граф пуст")
            return

        print("ГРАФ ЗАВИСИМОСТЕЙ")

        for package, dependencies in self.dependency_tree.items():
            print(f"\n {package}")
            if dependencies:
                for dep in dependencies:
                    scope_info = f" ({dep['scope']})" if dep.get('scope') and dep['scope'] != 'compile' else ""
                    print(f"   └── {dep['groupId']}:{dep['artifactId']}:{dep['version']}{scope_info}")
            else:
                print("   └── (нет зависимостей)")

        stats = self.get_statistics()
        print(f"\n Статистика:")
        print(f"   Всего пакетов: {stats['total_packages']}")
        print(f"   Всего зависимостей: {stats['total_dependencies']}")
        print(f"   Макс. глубина: {stats['max_depth_reached']}")
        print(f"   Фильтр: '{stats['filtered_by_substring']}'")