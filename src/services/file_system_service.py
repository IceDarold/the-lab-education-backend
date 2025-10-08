import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aiofiles

from src.core.errors import SecurityError


@dataclass
class DirectoryScanResult:
    name: str
    type: Literal['file', 'directory']
    path: str


class FileSystemService:
    def __init__(self):
        self.content_root = Path('./content').resolve()

    async def ensureContentRootExists(self):
        await asyncio.to_thread(self.content_root.mkdir, parents=True, exist_ok=True)

    async def readFile(self, relativePath: str) -> str:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists):
            raise FileNotFoundError(f"File not found: {relativePath}")
        async with aiofiles.open(absolute_path, 'r') as f:
            return await f.read()

    async def writeFile(self, relativePath: str, content: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.parent.mkdir, parents=True, exist_ok=True)
        async with aiofiles.open(absolute_path, 'w') as f:
            await f.write(content)

    async def createDirectory(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.mkdir, parents=True, exist_ok=True)

    async def deleteFile(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_file):
            raise FileNotFoundError(f"File not found: {relativePath}")
        await asyncio.to_thread(absolute_path.unlink)

    async def deleteDirectory(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_dir):
            raise FileNotFoundError(f"Directory not found: {relativePath}")
        await asyncio.to_thread(shutil.rmtree, absolute_path)

    async def renameItem(self, relativePath: str, newName: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists):
            raise FileNotFoundError(f"Item not found: {relativePath}")
        new_absolute_path = absolute_path.parent / newName
        if not str(new_absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.rename, new_absolute_path)

    async def pathExists(self, relativePath: str) -> bool:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        return await asyncio.to_thread(absolute_path.exists)

    async def scanDirectory(self, relativePath: str) -> list[DirectoryScanResult]:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_dir):
            raise FileNotFoundError(f"Directory not found: {relativePath}")
        items = await asyncio.to_thread(list, absolute_path.iterdir())
        results = []
        for item in items:
            item_type = 'directory' if item.is_dir() else 'file'
            results.append(DirectoryScanResult(
                name=item.name,
                type=item_type,
                path=str(item.relative_to(self.content_root))
            ))
        return results