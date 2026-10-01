"""환경변수에서 애플리케이션 설정을 읽는 모듈."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """API 실행에 필요한 설정값을 보관한다."""

    app_name: str = os.getenv("APP_NAME", "Todo API")
    aws_region: str = os.getenv("AWS_REGION", "ap-northeast-2")
    dynamodb_table_name: str = os.getenv("DYNAMODB_TABLE_NAME", "todos")


settings = Settings()

