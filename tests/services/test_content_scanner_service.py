import pytest
from unittest.mock import AsyncMock
from src.services.content_scanner_service import ContentScannerService
from src.services.file_system_service import DirectoryScanResult
from src.schemas.content_node import ContentNode


pytestmark = pytest.mark.asyncio


class TestContentScannerService:
    async def test_build_content_tree_with_mock_directory_structure(self, mocker):
        # Mock FileSystemService
        mock_fs_service = mocker.AsyncMock()

        # Mock scanDirectory for 'courses' directory
        mock_fs_service.scan_directory.side_effect = self._mock_scan_directory

        # Mock readFile for config files
        mock_fs_service.read_file.side_effect = self._mock_read_file

        # Create service instance
        service = ContentScannerService(mock_fs_service)

        # Call build_content_tree
        result = await service.build_content_tree()

        # Expected structure
        expected = [
            ContentNode(
                type='course',
                name='Course 1',
                path='courses/course1',
                config_path='courses/course1/_course.yml',
                children=[
                    ContentNode(
                        type='module',
                        name='Module 1',
                        path='courses/course1/module1',
                        config_path='courses/course1/module1/_module.yml',
                        children=[
                            ContentNode(
                                type='lesson',
                                name='lesson1',
                                path='courses/course1/module1/lesson1.lesson'
                            ),
                            ContentNode(
                                type='lesson',
                                name='lesson2',
                                path='courses/course1/module1/lesson2.lesson'
                            )
                        ]
                    ),
                    ContentNode(
                        type='module',
                        name='Module 2',
                        path='courses/course1/module2',
                        config_path='courses/course1/module2/_module.yml',
                        children=[
                            ContentNode(
                                type='lesson',
                                name='lesson3',
                                path='courses/course1/module2/lesson3.lesson'
                            )
                        ]
                    )
                ]
            ),
            ContentNode(
                type='course',
                name='Course 2',
                path='courses/course2',
                config_path='courses/course2/_course.yml',
                children=[
                    ContentNode(
                        type='lesson',
                        name='lesson4',
                        path='courses/course2/lesson4.lesson'
                    )
                ]
            )
        ]

        # Assert the result matches expected
        assert len(result) == 2
        assert result[0].type == 'course'
        assert result[0].name == 'Course 1'
        assert result[0].path == 'courses/course1'
        assert result[0].config_path == 'courses/course1/_course.yml'
        assert len(result[0].children) == 2

        # Module 1
        module1 = result[0].children[0]
        assert module1.type == 'module'
        assert module1.name == 'Module 1'
        assert len(module1.children) == 2
        assert module1.children[0].name == 'lesson1'
        assert module1.children[1].name == 'lesson2'

        # Module 2
        module2 = result[0].children[1]
        assert module2.type == 'module'
        assert module2.name == 'Module 2'
        assert len(module2.children) == 1
        assert module2.children[0].name == 'lesson3'

        # Course 2
        course2 = result[1]
        assert course2.type == 'course'
        assert course2.name == 'Course 2'
        assert len(course2.children) == 1
        assert course2.children[0].name == 'lesson4'

    def _mock_scan_directory(self, path):
        if path == 'courses':
            return [
                DirectoryScanResult(name='course1', type='directory', path='courses/course1'),
                DirectoryScanResult(name='course2', type='directory', path='courses/course2'),
                DirectoryScanResult(name='other_dir', type='directory', path='courses/other_dir'),  # No config, should be ignored
            ]
        elif path == 'courses/course1':
            return [
                DirectoryScanResult(name='_course.yml', type='file', path='courses/course1/_course.yml'),
                DirectoryScanResult(name='module1', type='directory', path='courses/course1/module1'),
                DirectoryScanResult(name='module2', type='directory', path='courses/course1/module2'),
            ]
        elif path == 'courses/course1/module1':
            return [
                DirectoryScanResult(name='_module.yml', type='file', path='courses/course1/module1/_module.yml'),
                DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/course1/module1/lesson1.lesson'),
                DirectoryScanResult(name='lesson2.lesson', type='file', path='courses/course1/module1/lesson2.lesson'),
            ]
        elif path == 'courses/course1/module2':
            return [
                DirectoryScanResult(name='_module.yml', type='file', path='courses/course1/module2/_module.yml'),
                DirectoryScanResult(name='lesson3.lesson', type='file', path='courses/course1/module2/lesson3.lesson'),
            ]
        elif path == 'courses/course2':
            return [
                DirectoryScanResult(name='_course.yml', type='file', path='courses/course2/_course.yml'),
                DirectoryScanResult(name='lesson4.lesson', type='file', path='courses/course2/lesson4.lesson'),
            ]
        elif path == 'courses/other_dir':
            return [
                DirectoryScanResult(name='some_file.txt', type='file', path='courses/other_dir/some_file.txt'),
            ]
        return []

    def _mock_read_file(self, path):
        if path == 'courses/course1/_course.yml':
            return 'title: Course 1\n'
        elif path == 'courses/course1/module1/_module.yml':
            return 'title: Module 1\n'
        elif path == 'courses/course1/module2/_module.yml':
            return 'title: Module 2\n'
        elif path == 'courses/course2/_course.yml':
            return 'title: Course 2\n'
        return ''

    async def test_build_node_course_with_valid_config(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
            DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/test_course/lesson1.lesson'),
        ]
        mock_fs.read_file.return_value = 'title: Test Course\n'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'Test Course'
        assert result.path == 'courses/test_course'
        assert result.config_path == 'courses/test_course/_course.yml'
        assert len(result.children) == 1
        assert result.children[0].type == 'lesson'
        assert result.children[0].name == 'lesson1'

    async def test_build_node_course_with_invalid_yaml(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
        ]
        mock_fs.read_file.return_value = 'invalid: yaml: content:'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'test_course'  # Falls back to path basename
        assert result.path == 'courses/test_course'
        assert result.config_path == 'courses/test_course/_course.yml'
        assert len(result.children) == 0

    async def test_build_node_course_with_missing_title(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
        ]
        mock_fs.read_file.return_value = 'other_field: value\n'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'test_course'  # Falls back to path basename
        assert result.path == 'courses/test_course'
        assert result.config_path == 'courses/test_course/_course.yml'
        assert len(result.children) == 0

    async def test_build_node_module_with_valid_config(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_module.yml', type='file', path='courses/course/module/_module.yml'),
            DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/course/module/lesson1.lesson'),
        ]
        mock_fs.read_file.return_value = 'title: Test Module\n'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/course/module')

        assert result is not None
        assert result.type == 'module'
        assert result.name == 'Test Module'
        assert result.path == 'courses/course/module'
        assert result.config_path == 'courses/course/module/_module.yml'
        assert len(result.children) == 1
        assert result.children[0].type == 'lesson'
        assert result.children[0].name == 'lesson1'

    async def test_build_node_module_with_invalid_yaml(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_module.yml', type='file', path='courses/course/module/_module.yml'),
        ]
        mock_fs.read_file.return_value = 'invalid yaml content'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/course/module')

        assert result is not None
        assert result.type == 'module'
        assert result.name == 'module'  # Falls back to path basename
        assert result.path == 'courses/course/module'
        assert result.config_path == 'courses/course/module/_module.yml'
        assert len(result.children) == 0

    async def test_build_node_module_with_missing_title(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_module.yml', type='file', path='courses/course/module/_module.yml'),
        ]
        mock_fs.read_file.return_value = 'description: Some description\n'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/course/module')

        assert result is not None
        assert result.type == 'module'
        assert result.name == 'module'  # Falls back to path basename
        assert result.path == 'courses/course/module'
        assert result.config_path == 'courses/course/module/_module.yml'
        assert len(result.children) == 0

    async def test_build_node_directory_without_config(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/no_config/lesson1.lesson'),
            DirectoryScanResult(name='other_file.txt', type='file', path='courses/no_config/other_file.txt'),
        ]

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/no_config')

        assert result is None

    async def test_build_node_with_child_directories_recursive(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.side_effect = lambda path: {
            'courses/test_course': [
                DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
                DirectoryScanResult(name='module1', type='directory', path='courses/test_course/module1'),
            ],
            'courses/test_course/module1': [
                DirectoryScanResult(name='_module.yml', type='file', path='courses/test_course/module1/_module.yml'),
            ]
        }.get(path, [])
        mock_fs.read_file.side_effect = lambda path: {
            'courses/test_course/_course.yml': 'title: Test Course\n',
            'courses/test_course/module1/_module.yml': 'title: Module 1\n'
        }.get(path, '')

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'Test Course'
        assert len(result.children) == 1
        child = result.children[0]
        assert child.type == 'module'
        assert child.name == 'Module 1'
        assert len(child.children) == 0

    async def test_build_node_with_lesson_files(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
            DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/test_course/lesson1.lesson'),
            DirectoryScanResult(name='lesson2.lesson', type='file', path='courses/test_course/lesson2.lesson'),
        ]
        mock_fs.read_file.return_value = 'title: Test Course\n'

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert len(result.children) == 2
        assert all(child.type == 'lesson' for child in result.children)
        assert {child.name for child in result.children} == {'lesson1', 'lesson2'}

    async def test_build_node_mixed_content(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.side_effect = lambda path: {
            'courses/test_course': [
                DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
                DirectoryScanResult(name='module1', type='directory', path='courses/test_course/module1'),
                DirectoryScanResult(name='lesson1.lesson', type='file', path='courses/test_course/lesson1.lesson'),
            ],
            'courses/test_course/module1': [
                DirectoryScanResult(name='_module.yml', type='file', path='courses/test_course/module1/_module.yml'),
                DirectoryScanResult(name='lesson2.lesson', type='file', path='courses/test_course/module1/lesson2.lesson'),
            ]
        }.get(path, [])
        mock_fs.read_file.side_effect = lambda path: {
            'courses/test_course/_course.yml': 'title: Test Course\n',
            'courses/test_course/module1/_module.yml': 'title: Module 1\n'
        }.get(path, '')

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'Test Course'
        assert len(result.children) == 2  # One module, one lesson
        module_child = next(child for child in result.children if child.type == 'module')
        lesson_child = next(child for child in result.children if child.type == 'lesson')
        assert module_child.name == 'Module 1'
        assert len(module_child.children) == 1
        assert module_child.children[0].name == 'lesson2'
        assert lesson_child.name == 'lesson1'

    async def test_build_node_file_read_error(self, mocker):
        mock_fs = mocker.AsyncMock()
        mock_fs.scan_directory.return_value = [
            DirectoryScanResult(name='_course.yml', type='file', path='courses/test_course/_course.yml'),
        ]
        mock_fs.read_file.side_effect = Exception("File read error")

        service = ContentScannerService(mock_fs)
        result = await service._build_node('courses/test_course')

        assert result is not None
        assert result.type == 'course'
        assert result.name == 'test_course'  # Falls back to path basename
        assert result.path == 'courses/test_course'
        assert result.config_path == 'courses/test_course/_course.yml'
        assert len(result.children) == 0