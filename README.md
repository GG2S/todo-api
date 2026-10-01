# Todo API

Terraform으로 구축한 EC2와 DynamoDB를 연결해 사용하는 FastAPI 기반 할 일 관리 API입니다.

## API 목록

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | 서버 상태 확인 |
| GET | `/todos` | 전체 할 일 조회 |
| GET | `/todos/{id}` | 개별 할 일 조회 |
| POST | `/todos` | 할 일 생성 |
| PATCH | `/todos/{id}` | 할 일 일부 수정 |
| DELETE | `/todos/{id}` | 할 일 삭제 |

## 사전 조건

- Python 3.9 이상
- 파티션 키가 문자열 `id`인 DynamoDB 테이블
- DynamoDB CRUD 권한을 가진 AWS 자격 증명 또는 EC2 IAM Role

## Windows 로컬 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:AWS_REGION = "ap-northeast-2"
$env:DYNAMODB_TABLE_NAME = "실제_테이블_이름"

uvicorn app.main:app --reload
```

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 상태 확인: `http://127.0.0.1:8000/health`

로컬에서 DynamoDB까지 테스트하려면 AWS CLI 자격 증명이 설정되어 있어야 합니다. EC2에서는 액세스 키 대신 인스턴스에 연결된 IAM Role을 사용합니다.

## 요청 예시

```http
POST /todos
Content-Type: application/json

{
  "title": "Terraform 프로젝트 완료",
  "completed": false
}
```

```http
PATCH /todos/{id}
Content-Type: application/json

{
  "completed": true
}
```

## EC2 서비스 설정

`todo-api.service`의 다음 값을 실제 환경에 맞게 확인합니다.

- `User`, `Group`: EC2 로그인 사용자
- `WorkingDirectory`: API 배치 경로
- `DYNAMODB_TABLE_NAME`: Terraform이 생성한 실제 테이블 이름

서비스 파일을 `/etc/systemd/system/todo-api.service`에 배치한 뒤 다음 명령으로 실행합니다.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now todo-api
sudo systemctl status todo-api
```
