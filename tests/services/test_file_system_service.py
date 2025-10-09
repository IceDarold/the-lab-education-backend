import asyncio
from pathlib import Path

import pytest

from src.core.errors import ContentFileNotFoundError, FileSystemOperationError, SecurityError
from src.services.file_system_service import DirectoryScanResult, FileSystemService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fs_service(tmp_path):
    """Provide a FileSystemService bound to an isolated temporary content root."""
    content_root = tmp_path / "content"
    content_root.mkdir()
    service = FileSystemService()
    service.content_root = content_root.resolve()
    return service, content_root


async def test_successful_read_write_file(fs_service):
    service, _ = fs_service
    await service.write_file("test.txt", "Hello World")
    content = await service.read_file("test.txt")
    assert content == "Hello World"


async def test_read_non_existent_file_raises_content_file_not_found_error(fs_service):
    service, _ = fs_service
    with pytest.raises(ContentFileNotFoundError):
        await service.read_file("nonexistent.txt")


async def test_read_file_raises_file_system_operation_error_on_os_error(fs_service, mocker):
    service, _ = fs_service
    await service.write_file("test.txt", "content")
    mocker.patch("aiofiles.open", side_effect=OSError("Permission denied"))

    with pytest.raises(FileSystemOperationError):
        await service.read_file("test.txt")



async def test_recursive_create_directory(fs_service):
    service, content_root = fs_service
    await service.create_directory("a/b/c")
    target = content_root / "a" / "b" / "c"
    assert target.exists()
    assert target.is_dir()


async def test_delete_directory(fs_service):
    service, content_root = fs_service
    await service.create_directory("testdir")
    assert (content_root / "testdir").exists()
    await service.delete_directory("testdir")
    assert not (content_root / "testdir").exists()


async def test_scan_directory_returns_correct_directory_scan_result_list(fs_service):
    service, _ = fs_service
    await service.write_file("file1.txt", "content1")
    await service.create_directory("subdir")
    await service.write_file("subdir/file2.txt", "content2")

    results = await service.scan_directory("")
    assert len(results) == 2
    assert all(isinstance(result, DirectoryScanResult) for result in results)

    names = {r.name for r in results}
    types = {r.type for r in results}
    paths = {r.path for r in results}

    assert {"file1.txt", "subdir"} <= names
    assert {"file", "directory"} <= types
    assert {"file1.txt", "subdir"} <= paths


async def test_path_exists(fs_service):
    service, _ = fs_service
    await service.write_file("exists.txt", "content")
    assert await service.path_exists("exists.txt")
    assert not await service.path_exists("notexists.txt")


async def test_rename_item(fs_service):
    service, _ = fs_service
    await service.write_file("old.txt", "content")
    await service.rename_item("old.txt", "new.txt")
    assert not await service.path_exists("old.txt")
    assert await service.path_exists("new.txt")
    assert await service.read_file("new.txt") == "content"


async def test_security_access_denied_for_path_traversal(fs_service):
    service, _ = fs_service
    traversal_paths = [
        ("read_file", ("../../../etc/passwd",)),
        ("write_file", ("../../../etc/passwd", "content")),
        ("create_directory", ("../../../etc/newdir",)),
        ("delete_directory", ("../../../etc",)),
        ("rename_item", ("../../../etc/passwd", "newname")),
        ("path_exists", ("../../../etc/passwd",)),
        ("scan_directory", ("../../../etc",)),
    ]

    for method_name, args in traversal_paths:
        method = getattr(service, method_name)
        with pytest.raises(SecurityError):
            result = method(*args)
            if asyncio.iscoroutine(result):
                await result
