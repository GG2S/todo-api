"""FastAPI 라우트와 공통 오류 처리를 정의하는 실행 모듈."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response, status

from app.config import settings
from app.models import HealthResponse, Todo, TodoCreate, TodoList, TodoUpdate
from app.repository import (
    TodoNotFoundError,
    TodoStorageError,
    repository,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="EC2와 DynamoDB를 사용하는 간단한 할 일 관리 API",
    version="1.0.0",
)


def not_found_error(todo_id: str) -> HTTPException:
    """일관된 404 응답을 생성한다."""

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "TODO_NOT_FOUND",
            "message": f"할 일 '{todo_id}'을(를) 찾을 수 없습니다.",
        },
    )


def storage_error(exc: TodoStorageError) -> HTTPException:
    """DynamoDB 오류를 내부 정보가 노출되지 않는 응답으로 변환한다."""

    logger.exception("DynamoDB operation failed", exc_info=exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "STORAGE_UNAVAILABLE",
            "message": "데이터 저장소를 일시적으로 사용할 수 없습니다.",
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """프로세스가 요청을 받을 수 있는지 확인한다."""

    return HealthResponse(status="ok")


@app.get("/todos", response_model=TodoList, tags=["todos"])
def list_todos() -> TodoList:
    """모든 할 일을 최신 생성 순으로 반환한다."""

    try:
        return TodoList(items=repository.list_all())
    except TodoStorageError as exc:
        raise storage_error(exc) from exc


@app.get("/todos/{todo_id}", response_model=Todo, tags=["todos"])
def get_todo(todo_id: str) -> Todo:
    """특정 할 일을 반환한다."""

    try:
        return Todo.model_validate(repository.get(todo_id))
    except TodoNotFoundError as exc:
        raise not_found_error(todo_id) from exc
    except TodoStorageError as exc:
        raise storage_error(exc) from exc


@app.post(
    "/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
    tags=["todos"],
)
def create_todo(payload: TodoCreate) -> Todo:
    """새 할 일을 생성하고 201 상태 코드로 반환한다."""

    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": str(uuid4()),
        "title": payload.title,
        "completed": payload.completed,
        "created_at": now,
        "updated_at": now,
    }

    try:
        return Todo.model_validate(repository.create(item))
    except TodoStorageError as exc:
        raise storage_error(exc) from exc


@app.patch("/todos/{todo_id}", response_model=Todo, tags=["todos"])
def update_todo(todo_id: str, payload: TodoUpdate) -> Todo:
    """요청에 포함된 할 일 필드만 수정한다."""

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "EMPTY_UPDATE",
                "message": "수정할 필드를 한 개 이상 전달해야 합니다.",
            },
        )

    changes["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        return Todo.model_validate(repository.update(todo_id, changes))
    except TodoNotFoundError as exc:
        raise not_found_error(todo_id) from exc
    except TodoStorageError as exc:
        raise storage_error(exc) from exc


@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["todos"],
)
def delete_todo(todo_id: str) -> Response:
    """특정 할 일을 삭제하고 본문 없는 204 응답을 반환한다."""

    try:
        repository.delete(todo_id)
    except TodoNotFoundError as exc:
        raise not_found_error(todo_id) from exc
    except TodoStorageError as exc:
        raise storage_error(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)

