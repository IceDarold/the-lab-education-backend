from uuid import UUID

from pydantic import BaseModel


class AnswerPublic(BaseModel):
    answer_id: UUID
    answer_text: str


class QuestionPublic(BaseModel):
    question_id: UUID
    question_text: str
    answers: list[AnswerPublic]


class QuizCheckRequest(BaseModel):
    question_id: UUID
    selected_answer_id: UUID


class QuizCheckResponse(BaseModel):
    is_correct: bool
    correct_answer_id: UUID

