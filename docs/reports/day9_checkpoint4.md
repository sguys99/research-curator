# Day 9-1 Checkpoint 4: Feedback API 구현

## 작업 개요

**목표**: 사용자 피드백 수집 및 관리 시스템 구현

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. Feedback CRUD 함수 (`src/app/db/crud/feedback.py`)

**구현한 함수** (7개):

#### Read 함수
1. **`get_feedback_by_id()`**: UUID로 단일 피드백 조회
   - 인자: `feedback_id` (UUID)
   - 반환: `Feedback | None`

2. **`get_user_feedback()`**: 사용자의 피드백 목록 조회
   - 인자: `user_id`, `skip`, `limit`
   - 정렬: `created_at` 내림차순
   - 반환: `(feedback_list, total_count)` 튜플

3. **`get_article_feedback()`**: 아티클별 피드백 조회
   - 인자: `article_id`, `skip`, `limit`
   - 정렬: `created_at` 내림차순
   - 반환: `(feedback_list, total_count)` 튜플

4. **`get_article_feedback_stats()`**: 아티클 피드백 통계
   - 반환 데이터:
     - `count`: 전체 피드백 개수
     - `average_rating`: 평균 평점 (소수점 2자리)
     - `rating_distribution`: 평점별 분포 {1: count, 2: count, ..., 5: count}
   - SQLAlchemy `func.count()` 활용

#### Create/Update/Delete 함수
5. **`create_feedback()`**: 새 피드백 생성
   - 필수 인자: `user_id`, `article_id`, `rating` (1-5)
   - 선택 인자: `comment`
   - 반환: `Feedback`

6. **`update_feedback()`**: 피드백 업데이트
   - 인자: `feedback_id`, `rating` (optional), `comment` (optional)
   - 반환: `Feedback | None`

7. **`delete_feedback()`**: 피드백 삭제
   - 인자: `feedback_id`
   - 반환: `bool` (성공 여부)

**특징**:
- 페이지네이션 지원
- 통계 계산 (평균, 분포)
- UTC 타임스탬프
- Docstring 완비

---

### 2. Feedback API 라우터 (`src/app/api/routers/feedback.py`)

**구현한 엔드포인트** (7개):

#### 1. POST `/api/feedback` - 피드백 생성
```python
Request Body: FeedbackCreate
- article_id: UUID
- rating: int (1-5)
- comment: str | None

Response: FeedbackResponse (201 Created)
- id: UUID
- user_id: UUID (from current_user)
- article_id: UUID
- rating: int
- comment: str | None
- created_at: datetime

Features:
- JWT 인증 (current_user)
- Article 존재 여부 확인
- 자동으로 user_id 설정

Errors:
- 404: Article not found
```

#### 2. GET `/api/feedback/{feedback_id}` - 단일 피드백 조회
```python
Path Parameters:
- feedback_id: UUID

Response: FeedbackResponse

Authorization:
- 사용자는 자신의 피드백만 조회 가능

Errors:
- 404: Feedback not found
- 403: Not authorized (다른 사용자의 피드백)
```

#### 3. PUT `/api/feedback/{feedback_id}` - 피드백 업데이트
```python
Path Parameters:
- feedback_id: UUID

Request Body: FeedbackUpdate
- rating: int | None (1-5)
- comment: str | None

Response: FeedbackResponse

Authorization:
- 사용자는 자신의 피드백만 수정 가능

Errors:
- 404: Feedback not found
- 403: Not authorized
- 500: Update failed
```

#### 4. DELETE `/api/feedback/{feedback_id}` - 피드백 삭제
```python
Path Parameters:
- feedback_id: UUID

Response:
- message: "Feedback deleted successfully"

Authorization:
- 사용자는 자신의 피드백만 삭제 가능

Errors:
- 404: Feedback not found
- 403: Not authorized
- 500: Delete failed
```

#### 5. GET `/api/feedback/user/{user_id}` - 사용자 피드백 목록
```python
Path Parameters:
- user_id: UUID

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 20, max: 100)

Response: FeedbackListResponse
- feedback: list[FeedbackResponse]
- total: int
- skip: int
- limit: int

Authorization:
- 사용자는 자신의 피드백만 조회 가능

Errors:
- 403: Not authorized (다른 사용자 조회 시도)
```

#### 6. GET `/api/feedback/article/{article_id}` - 아티클 피드백 목록
```python
Path Parameters:
- article_id: UUID

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 20, max: 100)

Response: FeedbackListResponse

Features:
- 모든 사용자 조회 가능 (공개)
- Article 존재 여부 확인

Errors:
- 404: Article not found
```

#### 7. GET `/api/feedback/article/{article_id}/stats` - 아티클 피드백 통계
```python
Path Parameters:
- article_id: UUID

Response: FeedbackStatsResponse
- article_id: UUID
- count: int (총 피드백 개수)
- average_rating: float (평균 평점, 소수점 2자리)
- rating_distribution: dict[int, int]
  - {1: 5, 2: 10, 3: 20, 4: 30, 5: 35}

Features:
- 평점별 분포 제공
- 평균 평점 계산
- Article 존재 여부 확인

Errors:
- 404: Article not found
```

**공통 기능**:
- JWT 인증 필수 (`get_current_user`)
- Pydantic 스키마 검증
- 권한 검증 (본인 피드백만 수정/삭제)
- 상세한 에러 메시지

---

### 3. API 스키마 (`src/app/api/schemas/feedback.py`)

이미 Checkpoint 1에서 정의되어 있습니다:

```python
class FeedbackCreate(BaseModel):
    """피드백 생성 요청"""
    article_id: UUID
    rating: int = Field(..., ge=1, le=5)  # 1-5 범위
    comment: str | None = Field(None, max_length=1000)

class FeedbackUpdate(BaseModel):
    """피드백 업데이트 요청"""
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, max_length=1000)

class FeedbackResponse(BaseModel):
    """피드백 응답"""
    id: UUID
    user_id: UUID
    article_id: UUID
    rating: int
    comment: str | None
    created_at: datetime

class FeedbackListResponse(BaseModel):
    """피드백 목록 응답"""
    feedback: list[FeedbackResponse]
    total: int
    skip: int
    limit: int

class FeedbackStatsResponse(BaseModel):
    """피드백 통계 응답"""
    article_id: UUID
    count: int
    average_rating: float
    rating_distribution: dict[int, int]
```

---

### 4. 라우터 등록

**`src/app/api/main.py`**:
```python
from app.api.routers import articles, auth, collectors, feedback, llm, processors, scheduler, users

app.include_router(feedback.router, prefix="/api")
```

**라우터 태그**: `["feedback"]`
**베이스 경로**: `/api/feedback`

---

## 주요 특징

### 1. 권한 관리
- **Create**: 로그인한 사용자가 자신의 피드백 생성
- **Read (단일)**: 사용자는 자신의 피드백만 조회
- **Update**: 사용자는 자신의 피드백만 수정
- **Delete**: 사용자는 자신의 피드백만 삭제
- **Read (목록)**:
  - 사용자 피드백 목록: 본인만 조회 가능
  - 아티클 피드백 목록: 모든 사용자 조회 가능 (공개)
  - 아티클 통계: 모든 사용자 조회 가능 (공개)

### 2. 데이터 검증
- Rating: 1-5 범위 (Pydantic Field 검증)
- Comment: 최대 1000자
- Article 존재 여부 확인
- User 인증 검증

### 3. 통계 기능
- 평균 평점 계산 (소수점 2자리)
- 평점별 분포 (1점~5점)
- SQLAlchemy group_by 활용

### 4. 페이지네이션
- `skip`, `limit` 파라미터
- 최대 limit: 100
- 응답에 total, skip, limit 포함

---

## 파일 구조

```
src/app/
├── api/
│   ├── routers/
│   │   └── feedback.py          ⭐ 신규 (397 lines)
│   └── schemas/
│       └── feedback.py          ✅ 이미 정의됨 (Checkpoint 1)
│
└── db/
    └── crud/
        ├── __init__.py          ✨ 업데이트 (feedback 함수 export)
        └── feedback.py          ⭐ 신규 (222 lines)
```

---

## API 사용 예시

### 1. 피드백 생성
```bash
POST /api/feedback
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 5,
  "comment": "매우 유용한 논문이었습니다!"
}

# Response (201 Created)
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 5,
  "comment": "매우 유용한 논문이었습니다!",
  "created_at": "2025-12-05T10:00:00Z"
}
```

### 2. 아티클 통계 조회
```bash
GET /api/feedback/article/{article_id}/stats
Authorization: Bearer {access_token}

# Response (200 OK)
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "count": 100,
  "average_rating": 4.35,
  "rating_distribution": {
    "1": 2,
    "2": 5,
    "3": 15,
    "4": 38,
    "5": 40
  }
}
```

### 3. 사용자 피드백 목록
```bash
GET /api/feedback/user/{user_id}?skip=0&limit=10
Authorization: Bearer {access_token}

# Response (200 OK)
{
  "feedback": [
    {
      "id": "...",
      "user_id": "...",
      "article_id": "...",
      "rating": 5,
      "comment": "...",
      "created_at": "..."
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 10
}
```

---

## 구현 완료 확인

### ✅ CRUD 함수 (7개)
- [x] `get_feedback_by_id()` - ID 조회
- [x] `get_user_feedback()` - 사용자 피드백 목록
- [x] `get_article_feedback()` - 아티클 피드백 목록
- [x] `get_article_feedback_stats()` - 통계
- [x] `create_feedback()` - 생성
- [x] `update_feedback()` - 업데이트
- [x] `delete_feedback()` - 삭제

### ✅ API 엔드포인트 (7개)
- [x] `POST /api/feedback` - 피드백 생성
- [x] `GET /api/feedback/{id}` - 단일 조회
- [x] `PUT /api/feedback/{id}` - 업데이트
- [x] `DELETE /api/feedback/{id}` - 삭제
- [x] `GET /api/feedback/user/{user_id}` - 사용자 피드백 목록
- [x] `GET /api/feedback/article/{article_id}` - 아티클 피드백 목록
- [x] `GET /api/feedback/article/{article_id}/stats` - 통계

### ✅ 기능
- [x] JWT 인증
- [x] 권한 검증 (본인 피드백만 수정/삭제)
- [x] Article 존재 여부 확인
- [x] 페이지네이션
- [x] 통계 계산 (평균, 분포)
- [x] 에러 핸들링

### ✅ 통합
- [x] main.py에 라우터 등록
- [x] crud/__init__.py에 함수 export
- [x] 스키마 정의 (Checkpoint 1에서 완료)

---

## 테스트 방법

### 1. 서버 시작
```bash
source .venv/bin/activate
uvicorn src.app.api.main:app --reload
```

### 2. Swagger UI 접속
```
http://localhost:8000/docs
```

### 3. API 테스트 순서
1. **인증 토큰 발급** (`POST /auth/magic-link` → `GET /auth/verify`)
2. **피드백 생성** (`POST /api/feedback`)
3. **피드백 조회** (`GET /api/feedback/{id}`)
4. **피드백 업데이트** (`PUT /api/feedback/{id}`)
5. **사용자 피드백 목록** (`GET /api/feedback/user/{user_id}`)
6. **아티클 피드백 목록** (`GET /api/feedback/article/{article_id}`)
7. **아티클 통계** (`GET /api/feedback/article/{article_id}/stats`)
8. **피드백 삭제** (`DELETE /api/feedback/{id}`)

---

## 다음 단계 (Checkpoint 5)

**API 통합 테스트**:
1. 전체 API 엔드포인트 테스트 작성
2. End-to-End 시나리오 테스트
3. 에러 케이스 테스트
4. Swagger UI 검증

---

## 참고 사항

### 권한 검증 로직
```python
# 본인 피드백만 조회/수정/삭제 가능
if str(feedback.user_id) != str(current_user.id):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized"
    )
```

### 통계 계산
```python
# SQLAlchemy group_by 활용
rating_counts = (
    db.query(Feedback.rating, func.count(Feedback.id))
    .filter(Feedback.article_id == article_id)
    .group_by(Feedback.rating)
    .all()
)
```

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 4 완료

**다음**: Checkpoint 5 - API 통합 테스트
