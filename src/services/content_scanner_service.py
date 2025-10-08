import yaml
from cachetools import cached, TTLCache

from src.schemas.content_node import ContentNode
from src.services.file_system_service import FileSystemService


class ContentScannerService:
    def __init__(self, fs_service: FileSystemService):
        self.fs_service = fs_service

    @cached(cache=TTLCache(maxsize=1, ttl=3600))
    async def build_content_tree(self) -> list[ContentNode]:
        # Scan the root directory (assuming 'courses' is the root for content)
        items = await self.fs_service.scanDirectory('courses')
        root_nodes = []
        for item in items:
            if item.type == 'directory':
                node = await self._build_node(item.path)
                if node:
                    root_nodes.append(node)
        return root_nodes

    async def _build_node(self, path: str) -> ContentNode | None:
        items = await self.fs_service.scanDirectory(path)
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
                content = await self.fs_service.readFile(config_path)
                data = yaml.safe_load(content)
                title = data.get('title', path.split('/')[-1])
            except Exception:
                title = path.split('/')[-1]

        node = ContentNode(
            type=node_type,
            name=title,
            path=path,
            configPath=config_path
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