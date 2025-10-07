from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import get_current_user
from src.db.session import get_supabase_client
from src.schemas.quiz import QuizCheckRequest, QuizCheckResponse
from src.schemas.user import User

router = APIRouter()


async def _finalize(result):
    execute = getattr(result, "execute", None)
    if callable(execute):
        result = execute()
    if hasattr(result, "__await__"):
        result = await result
    return result


@router.post("/answers/check", response_model=QuizCheckResponse)
async def check_quiz_answer(
    payload: QuizCheckRequest,
    current_user: User = Depends(get_current_user),
) -> QuizCheckResponse:
    del current_user  # RLS handles permissions
    supabase = get_supabase_client()

    answers_table = supabase.table("answers")
    query = answers_table.eq("question_id", str(payload.question_id)).single()

    try:
        response = await _finalize(query)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found") from exc

    data = getattr(response, "data", response) or {}
    correct_answer_id = data.get("correct_answer_id")
    if not correct_answer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    correct_uuid = UUID(str(correct_answer_id))
    is_correct = payload.selected_answer_id == correct_uuid

    return QuizCheckResponse(is_correct=is_correct, correct_answer_id=correct_uuid)
