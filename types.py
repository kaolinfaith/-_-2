from typing import Dict, List, Set, Optional

# Общие типы данных для всего приложения
Dependency = Dict[str, str]  # {'groupId': '', 'artifactId': '', 'version': '', 'scope': ''}
DependencyGraphData = Dict[str, List[Dependency]]
ReverseDependencies = Dict[str, List[List[str]]]