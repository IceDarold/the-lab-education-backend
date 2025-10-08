from typing import Union
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import PlainTextResponse

from src.core.security import get_current_admin
from src.dependencies import get_fs_service, get_content_scanner
from src.schemas.api import CreateCourseRequest, CreateModuleRequest, CreateLessonRequest
from src.schemas.user import User
from src.schemas.content_node import ContentNode
from src.services.content_scanner_service import ContentScannerService
from src.services.file_system_service import FileSystemService

router = APIRouter()


@router.get("/content-tree", response_model=list[ContentNode])
async def get_content_tree(current_user: User = Depends(get_current_admin), cs_service: ContentScannerService = Depends(get_content_scanner)):
    return await cs_service.build_content_tree()


@router.get("/config-file", response_class=PlainTextResponse)
async def get_config_file(
    path: str = Query(..., description="Path to the config file"),
    current_user: User = Depends(get_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service)
):
    try:
        content = await fs_service.read_file(path)
        return PlainTextResponse(content)
    except ContentFileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.put("/config-file", status_code=status.HTTP_200_OK)
async def update_config_file(
    path: str = Query(..., description="Path to the config file"),
    content: str = Body(..., media_type="text/plain"),
    current_user: User = Depends(get_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):
    await fs_service.write_file(path, content)
    cs_service.clear_cache()
    return {"status": "updated"}


@router.post("/create/{item_type}", status_code=status.HTTP_201_CREATED)
async def create_item(
    item_type: str,
    request: Union[CreateCourseRequest, CreateModuleRequest, CreateLessonRequest],
    current_user: User = Depends(get_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):

    if item_type == "course":
        if not isinstance(request, CreateCourseRequest):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request for course")
        path = f"courses/{request.slug}"
        await fs_service.create_directory(path)
        config_path = f"{path}/_course.yml"
        config_content = f"title: {request.title}\n"
        await fs_service.write_file(config_path, config_content)

    elif item_type == "module":
        if not isinstance(request, CreateModuleRequest):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request for module")
        path = f"courses/{request.parentSlug}/{request.slug}"
        await fs_service.create_directory(path)
        config_path = f"{path}/_module.yml"
        config_content = f"title: {request.title}\n"
        await fs_service.write_file(config_path, config_content)

    elif item_type == "lesson":
        if not isinstance(request, CreateLessonRequest):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request for lesson")
        # Find parent path
        tree = await cs_service.build_content_tree()
        parent_path = None
        course_slug = None
        for node in tree:
            if node.type == 'course':
                for child in node.children or []:
                    if child.type == 'module' and child.name == request.parentSlug:
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
            "duration": "10m"
        }
        cells = [
            {
                "config": {"type": "markdown"},
                "content": f"# {request.title}\n\nLesson content goes here."
            }
        ]
        import yaml
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False).strip()
        body_parts = []
        for cell in cells:
            config_yaml = yaml.dump(cell['config'], default_flow_style=False).strip()
            body_parts.append(config_yaml)
            body_parts.append(cell['content'])
        body = '\n---\n'.join(body_parts)
        lesson_content = f"---\n{frontmatter_yaml}\n---\n{body}"
        await fs_service.write_file(lesson_path, lesson_content)

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item type")

    cs_service.clear_cache()
    return {"status": "created"}


@router.delete("/item", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    path: str = Query(..., description="Path to the item to delete"),
    current_user: User = Depends(get_current_admin),
    fs_service: FileSystemService = Depends(get_fs_service),
    cs_service: ContentScannerService = Depends(get_content_scanner)
):
    try:
        if await fs_service.path_exists(path):
            # Check if directory or file
            # Since scan_directory would work for dir, but to check type
            import os
            from pathlib import Path
            abs_path = Path('./content') / path
            if abs_path.is_dir():
                await fs_service.delete_directory(path)
            else:
                await fs_service.delete_file(path)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    cs_service.clear_cache()