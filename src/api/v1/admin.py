import uuid
from pathlib import PurePosixPath
from typing import List, Literal, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response

from src.core.errors import ContentFileNotFoundError, SecurityError
from src.dependencies import get_content_scanner, get_fs_service, validate_safe_path, require_current_admin
from src.schemas.api import CreateCourseRequest, CreateLessonRequest, CreateModuleRequest
from src.schemas.content_node import ContentNode
from src.schemas.user import User
from src.services.content_scanner_service import ContentScannerService
from src.services.file_system_service import FileSystemService

router = APIRouter()


@router.get("/content-tree", response_model=List[ContentNode])
async def get_content_tree(current_user: User = Depends(require_current_admin), cs_service: ContentScannerService = Depends(get_content_scanner)):
    try:
        return await cs_service.build_content_tree()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build content tree") from exc


@router.get("/config-file", response_class=PlainTextResponse)
async def get_config_file(
    path: str = Query(..., description="Path to the config file"),
    current_user: User = Depends(require_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service)
):
    # Validate path for security
    validate_safe_path(path)

    try:
        content = await fs_service.read_file(path)
        return PlainTextResponse(content)
    except ContentFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc
    except SecurityError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.put("/config-file", status_code=status.HTTP_200_OK)
async def update_config_file(
    path: str = Query(..., description="Path to the config file"),
    content: str = Body(..., media_type="text/plain"),
    current_user: User = Depends(require_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):
    # Validate path for security
    validate_safe_path(path)

    try:
        await fs_service.write_file(path, content)
    except SecurityError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    cs_service.clear_cache()
    return {"status": "updated"}


@router.post("/create/{item_type}", status_code=status.HTTP_201_CREATED)
async def create_item(
    item_type: Literal["course", "module", "lesson"],
    request_body: dict = Body(...),
    current_user: User = Depends(require_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):

    if item_type == "course":
        try:
            request = CreateCourseRequest(**request_body)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        path = f"courses/{request.slug}"
        await fs_service.create_directory(path)
        config_path = f"{path}/_course.yml"
        config_content = f"title: {request.title}\n"
        await fs_service.write_file(config_path, config_content)

    elif item_type == "module":
        try:
            request = CreateModuleRequest(**request_body)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        path = f"courses/{request.parent_slug}/{request.slug}"
        await fs_service.create_directory(path)
        config_path = f"{path}/_module.yml"
        config_content = f"title: {request.title}\n"
        await fs_service.write_file(config_path, config_content)

    elif item_type == "lesson":
        try:
            request = CreateLessonRequest(**request_body)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        tree = await cs_service.build_content_tree()
        parent_path = None
        course_slug = None
        for node in tree:
            if node.type == "course":
                for child in node.children or []:
                    if child.type == "module" and child.name == request.parent_slug:
                        parent_path = child.path
                        course_slug = node.name
                        break
                if parent_path:
                    break
        if not parent_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent module not found")

        lesson_path = f"{parent_path}/{request.slug}.lesson"
        frontmatter = {
            "title": request.title,
            "slug": request.slug,
            "course_slug": course_slug,
            "lesson_id": str(uuid.uuid4()),
            "duration": "10m",
        }
        cells = [
            {
                "config": {"type": "markdown"},
                "content": f"# {request.title}\n\nLesson content goes here.",
            }
        ]
        import yaml

        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False).strip()
        body_parts = []
        for cell in cells:
            config_yaml = yaml.dump(cell["config"], default_flow_style=False).strip()
            body_parts.append(config_yaml)
            body_parts.append(cell["content"])
        body = "\n---\n".join(body_parts)
        lesson_content = f"---\n{frontmatter_yaml}\n---\n{body}"
        await fs_service.write_file(lesson_path, lesson_content)

    cs_service.clear_cache()
    return {"status": "created"}


@router.delete("/item", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    path: str = Query(..., description="Path to the item to delete"),
    current_user: User = Depends(require_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):
    # Validate path for security
    validate_safe_path(path)

    try:
        exists = await fs_service.path_exists(path)
    except SecurityError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    path_obj = PurePosixPath(path.replace("\\", "/"))
    is_file = bool(path_obj.suffix) or path_obj.name.endswith(".lesson")

    try:
        if is_file:
            await fs_service.delete_file(path)
        else:
            await fs_service.delete_directory(path)
    except ContentFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    cs_service.clear_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
