import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aiofiles

from src.core.errors import ContentFileNotFoundError, FileSystemOperationError, SecurityError
from src.core.logging import get_logger


@dataclass
class DirectoryScanResult:
    name: str
    type: Literal['file', 'directory']
    path: str


class FileSystemService:
    def __init__(self):
        self.content_root = Path('./content').resolve()
        self.logger = get_logger(__name__)

    async def ensure_content_root_exists(self):
        self.logger.debug(f"Ensuring content root exists: {self.content_root}")
        try:
            await asyncio.to_thread(self.content_root.mkdir, parents=True, exist_ok=True)
            self.logger.info(f"Content root verified/created: {self.content_root}")
        except OSError as e:
            self.logger.error(f"Failed to create content root directory {self.content_root}: {str(e)}")
            raise FileSystemOperationError(f"Failed to create content root directory: {str(e)}")

    async def read_file(self, relativePath: str) -> str:
        self.logger.debug(f"Reading file: {relativePath}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted access outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        # Check if file exists
        if not await asyncio.to_thread(absolute_path.exists):
            self.logger.warning(f"File not found: {relativePath}")
            raise ContentFileNotFoundError(f"File not found: {relativePath}")

        try:
            async with aiofiles.open(absolute_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            self.logger.info(f"Successfully read file: {relativePath} ({len(content)} characters)")
            return content
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"File '{relativePath}' contains invalid encoding. Expected UTF-8 text file.")
        except OSError as e:
            self.logger.error(f"OS error reading file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to read file '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error reading file '{relativePath}': {str(e)}")

    async def write_file(self, relativePath: str, content: str):
        self.logger.debug(f"Writing file: {relativePath} ({len(content)} characters)")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted write outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        # Ensure parent directory exists
        try:
            await asyncio.to_thread(absolute_path.parent.mkdir, parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create parent directory for {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to create directory for file '{relativePath}': {str(e)}")

        try:
            async with aiofiles.open(absolute_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            self.logger.info(f"Successfully wrote file: {relativePath}")
        except OSError as e:
            self.logger.error(f"OS error writing file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to write file '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error writing file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error writing file '{relativePath}': {str(e)}")

    async def create_directory(self, relativePath: str):
        self.logger.debug(f"Creating directory: {relativePath}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted directory creation outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        try:
            await asyncio.to_thread(absolute_path.mkdir, parents=True, exist_ok=True)
            self.logger.info(f"Successfully created directory: {relativePath}")
        except OSError as e:
            self.logger.error(f"OS error creating directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to create directory '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error creating directory '{relativePath}': {str(e)}")

    async def delete_file(self, relativePath: str):
        self.logger.debug(f"Deleting file: {relativePath}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted file deletion outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        # Check if file exists and is a file
        if not await asyncio.to_thread(absolute_path.exists):
            self.logger.warning(f"File not found for deletion: {relativePath}")
            raise ContentFileNotFoundError(f"File not found: {relativePath}")
        if not await asyncio.to_thread(absolute_path.is_file):
            self.logger.warning(f"Path is not a file: {relativePath}")
            raise FileSystemOperationError(f"Path is not a file: {relativePath}")

        try:
            await asyncio.to_thread(absolute_path.unlink)
            self.logger.info(f"Successfully deleted file: {relativePath}")
        except OSError as e:
            self.logger.error(f"OS error deleting file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to delete file '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting file {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error deleting file '{relativePath}': {str(e)}")

    async def delete_directory(self, relativePath: str):
        self.logger.debug(f"Deleting directory: {relativePath}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted directory deletion outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        # Check if directory exists
        if not await asyncio.to_thread(absolute_path.exists):
            self.logger.warning(f"Directory not found for deletion: {relativePath}")
            raise ContentFileNotFoundError(f"Directory not found: {relativePath}")
        if not await asyncio.to_thread(absolute_path.is_dir):
            self.logger.warning(f"Path is not a directory: {relativePath}")
            raise FileSystemOperationError(f"Path is not a directory: {relativePath}")

        try:
            await asyncio.to_thread(shutil.rmtree, absolute_path)
            self.logger.info(f"Successfully deleted directory: {relativePath}")
        except OSError as e:
            self.logger.error(f"OS error deleting directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to delete directory '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error deleting directory '{relativePath}': {str(e)}")

    async def rename_item(self, relativePath: str, newName: str):
        self.logger.debug(f"Renaming item: {relativePath} to {newName}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check for source path
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted rename from outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for source '{relativePath}'")

        # Check if source exists
        if not await asyncio.to_thread(absolute_path.exists):
            self.logger.warning(f"Item not found for rename: {relativePath}")
            raise ContentFileNotFoundError(f"Item not found: {relativePath}")

        new_absolute_path = absolute_path.parent / newName

        # Security check for destination path
        if not str(new_absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted rename to outside content root: {newName}")
            raise SecurityError(f"Access denied: path traversal attempt detected for destination '{newName}'")

        try:
            await asyncio.to_thread(absolute_path.rename, new_absolute_path)
            self.logger.info(f"Successfully renamed item: {relativePath} to {newName}")
        except OSError as e:
            self.logger.error(f"OS error renaming {relativePath} to {newName}: {str(e)}")
            raise FileSystemOperationError(f"Failed to rename item '{relativePath}' to '{newName}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error renaming {relativePath} to {newName}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error renaming item '{relativePath}' to '{newName}': {str(e)}")

    async def path_exists(self, relativePath: str) -> bool:
        absolute_path = (self.content_root / relativePath).resolve()
        if not str(absolute_path).startswith(str(self.content_root)):
            raise SecurityError("Access denied")
        return await asyncio.to_thread(absolute_path.exists)

    async def scan_directory(self, relativePath: str) -> list[DirectoryScanResult]:
        self.logger.debug(f"Scanning directory: {relativePath}")
        absolute_path = (self.content_root / relativePath).resolve()

        # Security check
        if not str(absolute_path).startswith(str(self.content_root)):
            self.logger.warning(f"Security violation: attempted directory scan outside content root: {relativePath}")
            raise SecurityError(f"Access denied: path traversal attempt detected for '{relativePath}'")

        # Check if directory exists
        if not await asyncio.to_thread(absolute_path.exists):
            self.logger.warning(f"Directory not found for scan: {relativePath}")
            raise ContentFileNotFoundError(f"Directory not found: {relativePath}")
        if not await asyncio.to_thread(absolute_path.is_dir):
            self.logger.warning(f"Path is not a directory for scan: {relativePath}")
            raise FileSystemOperationError(f"Path is not a directory: {relativePath}")

        try:
            items = await asyncio.to_thread(list, absolute_path.iterdir())
            results = []
            for item in items:
                item_type = 'directory' if item.is_dir() else 'file'
                results.append(DirectoryScanResult(
                    name=item.name,
                    type=item_type,
                    path=str(item.relative_to(self.content_root))
                ))
            self.logger.info(f"Successfully scanned directory: {relativePath} ({len(results)} items)")
            return results
        except OSError as e:
            self.logger.error(f"OS error scanning directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Failed to scan directory '{relativePath}': {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error scanning directory {relativePath}: {str(e)}")
            raise FileSystemOperationError(f"Unexpected error scanning directory '{relativePath}': {str(e)}")