import pytest
from pathlib import Path
from src.services.file_system_service import FileSystemService, DirectoryScanResult
from src.core.errors import ContentFileNotFoundError, FileSystemOperationError, SecurityError


pytestmark = pytest.mark.asyncio


class TestFileSystemService:
    @pytest.fixture(autouse=True)
    def setup_service(self, tmp_path):
        self.tmp_path = tmp_path
        self.content_root = Path(tmp_path) / 'content'
        self.service = FileSystemService()
        self.service.content_root = self.content_root

    async def test_successful_read_write_file(self):
        await self.service.write_file('test.txt', 'Hello World')
        content = await self.service.read_file('test.txt')
        assert content == 'Hello World'

    async def test_read_non_existent_file_raises_content_file_not_found_error(self):
        with pytest.raises(ContentFileNotFoundError):
            await self.service.read_file('nonexistent.txt')

    async def test_read_file_raises_file_system_operation_error_on_os_error(self, mocker, caplog):
        await self.service.write_file('test.txt', 'content')
        mocker.patch('aiofiles.open', side_effect=OSError("Permission denied"))
        with pytest.raises(FileSystemOperationError):
            await self.service.read_file('test.txt')
        assert any("Failed to read_file: test.txt" in record.message for record in caplog.records if record.levelname == 'ERROR')

    async def test_recursive_create_directory(self):
        await self.service.create_directory('a/b/c')
        assert (self.content_root / 'a' / 'b' / 'c').exists()
        assert (self.content_root / 'a' / 'b' / 'c').is_dir()

    async def test_delete_directory(self):
        await self.service.create_directory('testdir')
        assert (self.content_root / 'testdir').exists()
        await self.service.delete_directory('testdir')
        assert not (self.content_root / 'testdir').exists()

    async def test_scan_directory_returns_correct_directory_scan_result_list(self):
        await self.service.write_file('file1.txt', 'content1')
        await self.service.create_directory('subdir')
        await self.service.write_file('subdir/file2.txt', 'content2')
        results = await self.service.scan_directory('')
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
        await self.service.write_file('exists.txt', 'content')
        assert await self.service.path_exists('exists.txt')
        assert not await self.service.path_exists('notexists.txt')

    async def test_rename_item(self):
        await self.service.write_file('old.txt', 'content')
        await self.service.rename_item('old.txt', 'new.txt')
        assert not await self.service.path_exists('old.txt')
        assert await self.service.path_exists('new.txt')
        assert await self.service.read_file('new.txt') == 'content'

    async def test_security_access_denied_for_path_traversal(self):
        with pytest.raises(SecurityError):
            await self.service.read_file('../../../etc/passwd')
        with pytest.raises(SecurityError):
            await self.service.write_file('../../../etc/passwd', 'content')
        with pytest.raises(SecurityError):
            await self.service.create_directory('../../../etc/newdir')
        with pytest.raises(SecurityError):
            await self.service.delete_directory('../../../etc')
        with pytest.raises(SecurityError):
            await self.service.rename_item('../../../etc/passwd', 'newname')
        with pytest.raises(SecurityError):
            await self.service.path_exists('../../../etc/passwd')
        with pytest.raises(SecurityError):
            await self.service.scan_directory('../../../etc')