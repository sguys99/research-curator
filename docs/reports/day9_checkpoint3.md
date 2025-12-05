# Day 9-1 Checkpoint 3: Articles CRUD API 구현

## 작업 개요

**목표**: 아티클 관리 및 검색 API 완성

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. Articles CRUD 함수 (`src/app/db/crud/articles.py`)

**구현한 함수** (9개):

#### Read 함수
1. **`get_articles()`**: 아티클 목록 조회 (필터링, 정렬, 페이지네이션)
   - 필터: `source_type`, `category`, `min_importance_score`, `date_from`, `date_to`
   - 정렬: `collected_at` (기본), `importance_score`
   - 페이지네이션: `skip`, `limit`
   - 반환: `(articles, total_count)` 튜플

2. **`get_article_by_id()`**: UUID로 단일 아티클 조회
   - 인자: `article_id` (UUID)
   - 반환: `CollectedArticle | None`

3. **`get_article_by_url()`**: URL로 아티클 조회 (중복 검사용)
   - 인자: `source_url` (str)
   - 반환: `CollectedArticle | None`

4. **`get_articles_by_ids()`**: 배치 조회 (여러 UUID 한 번에)
   - 인자: `article_ids` (list[UUID])
   - 반환: `list[CollectedArticle]`

#### Create/Update/Delete 함수
5. **`create_article()`**: 새 아티클 생성
   - 필수 인자: `title`, `content`, `summary`, `source_url`, `source_type`, `category`, `importance_score`
   - 선택 인자: `metadata`, `vector_id`
   - 반환: `CollectedArticle`

6. **`update_article()`**: 아티클 업데이트
   - 모든 필드 선택적 업데이트 가능
   - 반환: `CollectedArticle | None`

7. **`delete_article()`**: 아티클 삭제
   - 인자: `article_id` (UUID)
   - 반환: `bool` (성공 여부)

#### 통계 및 검색 함수
8. **`get_article_statistics()`**: 아티클 통계
   - 반환 데이터:
     - `total`: 전체 개수
     - `by_source_type`: 소스 타입별 개수 (dict)
     - `by_category`: 카테고리별 개수 (dict)
     - `average_importance_score`: 평균 중요도
   - 날짜 필터 지원

9. **`search_articles()`**: 키워드 기반 검색
   - 검색 대상: `title`, `content`, `summary`
   - ILIKE 패턴 매칭 (대소문자 무시)
   - 반환: `(articles, total_count)` 튜플

**특징**:
- SQLAlchemy ORM 활용
- 타입 힌트 완벽 적용
- Docstring 포함
- 에러 핸들링

---

### 2. Articles API 라우터 (`src/app/api/routers/articles.py`)

**구현한 엔드포인트** (9개):

#### 1. GET `/api/articles` - 아티클 목록 조회
```python
Query Parameters:
- skip: int (default: 0, pagination)
- limit: int (default: 20, max: 100)
- source_type: list[str] | None (paper, news, report)
- category: list[str] | None
- min_importance_score: float | None (0.0-1.0)
- date_from: datetime | None
- date_to: datetime | None
- order_by: str (default: "collected_at")
- order_desc: bool (default: True)

Response: ArticleListResponse
- articles: list[ArticleResponse]
- total: int
- skip: int
- limit: int
```

#### 2. GET `/api/articles/{article_id}` - 단일 아티클 조회
```python
Path Parameters:
- article_id: UUID

Response: ArticleResponse

Errors:
- 404: Article not found
```

#### 3. POST `/api/articles/search` - 시맨틱 검색
```python
Request Body: ArticleSearchRequest
- query: str (자연어 쿼리)
- limit: int (default: 10, max: 100)
- score_threshold: float (default: 0.7)
- source_type: list[str] | None
- category: list[str] | None
- min_importance_score: float | None
- date_from: datetime | None
- date_to: datetime | None

Response: ArticleSearchResponse
- query: str (원본 쿼리)
- results: list[ArticleSearchResult]
  - ...ArticleResponse fields
  - similarity_score: float (유사도)
- total: int

Features:
- Qdrant Vector DB 활용
- 임베딩 기반 유사도 검색
- 필터링 지원
```

#### 4. GET `/api/articles/{article_id}/similar` - 유사 아티클 추천
```python
Path Parameters:
- article_id: UUID

Query Parameters:
- limit: int (default: 5, max: 20)

Response: ArticleSearchResponse

Features:
- Vector DB에서 유사한 아티클 검색
- 자기 자신 제외
- 유사도 점수 포함

Errors:
- 404: Article not found
- 400: Article has no vector embedding
```

#### 5. POST `/api/articles/batch` - 배치 조회
```python
Request Body: BatchArticleRequest
- article_ids: list[UUID] (min: 1, max: 50)

Response: ArticleListResponse
```

#### 6. GET `/api/articles/statistics/summary` - 통계 조회
```python
Query Parameters:
- date_from: datetime | None
- date_to: datetime | None

Response: ArticleStatisticsResponse
- total: int
- by_source_type: dict[str, int]
- by_category: dict[str, int]
- average_importance_score: float
```

#### 7. DELETE `/api/articles/{article_id}` - 아티클 삭제
```python
Path Parameters:
- article_id: UUID

Response:
- message: "Article deleted successfully"

Errors:
- 404: Article not found
```

#### 8. GET `/api/articles/keyword-search` - 키워드 검색
```python
Query Parameters:
- q: str (검색 쿼리)
- skip: int (default: 0)
- limit: int (default: 20, max: 100)

Response: ArticleListResponse

Note:
- 시맨틱 검색(semantic search)과 달리 키워드 기반
- title, content, summary 필드에서 ILIKE 검색
```

**공통 기능**:
- JWT 인증 필수 (`get_current_user` 의존성)
- Pydantic 스키마 검증
- 상세한 에러 핸들링 (HTTPException)
- 비동기 Vector DB 연산

---

### 3. API 스키마 보완 (`src/app/api/schemas/articles.py`)

**추가한 스키마**:

#### BatchArticleRequest
```python
class BatchArticleRequest(BaseModel):
    article_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Article IDs"
    )
```

#### ArticleStatisticsResponse
```python
class ArticleStatisticsResponse(BaseModel):
    total: int
    by_source_type: dict[str, int]
    by_category: dict[str, int]
    average_importance_score: float
```

#### ArticleListResponse 개선
```python
class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    skip: int  # 추가
    limit: int  # 추가
```

**기존 스키마** (이미 구현됨):
- `ArticleBase`, `ArticleCreate`, `ArticleUpdate`
- `ArticleResponse`
- `ArticleSearchRequest`, `ArticleSearchResult`, `ArticleSearchResponse`
- `SimilarArticlesRequest`, `SimilarArticlesResponse`
- `ArticleListRequest`

---

### 4. API 라우터 등록

**`src/app/api/main.py`**:
```python
from app.api.routers import articles, auth, collectors, llm, processors, scheduler, users

app.include_router(articles.router, prefix="/api")
```

**라우터 태그**: `["articles"]`
**베이스 경로**: `/api/articles`

---

## 주요 특징

### 1. Vector DB 통합
- `search_similar_articles()`: 자연어 쿼리 → 임베딩 → Qdrant 검색
- `find_similar_articles()`: 특정 아티클과 유사한 아티클 검색
- 필터링 지원 (source_type, category, importance_score, date)

### 2. 필터링 & 정렬
- 다중 필터 조합 가능
- AND 조건 (SQLAlchemy `and_()`)
- 정렬 필드: `collected_at`, `importance_score`
- 정렬 방향: `ascending`, `descending`

### 3. 페이지네이션
- `skip`, `limit` 파라미터
- 응답에 `total`, `skip`, `limit` 포함
- 최대 limit: 100

### 4. 에러 핸들링
- 404: 리소스 없음
- 400: 잘못된 요청 (vector_id 없음 등)
- 500: 내부 서버 오류 (Vector DB 실패 등)
- 상세한 에러 메시지

### 5. 인증
- 모든 엔드포인트 JWT 인증 필수
- `get_current_user` 의존성
- Bearer 토큰 스키마

---

## 파일 구조

```
src/app/
├── api/
│   ├── routers/
│   │   └── articles.py          ⭐ 신규 (463 lines)
│   └── schemas/
│       └── articles.py          ✨ 보완 (199 lines)
│
└── db/
    └── crud/
        ├── __init__.py          ✨ 업데이트 (articles 함수 export)
        └── articles.py          ⭐ 신규 (355 lines)
```

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
2. **아티클 목록 조회** (`GET /api/articles`)
3. **단일 아티클 조회** (`GET /api/articles/{id}`)
4. **시맨틱 검색** (`POST /api/articles/search`)
5. **유사 아티클** (`GET /api/articles/{id}/similar`)
6. **통계 조회** (`GET /api/articles/statistics/summary`)

---

## 구현 완료 확인

### ✅ CRUD 함수 (9개)
- [x] `get_articles()` - 목록 조회
- [x] `get_article_by_id()` - ID 조회
- [x] `get_article_by_url()` - URL 조회
- [x] `get_articles_by_ids()` - 배치 조회
- [x] `create_article()` - 생성
- [x] `update_article()` - 업데이트
- [x] `delete_article()` - 삭제
- [x] `get_article_statistics()` - 통계
- [x] `search_articles()` - 키워드 검색

### ✅ API 엔드포인트 (9개)
- [x] `GET /api/articles` - 목록
- [x] `GET /api/articles/{id}` - 상세
- [x] `POST /api/articles/search` - 시맨틱 검색
- [x] `GET /api/articles/{id}/similar` - 유사 아티클
- [x] `POST /api/articles/batch` - 배치 조회
- [x] `GET /api/articles/statistics/summary` - 통계
- [x] `DELETE /api/articles/{id}` - 삭제
- [x] `GET /api/articles/keyword-search` - 키워드 검색

### ✅ 스키마
- [x] `BatchArticleRequest`
- [x] `ArticleStatisticsResponse`
- [x] `ArticleListResponse` (skip, limit 추가)

### ✅ 통합
- [x] main.py에 라우터 등록
- [x] crud/__init__.py에 함수 export
- [x] Vector DB operations 함수 사용
- [x] JWT 인증 의존성 적용

---

## 다음 단계 (Checkpoint 4)

**Feedback API 구현**:
1. `src/app/db/crud/feedback.py` - CRUD 함수
2. `src/app/api/routers/feedback.py` - API 라우터
3. 4개 엔드포인트:
   - `POST /api/feedback` - 피드백 생성
   - `GET /api/feedback/{id}` - 단일 피드백 조회
   - `GET /api/users/{user_id}/feedback` - 사용자 피드백 목록
   - `GET /api/articles/{article_id}/feedback` - 아티클 피드백 조회

---

## 참고 사항

### API 응답 예시

**ArticleResponse**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Attention Is All You Need",
  "content": "We propose the Transformer...",
  "summary": "트랜스포머 아키텍처를 제안...",
  "source_url": "https://arxiv.org/abs/1706.03762",
  "source_type": "paper",
  "category": "NLP",
  "importance_score": 0.95,
  "article_metadata": {
    "authors": ["Ashish Vaswani", "..."],
    "citations": 50000
  },
  "collected_at": "2025-12-05T10:00:00Z",
  "vector_id": "vector-123",
  "published_at": "2017-06-12T00:00:00Z"
}
```

**ArticleSearchResponse**:
```json
{
  "query": "transformer optimization",
  "results": [
    {
      ...ArticleResponse fields,
      "similarity_score": 0.92
    }
  ],
  "total": 15
}
```

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 3 완료
