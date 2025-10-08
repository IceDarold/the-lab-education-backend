from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ContentNode(BaseModel):
    type: str  # 'course' | 'module' | 'lesson'
    name: str
    path: str
    children: List[ContentNode] = []
    configPath: Optional[str] = None