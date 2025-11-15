from typing import Dict, List, Set, Optional
from collections import deque
from errors import ReverseDependencyError


class ReverseDependencyFinder:
    """Класс для поиска обратных зависимостей"""

    def __init__(self, dependency_graph):
        """
        Args:
            dependency_graph: Объект графа зависимостей
        """
        self.dependency_graph = dependency_graph
        self.reverse_deps = {}

    def find_reverse_dependencies(self, target_package: str) -> Dict[str, List[List[str]]]:
        """
        Находит все пакеты, которые зависят от целевого пакета

        Args:
            target_package: Целевой пакет для поиска обратных зависимостей

        Returns:
            Dict: Словарь с обратными зависимостями {пакет: [пути_зависимостей]}
        """
        try:
            self.reverse_deps.clear()

            # Определяем тип графа по его атрибутам
            if hasattr(self.dependency_graph, 'parser') and hasattr(self.dependency_graph.parser, 'repository_path'):
                return self._find_reverse_deps_test(target_package)
            else:
                return self._find_reverse_deps_real(target_package)

        except Exception as e:
            raise ReverseDependencyError(f"Ошибка поиска обратных зависимостей: {e}")

    def _find_reverse_deps_real(self, target_package: str) -> Dict[str, List[List[str]]]:
        """Поиск обратных зависимостей для реального репозитория"""
        # Сначала строим полный граф от корневого пакета
        root_package = self._get_root_package()
        graph_data = self.dependency_graph.build_graph(root_package)

        # Ищем обратные зависимости в построенном графе
        return self._analyze_reverse_dependencies(graph_data, target_package)

    def _find_reverse_deps_test(self, target_package: str) -> Dict[str, List[List[str]]]:
        """Поиск обратных зависимостей для тестового репозитория"""
        # Для тестового репозитория строим граф от всех возможных корней
        all_packages = self._get_all_test_packages()
        all_reverse_deps = {}

        for root_package in all_packages:
            try:
                graph_data = self.dependency_graph.build_graph(root_package)
                reverse_deps = self._analyze_reverse_dependencies(graph_data, target_package)
                all_reverse_deps.update(reverse_deps)
            except Exception as e:
                continue  # Пропускаем пакеты, для которых не удалось построить граф

        return all_reverse_deps

    def _get_root_package(self) -> str:
        """Получает корневой пакет из конфигурации графа"""
        # Для реального графа используем первый пакет из visited
        if hasattr(self.dependency_graph, 'visited') and self.dependency_graph.visited:
            return next(iter(self.dependency_graph.visited))
        return "unknown:unknown:1.0.0"

    def _get_all_test_packages(self) -> List[str]:
        """Получает все пакеты из тестового репозитория"""
        try:
            # Читаем тестовый репозиторий и извлекаем все пакеты
            repository_path = self.dependency_graph.parser.repository_path
            with open(repository_path, 'r', encoding='utf-8') as f:
                content = f.read()

            packages = set()
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    package_part = line.split(':')[0].strip()
                    if package_part and package_part.isupper():
                        packages.add(package_part)

            return list(packages)
        except Exception:
            return ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # Fallback

    def _analyze_reverse_dependencies(self, graph_data: Dict, target_package: str) -> Dict[str, List[List[str]]]:
        """
        Анализирует граф и находит обратные зависимости

        Args:
            graph_data: Данные графа зависимостей
            target_package: Целевой пакет

        Returns:
            Dict: Обратные зависимости
        """
        reverse_deps = {}

        for package, dependencies in graph_data.items():
            # Проверяем, зависит ли текущий пакет от целевого
            paths = self._find_dependency_paths(package, target_package, graph_data)
            if paths:
                reverse_deps[package] = paths

        return reverse_deps

    def _find_dependency_paths(self, start_package: str, target_package: str,
                               graph_data: Dict) -> List[List[str]]:
        """
        Находит все пути от start_package до target_package

        Args:
            start_package: Начальный пакет
            target_package: Целевой пакет
            graph_data: Данные графа

        Returns:
            List: Список путей зависимостей
        """
        paths = []
        visited = set()

        def dfs(current: str, path: List[str]):
            if current in visited:
                return

            visited.add(current)
            current_path = path + [current]

            # Если нашли целевой пакет, сохраняем путь
            if current == target_package and len(current_path) > 1:
                paths.append(current_path.copy())
                return

            # Рекурсивно ищем в зависимостях
            if current in graph_data:
                for dep in graph_data[current]:
                    dep_key = self._get_dependency_key(dep)
                    if dep_key not in current_path:  # Избегаем циклов
                        dfs(dep_key, current_path)

            visited.remove(current)

        dfs(start_package, [])
        return paths

    def _get_dependency_key(self, dep: Dict) -> str:
        """Создает ключ для зависимости"""
        # Определяем тип по наличию артефакта
        if 'artifactId' in dep and not dep.get('groupId'):
            return dep['artifactId']  # Тестовый формат
        else:
            return f"{dep['groupId']}:{dep['artifactId']}:{dep['version']}"  # Maven формат

    def print_reverse_dependencies(self, target_package: str, reverse_deps: Dict[str, List[List[str]]]):
        """Выводит обратные зависимости в читаемом формате"""
        if not reverse_deps:
            print(f"\nНет пакетов, зависящих от: {target_package}")
            return


        print(f"ОБРАТНЫЕ ЗАВИСИМОСТИ ДЛЯ: {target_package}")


        total_dependents = len(reverse_deps)
        total_paths = sum(len(paths) for paths in reverse_deps.values())

        print(f"Найдено пакетов, зависящих от '{target_package}': {total_dependents}")
        print(f"Всего путей зависимостей: {total_paths}")


        for i, (dependent_package, paths) in enumerate(reverse_deps.items(), 1):
            print(f"\n{i}.{dependent_package} зависит от {target_package}:")

            for j, path in enumerate(paths, 1):
                path_str = " → ".join(path)
                print(f"   {j}) {path_str}")

