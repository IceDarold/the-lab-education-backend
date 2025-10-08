import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aiofiles

from src.core.errors import ContentFileNotFoundError, SecurityError


@dataclass
class DirectoryScanResult:
    name: str
    type: Literal['file', 'directory']
    path: str


class FileSystemService:
    def __init__(self):
        self.content_root = Path('./content').resolve()

    async def ensure_content_root_exists(self):
        await asyncio.to_thread(self.content_root.mkdir, parents=True, exist_ok=True)

    async def read_file(self, relativePath: str) -> str:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists):
            raise ContentFileNotFoundError(f"File not found: {relativePath}")
        async with aiofiles.open(absolute_path, 'r') as f:
            return await f.read()

    async def write_file(self, relativePath: str, content: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.parent.mkdir, parents=True, exist_ok=True)
        async with aiofiles.open(absolute_path, 'w') as f:
            await f.write(content)

    async def create_directory(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.mkdir, parents=True, exist_ok=True)

    async def delete_file(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_file):
            raise ContentFileNotFoundError(f"File not found: {relativePath}")
        await asyncio.to_thread(absolute_path.unlink)

    async def delete_directory(self, relativePath: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_dir):
            raise ContentFileNotFoundError(f"Directory not found: {relativePath}")
        await asyncio.to_thread(shutil.rmtree, absolute_path)

    async def rename_item(self, relativePath: str, newName: str):
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists):
            raise ContentFileNotFoundError(f"Item not found: {relativePath}")
        new_absolute_path = absolute_path.parent / newName
        if not str(new_absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        await asyncio.to_thread(absolute_path.rename, new_absolute_path)

    async def path_exists(self, relativePath: str) -> bool:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        return await asyncio.to_thread(absolute_path.exists)

    async def scan_directory(self, relativePath: str) -> list[DirectoryScanResult]:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        if not await asyncio.to_thread(absolute_path.exists) or not await asyncio.to_thread(absolute_path.is_dir):
            raise ContentFileNotFoundError(f"Directory not found: {relativePath}")
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