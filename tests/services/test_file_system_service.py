import pytest
from pathlib import Path
from src.services.file_system_service import FileSystemService, DirectoryScanResult
from src.core.errors import SecurityError


pytestmark = pytest.mark.asyncio


class TestFileSystemService:
    def setup_method(self, tmp_path):
        self.tmp_path = tmp_path
        self.content_root = tmp_path / 'content'
        self.service = FileSystemService()
        self.service.content_root = self.content_root

    async def test_successful_read_write_file(self):
        await self.service.writeFile('test.txt', 'Hello World')
        content = await self.service.readFile('test.txt')
        assert content == 'Hello World'

    async def test_read_non_existent_file_raises_file_not_found_error(self):
        with pytest.raises(FileNotFoundError):
            await self.service.readFile('nonexistent.txt')

    async def test_recursive_create_directory(self):
        await self.service.createDirectory('a/b/c')
        assert (self.content_root / 'a' / 'b' / 'c').exists()
        assert (self.content_root / 'a' / 'b' / 'c').is_dir()

    async def test_delete_directory(self):
        await self.service.createDirectory('testdir')
        assert (self.content_root / 'testdir').exists()
        await self.service.deleteDirectory('testdir')
        assert not (self.content_root / 'testdir').exists()

    async def test_scan_directory_returns_correct_directory_scan_result_list(self):
        await self.service.writeFile('file1.txt', 'content1')
        await self.service.createDirectory('subdir')
        await self.service.writeFile('subdir/file2.txt', 'content2')
        results = await self.service.scanDirectory('')
        assert len(results) == 2
        names = [r.name for r in results]
        types = [r.type for r in results]
        paths = [r.path for r in results]
        assert 'file1.txt' in names
        assert 'subdir' in names
        assert 'file' in types
        assert 'directory' in types
        assert 'file1.txt' in paths
        assert 'subdir' in paths

    async def test_path_exists(self):
        await self.service.writeFile('exists.txt', 'content')
        assert await self.service.pathExists('exists.txt')
        assert not await self.service.pathExists('notexists.txt')

    async def test_rename_item(self):
        await self.service.writeFile('old.txt', 'content')
        await self.service.renameItem('old.txt', 'new.txt')
        assert not await self.service.pathExists('old.txt')
        assert await self.service.pathExists('new.txt')
        assert await self.service.readFile('new.txt') == 'content'

    async def test_security_access_denied_for_path_traversal(self):
        with pytest.raises(SecurityError):
            await self.service.readFile('../../../etc/passwd')
        with pytest.raises(SecurityError):
            await self.service.writeFile('../../../etc/passwd', 'content')
        with pytest.raises(SecurityError):
            await self.service.createDirectory('../../../etc/newdir')
        with pytest.raises(SecurityError):
            await self.service.deleteDirectory('../../../etc')
        with pytest.raises(SecurityError):
            await self.service.renameItem('../../../etc/passwd', 'newname')
        with pytest.raises(SecurityError):
            await self.service.pathExists('../../../etc/passwd')
        with pytest.raises(SecurityError):
            await self.service.scanDirectory('../../../etc')