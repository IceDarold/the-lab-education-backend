from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.ulf_parser import ULFParseError, parse_lesson_file


def make_lesson(tmp_path: Path, text: str) -> Path:
    file_path = tmp_path / "example.lesson"
    file_path.write_text(text.strip())
    return file_path


def test_parse_lesson_file_success(tmp_path):
    file_path = make_lesson(
        tmp_path,
        """
---
title: Parsing Demo
slug: parsing-demo
course_slug: parsing-course
lesson_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
level: beginner
---
type: markdown
order: 1
---
# Intro

---
type: quiz
question_id: q1
---
What is ULF?
""",
    )

    lesson = parse_lesson_file(file_path)

    assert lesson.slug == "parsing-demo"
    assert lesson.title == "Parsing Demo"
    assert lesson.course_slug == "parsing-course"
    assert str(lesson.lesson_id) == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert lesson.metadata == {"level": "beginner"}
    assert len(lesson.cells) == 2
    assert lesson.cells[0].cell_type == "markdown"
    assert "Intro" in lesson.cells[0].content
    assert lesson.cells[1].metadata == {"question_id": "q1"}


def test_parse_lesson_invalid_front_matter(tmp_path):
    file_path = make_lesson(tmp_path, "---\nnot yaml")

    with pytest.raises(ULFParseError):
        parse_lesson_file(file_path)


def test_parse_lesson_missing_cell_type(tmp_path):
    file_path = make_lesson(
        tmp_path,
        """
---
title: Bad Lesson
slug: bad-lesson
---
foo: bar
---
content
""",
    )

    with pytest.raises(ULFParseError):
        parse_lesson_file(file_path)
