from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from uuid import UUID
import os

import yaml

from src.schemas.lesson import LessonCell, LessonContent


# Cache for parsed lesson files: path -> (mtime, LessonContent)
_lesson_cache: Dict[str, Tuple[float, LessonContent]] = {}


class ULFParseError(Exception):
    """Raised when a lesson file in ULF format cannot be parsed."""


def parse_lesson_file_from_text(raw_text: str) -> LessonContent:
    """Parse a lesson from raw text in the Unified Lesson Format (.lesson).

    Args:
        raw_text: Raw text content of the lesson file.

    Raises:
        ULFParseError: If the text has invalid structure.

    Returns:
        A `LessonContent` pydantic model describing the lesson.
    """
    front_matter, body = _split_front_matter(raw_text)
    metadata = _parse_yaml(front_matter, error_message="Invalid front matter in lesson file")

    if not isinstance(metadata, dict):
        raise ULFParseError("Lesson front matter must be a mapping")

    slug = metadata.get("slug") or metadata.get("lesson_slug")
    if not slug:
        raise ULFParseError("Lesson front matter must include 'slug'")

    title = metadata.get("title")
    if not title:
        raise ULFParseError("Lesson front matter must include 'title'")

    lesson_id = metadata.get("lesson_id") or metadata.get("id")
    lesson_uuid = _coerce_optional_uuid(lesson_id)

    course_slug = metadata.get("course_slug")

    cells = _parse_cells(body)

    known_keys = {"slug", "lesson_slug", "title", "lesson_id", "id", "course_slug"}
    extra_metadata = {k: v for k, v in metadata.items() if k not in known_keys}

    return LessonContent(
        slug=str(slug),
        title=str(title),
        course_slug=str(course_slug) if course_slug else None,
        lesson_id=lesson_uuid,
        metadata=extra_metadata,
        cells=cells,
    )


def parse_lesson_file(path: Path) -> LessonContent:
    """Parse a lesson stored in the Unified Lesson Format (.lesson).

    Args:
        path: Path to the lesson file.

    Raises:
        FileNotFoundError: If the path does not exist.
        ULFParseError: If the file exists but has invalid structure.

    Returns:
        A `LessonContent` pydantic model describing the lesson.
    """

    if not path.exists():
        raise FileNotFoundError(path)

    path_str = str(path)
    mtime = path.stat().st_mtime
    if path_str in _lesson_cache:
        cached_mtime, cached_content = _lesson_cache[path_str]
        if cached_mtime == mtime:
            return cached_content

    raw_text = path.read_text(encoding="utf-8")
    front_matter, body = _split_front_matter(raw_text)
    metadata = _parse_yaml(front_matter, error_message="Invalid front matter in lesson file")

    if not isinstance(metadata, dict):
        raise ULFParseError("Lesson front matter must be a mapping")

    slug = metadata.get("slug") or metadata.get("lesson_slug")
    if not slug:
        raise ULFParseError("Lesson front matter must include 'slug'")

    title = metadata.get("title")
    if not title:
        raise ULFParseError("Lesson front matter must include 'title'")

    lesson_id = metadata.get("lesson_id") or metadata.get("id")
    lesson_uuid = _coerce_optional_uuid(lesson_id)

    course_slug = metadata.get("course_slug")

    cells = _parse_cells(body)

    known_keys = {"slug", "lesson_slug", "title", "lesson_id", "id", "course_slug"}
    extra_metadata = {k: v for k, v in metadata.items() if k not in known_keys}

    result = LessonContent(
        slug=str(slug),
        title=str(title),
        course_slug=str(course_slug) if course_slug else None,
        lesson_id=lesson_uuid,
        metadata=extra_metadata,
        cells=cells,
    )
    _lesson_cache[path_str] = (mtime, result)
    return result


def _split_front_matter(raw_text: str) -> Tuple[str, str]:
    if not raw_text.startswith("---"):
        raise ULFParseError("Lesson file must start with YAML front matter delimited by '---'")

    parts = raw_text.split("\n---\n", 1)
    if len(parts) != 2:
        raise ULFParseError("Lesson file must contain front matter and a body separated by '---'")

    # parts[0] still has leading '---' without trailing newline
    front_matter = parts[0][3:]  # remove initial '---'
    body = parts[1]
    return front_matter.strip(), body


def _parse_yaml(raw: str, *, error_message: str) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - defensive branch
        raise ULFParseError(error_message) from exc

    if not isinstance(data, dict):
        raise ULFParseError(error_message)
    return data


def _parse_cells(body: str) -> List[LessonCell]:
    body = body.strip()
    if not body:
        return []

    parts = body.split("\n---\n")
    if len(parts) % 2 != 0:
        raise ULFParseError("Each lesson cell must contain metadata and content separated by '---'")

    cells: List[LessonCell] = []
    for meta_raw, content_raw in zip(parts[0::2], parts[1::2]):
        meta = _parse_yaml(meta_raw, error_message="Cell metadata must be valid YAML mapping")
        if "type" not in meta:
            raise ULFParseError("Cell metadata must include a 'type' field")

        cell_type = str(meta.pop("type"))
        cell_content = content_raw.rstrip()

        cells.append(
            LessonCell(
                cell_type=cell_type,
                content=cell_content,
                metadata=meta,
            )
        )

    return cells


def _coerce_optional_uuid(value: Any) -> Optional[UUID]:
    if value in (None, ""):
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        raise ULFParseError("lesson_id must be a valid UUID") from exc

