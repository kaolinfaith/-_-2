from graph_base import DependencyGraph
from reverse_dependencies import ReverseDependencyFinder


class EnhancedDependencyGraph(DependencyGraph):

    """Расширенный класс графа с поддержкой обратных зависимостей"""

    def __init__(self, repository_url: str, max_depth: int = 3, filter_substring: str = ""):
        super().__init__(repository_url, max_depth, filter_substring)
        self.reverse_finder = ReverseDependencyFinder(self)

    def find_reverse_dependencies(self, target_package: str) -> Dict[str, List[str]]:
        """Находит обратные зависимости для целевого пакета"""
        return self.reverse_finder.find_reverse_dependencies(target_package)

    def print_reverse_dependencies(self, target_package: str):
        """Выводит обратные зависимости"""
        reverse_deps = self.find_reverse_dependencies(target_package)
        self.reverse_finder.print_reverse_dependencies(target_package, reverse_deps)