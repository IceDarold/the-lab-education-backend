from uuid import UUID

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import get_current_user
from src.db.session import get_supabase_client
from src.schemas.quiz import QuizCheckRequest, QuizCheckResponse
from src.schemas.user import User
from src.core.utils import maybe_await

router = APIRouter()


def get_answers_table(supabase_client=Depends(get_supabase_client)) -> Any:
    """Dependency wrapper for accessing the answers table."""
    return supabase_client.table("answers")


async def _execute_query(query: Any) -> Any:
    """Execute a Supabase query handling sync/async mocks seamlessly."""
    execute = getattr(query, "execute", None)
    if not callable(execute):
        raise RuntimeError("Supabase query missing execute method")
    result = execute()
    return await maybe_await(result)


@router.post("/answers/check", response_model=QuizCheckResponse)
async def check_quiz_answer(
    payload: QuizCheckRequest,
    current_user: User = Depends(get_current_user),
    answers_table: Any = Depends(get_answers_table),
) -> QuizCheckResponse:
    del current_user  # RLS handles permissions
    query = answers_table.eq("question_id", str(payload.question_id)).single()

    try:
        response = await _execute_query(query)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found") from exc

    data = getattr(response, "data", response) or {}
    correct_answer_id = data.get("correct_answer_id")
    if not correct_answer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    correct_uuid = UUID(str(correct_answer_id))
    is_correct = payload.selected_answer_id == correct_uuid

    return QuizCheckResponse(is_correct=is_correct, correct_answer_id=correct_uuid)
