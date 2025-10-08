from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerPublic(BaseModel):
    answer_id: UUID
    answer_text: str = Field(..., min_length=1, max_length=500)


class QuestionPublic(BaseModel):
    question_id: UUID
    question_text: str = Field(..., min_length=1, max_length=500)
    answers: list[AnswerPublic]


class QuizCheckRequest(BaseModel):
    question_id: UUID
    selected_answer_id: UUID


class QuizCheckResponse(BaseModel):
    is_correct: bool
    correct_answer_id: UUID

