import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
from urllib.parse import urljoin
from typing import List, Dict, Optional
import re
from errors import DependencyError, NetworkError


class MavenDependencyParser:
    """Парсер для извлечения зависимостей Maven пакетов"""

    def __init__(self, repository_url: str = "https://repo1.maven.org/maven2/"):
        self.repository_url = repository_url.rstrip('/') + '/'
        self.properties_cache = {}

    def get_dependencies(self, group_id: str, artifact_id: str, version: str) -> List[Dict[str, str]]:
        """
        Получает прямые зависимости Maven пакета

        Args:
            group_id: Group ID пакета (например, 'junit')
            artifact_id: Artifact ID пакета (например, 'junit')
            version: Версия пакета (например, '4.13.2')

        Returns:
            List[Dict]: Список зависимостей с ключами groupId, artifactId, version, scope

        Raises:
            NetworkError: Ошибки сети или доступа к репозиторию
            DependencyError: Ошибки парсинга зависимостей
        """
        try:
            # Получаем POM файл
            pom_content = self._download_pom_file(group_id, artifact_id, version)

            # Парсим свойства и зависимости из POM
            properties = self._parse_properties_from_pom(pom_content)
            dependencies = self._parse_dependencies_from_pom(pom_content, properties)

            return dependencies

        except urllib.error.URLError as e:
            print(f"Сетевая ошибка для {group_id}:{artifact_id}:{version}: {e}")
            return []
        except ET.ParseError as e:
            print(f"Ошибка парсинга POM для {group_id}:{artifact_id}:{version}: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка для {group_id}:{artifact_id}:{version}: {e}")
            return []

    def _download_pom_file(self, group_id: str, artifact_id: str, version: str) -> str:
        """Скачивает POM файл из репозитория"""
        pom_url = self._build_pom_url(group_id, artifact_id, version)

        try:
            with urllib.request.urlopen(pom_url) as response:
                content = response.read().decode('utf-8')
                print(f"Успешно загружен POM: {pom_url}")
                return content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DependencyError(f"POM файл не найден: {pom_url}")
            else:
                raise NetworkError(f"HTTP ошибка {e.code}: {e.reason}")

    def _build_pom_url(self, group_id: str, artifact_id: str, version: str) -> str:
        """Строит URL для POM файла"""
        group_path = group_id.replace('.', '/')
        filename = f"{artifact_id}-{version}.pom"

        return f"{self.repository_url}{group_path}/{artifact_id}/{version}/{filename}"

    def _parse_properties_from_pom(self, pom_content: str) -> Dict[str, str]:
        """Парсит свойства из POM файла"""
        properties = {}

        try:
            root = ET.fromstring(pom_content)

            # Находим секцию properties
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            properties_elem = root.find('.//maven:properties', namespace)

            if properties_elem is not None:
                for prop_elem in properties_elem:
                    tag = prop_elem.tag.split('}')[-1]  # Убираем namespace
                    if prop_elem.text:
                        properties[tag] = prop_elem.text

        except Exception:
            # Пробуем парсить без namespace
            try:
                root = ET.fromstring(pom_content)
                properties_elem = root.find('.//properties')

                if properties_elem is not None:
                    for prop_elem in properties_elem:
                        if prop_elem.text:
                            properties[prop_elem.tag] = prop_elem.text
            except Exception:
                pass

        return properties

    def _parse_dependencies_from_pom(self, pom_content: str, properties: Dict[str, str]) -> List[Dict[str, str]]:
        """Парсит зависимости из содержимого POM файла с учетом свойств"""
        dependencies = []

        try:
            root = ET.fromstring(pom_content)

            # Находим все зависимости
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            dependencies_elem = root.find('.//maven:dependencies', namespace)

            if dependencies_elem is not None:
                for dep_elem in dependencies_elem.findall('maven:dependency', namespace):
                    dependency = {
                        'groupId': self._get_element_text(dep_elem, 'maven:groupId', namespace),
                        'artifactId': self._get_element_text(dep_elem, 'maven:artifactId', namespace),
                        'version': self._get_element_text(dep_elem, 'maven:version', namespace),
                        'scope': self._get_element_text(dep_elem, 'maven:scope', namespace) or 'compile'
                    }

                    # Заменяем переменные в версии
                    if dependency['version'] and dependency['version'].startswith('${'):
                        dependency['version'] = self._resolve_property(dependency['version'], properties)

                    # Добавляем только если есть обязательные поля и версия определена
                    if dependency['groupId'] and dependency['artifactId'] and dependency['version']:
                        dependencies.append(dependency)
                    else:
                        print(f"Пропущена зависимость с неполными данными: {dependency}")

            return dependencies

        except ET.ParseError:
            # Пробуем парсить без namespace для совместимости
            return self._parse_dependencies_without_namespace(pom_content, properties)

    def _parse_dependencies_without_namespace(self, pom_content: str, properties: Dict[str, str]) -> List[
        Dict[str, str]]:
        """Парсит зависимости без использования namespace (fallback)"""
        dependencies = []

        root = ET.fromstring(pom_content)
        dependencies_elem = root.find('.//dependencies')

        if dependencies_elem is not None:
            for dep_elem in dependencies_elem.findall('dependency'):
                dependency = {
                    'groupId': self._get_element_text_simple(dep_elem, 'groupId'),
                    'artifactId': self._get_element_text_simple(dep_elem, 'artifactId'),
                    'version': self._get_element_text_simple(dep_elem, 'version'),
                    'scope': self._get_element_text_simple(dep_elem, 'scope') or 'compile'
                }

                # Заменяем переменные в версии
                if dependency['version'] and dependency['version'].startswith('${'):
                    dependency['version'] = self._resolve_property(dependency['version'], properties)

                if dependency['groupId'] and dependency['artifactId'] and dependency['version']:
                    dependencies.append(dependency)
                else:
                    print(f"Пропущена зависимость с неполными данными: {dependency}")

        return dependencies

    def _resolve_property(self, property_ref: str, properties: Dict[str, str]) -> str:
        """Разрешает Maven свойства вида ${property.name}"""
        if not property_ref.startswith('${') or not property_ref.endswith('}'):
            return property_ref

        property_name = property_ref[2:-1]  # Убираем ${ и }

        # Ищем свойство в переданных свойствах
        if property_name in properties:
            return properties[property_name]

        # Пробуем найти версию по имени артефакта
        if property_name.endswith('Version'):
            artifact_name = property_name.replace('Version', '').lower()
            # Пробуем найти соответствующую версию в свойствах
            for key, value in properties.items():
                if key.lower().endswith('version') and artifact_name in key.lower():
                    return value

        print(f"Не удалось разрешить свойство: {property_ref}")
        return property_ref  # Возвращаем как есть, если не смогли разрешить

    def _get_element_text(self, parent, tag: str, namespace: Dict[str, str]) -> Optional[str]:
        """Получает текст элемента с учетом namespace"""
        elem = parent.find(tag, namespace)
        return elem.text if elem is not None else None

    def _get_element_text_simple(self, parent, tag: str) -> Optional[str]:
        """Получает текст элемента без namespace"""
        elem = parent.find(tag)
        return elem.text if elem is not None else None

    def resolve_version(self, group_id: str, artifact_id: str, version: str = None) -> str:
        """
        Разрешает версию пакета (получает актуальную версию если указана LATEST или RELEASE)

        Args:
            group_id: Group ID пакета
            artifact_id: Artifact ID пакета
            version: Версия или специальное значение (LATEST, RELEASE)

        Returns:
            str: Конкретная версия пакета
        """
        if version and version.upper() in ['LATEST', 'RELEASE']:
            return self._get_latest_version(group_id, artifact_id)
        return version or self._get_latest_version(group_id, artifact_id)

    def _get_latest_version(self, group_id: str, artifact_id: str) -> str:
        """Получает последнюю версию пакета из maven-metadata.xml"""
        metadata_url = self._build_metadata_url(group_id, artifact_id)

        try:
            with urllib.request.urlopen(metadata_url) as response:
                metadata_content = response.read().decode('utf-8')
                return self._parse_latest_version(metadata_content)
        except urllib.error.HTTPError:
            raise DependencyError(f"Не удалось получить метаданные для {group_id}:{artifact_id}")

    def _build_metadata_url(self, group_id: str, artifact_id: str) -> str:
        """Строит URL для maven-metadata.xml"""
        group_path = group_id.replace('.', '/')
        return f"{self.repository_url}{group_path}/{artifact_id}/maven-metadata.xml"

    def _parse_latest_version(self, metadata_content: str) -> str:
        """Парсит последнюю версию из maven-metadata.xml"""
        root = ET.fromstring(metadata_content)

        # Пробуем найти latest версию
        latest_elem = root.find('.//latest')
        if latest_elem is not None and latest_elem.text:
            return latest_elem.text

        # Если latest нет, берем первую версию из списка
        versions_elem = root.find('.//versions')
        if versions_elem is not None:
            version_elems = versions_elem.findall('version')
            if version_elems:
                return version_elems[-1].text  # Последняя версия в списке

        raise DependencyError("Не удалось определить версию пакета")