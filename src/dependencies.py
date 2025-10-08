from src.services.file_system_service import FileSystemService
from src.services.content_scanner_service import ContentScannerService
from src.services.ulf_parser_service import ULFParserService


def get_fs_service() -> FileSystemService:
    return FileSystemService()


def get_content_scanner(fs: FileSystemService = get_fs_service()) -> ContentScannerService:
    return ContentScannerService(fs)


def get_ulf_parser() -> ULFParserService:
    return ULFParserService()