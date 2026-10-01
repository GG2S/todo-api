"""Boto3를 사용해 DynamoDB의 할 일 데이터를 처리하는 모듈."""

from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class TodoNotFoundError(Exception):
    """요청한 할 일이 DynamoDB에 없을 때 발생한다."""


class TodoStorageError(Exception):
    """DynamoDB 요청 자체가 실패했을 때 발생한다."""


class TodoRepository:
    """DynamoDB의 CRUD 작업을 한곳에서 담당한다."""

    def __init__(self) -> None:
        # 로컬에서는 AWS CLI 자격 증명, EC2에서는 IAM Role을 자동 사용한다.
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table = dynamodb.Table(settings.dynamodb_table_name)

    def list_all(self) -> list[dict[str, Any]]:
        """페이지가 여러 개인 경우를 포함해 모든 할 일을 조회한다."""

        try:
            response = self.table.scan()
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response:
                response = self.table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                items.extend(response.get("Items", []))

            return sorted(items, key=lambda item: item["created_at"], reverse=True)
        except (BotoCoreError, ClientError, KeyError) as exc:
            raise TodoStorageError("할 일 목록을 조회하지 못했습니다.") from exc

    def get(self, todo_id: str) -> dict[str, Any]:
        """ID에 해당하는 할 일 한 건을 조회한다."""

        try:
            response = self.table.get_item(
                Key={"id": todo_id},
                ConsistentRead=True,
            )
        except (BotoCoreError, ClientError) as exc:
            raise TodoStorageError("할 일을 조회하지 못했습니다.") from exc

        item = response.get("Item")
        if item is None:
            raise TodoNotFoundError(todo_id)
        return item

    def create(self, item: dict[str, Any]) -> dict[str, Any]:
        """새 할 일을 저장한다."""

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("id").not_exists(),
            )
            return item
        except (BotoCoreError, ClientError) as exc:
            raise TodoStorageError("할 일을 생성하지 못했습니다.") from exc

    def update(self, todo_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        """전달된 필드만 수정하고 수정된 전체 데이터를 반환한다."""

        expression_names: dict[str, str] = {}
        expression_values: dict[str, Any] = {}
        assignments: list[str] = []

        for index, (field, value) in enumerate(changes.items()):
            name_key = f"#field{index}"
            value_key = f":value{index}"
            expression_names[name_key] = field
            expression_values[value_key] = value
            assignments.append(f"{name_key} = {value_key}")

        try:
            response = self.table.update_item(
                Key={"id": todo_id},
                UpdateExpression="SET " + ", ".join(assignments),
                ConditionExpression=Attr("id").exists(),
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW",
            )
            return response["Attributes"]
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise TodoNotFoundError(todo_id) from exc
            raise TodoStorageError("할 일을 수정하지 못했습니다.") from exc
        except (BotoCoreError, KeyError) as exc:
            raise TodoStorageError("할 일을 수정하지 못했습니다.") from exc

    def delete(self, todo_id: str) -> None:
        """ID에 해당하는 할 일을 삭제한다."""

        try:
            self.table.delete_item(
                Key={"id": todo_id},
                ConditionExpression=Attr("id").exists(),
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise TodoNotFoundError(todo_id) from exc
            raise TodoStorageError("할 일을 삭제하지 못했습니다.") from exc
        except BotoCoreError as exc:
            raise TodoStorageError("할 일을 삭제하지 못했습니다.") from exc


repository = TodoRepository()

