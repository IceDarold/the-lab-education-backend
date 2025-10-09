import asyncio
import yaml
from typing import Optional
from cachetools import TTLCache

from src.schemas.content_node import ContentNode
from src.services.file_system_service import FileSystemService


class ContentScannerService:
    def __init__(self, fs_service: FileSystemService):
        self.fs_service = fs_service
        self._cache = TTLCache(maxsize=1, ttl=3600)
        self._cache_lock = asyncio.Lock()

    async def build_content_tree(self) -> list[ContentNode]:
        """Scan content directory and build a cached hierarchical tree."""
        cache_key = "content_tree"
        async with self._cache_lock:
            cached_tree = self._cache.get(cache_key)
            if cached_tree is not None:
                return cached_tree

            items = await self.fs_service.scan_directory('courses')
            root_nodes = []
            for item in items:
                if item.type == 'directory':
                    node = await self._build_node(item.path)
                    if node:
                        root_nodes.append(node)

            self._cache[cache_key] = root_nodes
            return root_nodes

    async def _build_node(self, path: str) -> Optional[ContentNode]:
        items = await self.fs_service.scan_directory(path)
        # Check for config files
        config_path = None
        node_type = None
        title = None
        if any(item.name == '_course.yml' for item in items if item.type == 'file'):
            config_path = f"{path}/_course.yml"
            node_type = 'course'
        elif any(item.name == '_module.yml' for item in items if item.type == 'file'):
            config_path = f"{path}/_module.yml"
            node_type = 'module'
        else:
            # If no config, perhaps it's a directory with lessons, but according to task, only for dirs with config
            return None

        if config_path:
            try:
                content = await self.fs_service.read_file(config_path)
                data = yaml.safe_load(content)
                title = data.get('title', path.split('/')[-1])
            except Exception:
                title = path.split('/')[-1]

        node = ContentNode(
            type=node_type,
            name=title,
            path=path,
            config_path=config_path
        )

        # Add children
        children = []
        for item in items:
            if item.type == 'directory':
                child_node = await self._build_node(item.path)
                if child_node:
                    children.append(child_node)
            elif item.name.endswith('.lesson'):
                lesson_node = ContentNode(
                    type='lesson',
                    name=item.name.replace('.lesson', ''),
                    path=item.path
                )
                children.append(lesson_node)

        node.children = children
        return node

    async def get_course_lesson_slugs(self, course_slug: str) -> list[str]:
        """Return all lesson slugs for a given course, traversing nested modules."""
        tree = await self.build_content_tree()
        normalized_slug = course_slug.lower()

        def gather_lessons(node: ContentNode) -> list[str]:
            collected: list[str] = []
            for child in node.children or []:
                if child.type == 'lesson':
                    collected.append(child.name)
                else:
                    collected.extend(gather_lessons(child))
            return collected

        for course_node in tree:
            if course_node.type != 'course':
                continue
            path_slug = course_node.path.strip("/").split("/")[-1].lower()
            if path_slug == normalized_slug or course_node.name.lower() == normalized_slug:
                return gather_lessons(course_node)
        return []

    def clear_cache(self):
        self._cache.clear()
