import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.ulf_parser_service import ULFParserService
from src.core.errors import ParsingError


def test_parse_valid_ulf_text():
    """Test parsing valid ULF text with frontmatter and cells."""
    ulf_text = """---
title: Test Lesson
slug: test-lesson
course_slug: test-course
lesson_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
level: beginner
---
type: markdown
order: 1
---
# Introduction

This is a test lesson.
---
type: quiz
question_id: q1
---
What is ULF?
"""

    result = ULFParserService.parse(ulf_text)

    assert result['frontmatter']['title'] == 'Test Lesson'
    assert result['frontmatter']['slug'] == 'test-lesson'
    assert result['frontmatter']['course_slug'] == 'test-course'
    assert result['frontmatter']['lesson_id'] == 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    assert result['frontmatter']['level'] == 'beginner'

    assert len(result['cells']) == 2

    assert result['cells'][0]['config']['type'] == 'markdown'
    assert result['cells'][0]['config']['order'] == 1
    assert '# Introduction' in result['cells'][0]['content']
    assert 'This is a test lesson.' in result['cells'][0]['content']

    assert result['cells'][1]['config']['type'] == 'quiz'
    assert result['cells'][1]['config']['question_id'] == 'q1'
    assert result['cells'][1]['content'] == 'What is ULF?'


def test_stringify_reverse():
    """Test that stringify(parse(text)) produces equivalent structure."""
    ulf_text = """---
title: Test Lesson
slug: test-lesson
---
type: markdown
order: 1
---
# Introduction

Content here.
---
type: quiz
question_id: q1
---
Question?
"""

    parsed = ULFParserService.parse(ulf_text)
    stringified = ULFParserService.stringify(parsed)
    reparsed = ULFParserService.parse(stringified)

    assert reparsed['frontmatter'] == parsed['frontmatter']
    assert len(reparsed['cells']) == len(parsed['cells'])
    for i, cell in enumerate(parsed['cells']):
        assert reparsed['cells'][i]['config'] == cell['config']
        assert reparsed['cells'][i]['content'] == cell['content']


def test_parse_invalid_yaml_raises_parsing_error():
    """Test that invalid YAML in frontmatter raises ParsingError."""
    invalid_ulf_text = """---
title: Test Lesson
invalid yaml here: [unclosed
slug: test-lesson
---
type: markdown
---
Content
"""

    with pytest.raises(ParsingError):
        ULFParserService.parse(invalid_ulf_text)


def test_parse_invalid_cell_config_yaml_raises_parsing_error():
    """Test that invalid YAML in cell config raises ParsingError."""
    invalid_ulf_text = """---
title: Test Lesson
slug: test-lesson
---
type: markdown
invalid: [unclosed
---
Content
"""

    with pytest.raises(ParsingError):
        ULFParserService.parse(invalid_ulf_text)