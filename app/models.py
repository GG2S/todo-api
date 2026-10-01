"""API 요청과 응답에 사용하는 데이터 모델 모듈."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    """할 일 생성 요청 본문의 형식을 검증한다."""

    title: str = Field(min_length=1, max_length=100)
    completed: bool = False


class TodoUpdate(BaseModel):
    """할 일 수정 요청에서 전달된 필드만 검증한다."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    completed: Optional[bool] = None


class Todo(BaseModel):
    """클라이언트에 반환하는 할 일 데이터 형식."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class TodoList(BaseModel):
    """할 일 목록 응답 형식."""

    items: list[Todo]


class HealthResponse(BaseModel):
    """서버 상태 확인 응답 형식."""

    status: str
