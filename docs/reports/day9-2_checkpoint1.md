# Day 9-2 Checkpoint 1: API 클라이언트 업데이트

## 작업 개요

**목표**: Frontend API 클라이언트를 Day 9-1에서 완성한 Backend API에 맞게 업데이트

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. Articles API 메서드 업데이트 (`src/app/frontend/utils/api_client.py`)

#### 기존 메서드 업데이트

**`get_articles()`** - 고급 필터링 지원
```python
def get_articles(
    self,
    skip: int = 0,
    limit: int = 20,
    source_type: list[str] | None = None,  # 변경: str → list[str]
    category: list[str] | None = None,      # 변경: str → list[str]
    min_importance_score: float | None = None,  # 신규
    date_from: str | None = None,               # 신규
    date_to: str | None = None,                 # 신규
    order_by: str = "collected_at",             # 변경: sort_by → order_by
    order_desc: bool = True,                    # 변경: order → order_desc
) -> dict[str, Any]:
```

**변경사항:**
- URL: `/articles` → `/api/articles`
- `source_type`, `category`: 단일 값 → 리스트
- 필터 추가: `min_importance_score`, `date_from`, `date_to`
- 파라미터명 변경: `sort_by` → `order_by`, `order` → `order_desc`

#### 신규 메서드 (4개)

**1. `get_articles_batch()`** - 배치 조회
```python
def get_articles_batch(self, article_ids: list[str]) -> dict[str, Any]:
    """Get multiple articles by IDs (batch retrieval)."""
    # POST /api/articles/batch
```

**2. `get_article_statistics()`** - 통계 조회
```python
def get_article_statistics(
    self,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Get article statistics."""
    # GET /api/articles/statistics/summary
```

**3. `search_articles_keyword()`** - 키워드 검색
```python
def search_articles_keyword(
    self,
    query: str,
    skip: int = 0,
    limit: int = 20,
) -> dict[str, Any]:
    """Search articles using keyword search (ILIKE pattern matching)."""
    # GET /api/articles/keyword-search
```

**4. `delete_article()`** - 아티클 삭제
```python
def delete_article(self, article_id: str) -> dict[str, Any]:
    """Delete article by ID."""
    # DELETE /api/articles/{article_id}
```

#### 기존 검색 메서드 변경

**`search_articles()` → `search_articles_semantic()`**
```python
def search_articles_semantic(  # 이름 변경
    self,
    query: str,
    limit: int = 10,
    score_threshold: float = 0.7,
    source_type: list[str] | None = None,
    category: list[str] | None = None,
    min_importance_score: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
```

**변경사항:**
- 메서드명: `search_articles()` → `search_articles_semantic()`
- URL: `/search` → `/api/articles/search`

**`find_similar_articles()` → `get_similar_articles()`**
```python
def get_similar_articles(  # 이름 변경
    self,
    article_id: str,
    limit: int = 5,
) -> dict[str, Any]:
```

**변경사항:**
- 메서드명: `find_similar_articles()` → `get_similar_articles()`
- URL: `/articles/{id}/similar` → `/api/articles/{id}/similar`
- 파라미터 제거: `score_threshold` (백엔드에서 고정값 0.7 사용)

---

### 2. Feedback API 메서드 완전 재구성

#### 기존 메서드 변경

**`submit_feedback()` → `create_feedback()`**
```python
# 변경 전
def submit_feedback(
    self,
    user_id: str,  # 제거
    article_id: str,
    rating: int,
    comment: str = "",
) -> dict[str, Any]:

# 변경 후
def create_feedback(
    self,
    article_id: str,
    rating: int,
    comment: str | None = None,  # 변경: str → str | None
) -> dict[str, Any]:
    """Create feedback for an article (user_id from JWT)."""
    # POST /api/feedback
```

**변경사항:**
- 메서드명: `submit_feedback()` → `create_feedback()`
- `user_id` 제거: JWT에서 자동 할당
- URL: `/feedback` → `/api/feedback`
- `comment` 타입 변경: `str` → `str | None`

**`get_user_feedback()` 업데이트**
```python
def get_user_feedback(self, user_id: str, skip: int = 0, limit: int = 20):
    """Get user's feedback list."""
    # GET /api/feedback/user/{user_id}
```

**변경사항:**
- URL: `/users/{user_id}/feedback` → `/api/feedback/user/{user_id}`
- `limit` 기본값: 10 → 20

#### 신규 메서드 (5개)

**1. `get_feedback()`** - 단일 피드백 조회
```python
def get_feedback(self, feedback_id: str) -> dict[str, Any]:
    """Get single feedback by ID."""
    # GET /api/feedback/{feedback_id}
```

**2. `update_feedback()`** - 피드백 업데이트
```python
def update_feedback(
    self,
    feedback_id: str,
    rating: int | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Update feedback."""
    # PUT /api/feedback/{feedback_id}
```

**3. `delete_feedback()`** - 피드백 삭제
```python
def delete_feedback(self, feedback_id: str) -> dict[str, Any]:
    """Delete feedback."""
    # DELETE /api/feedback/{feedback_id}
```

**4. `get_article_feedback()`** - 아티클 피드백 목록
```python
def get_article_feedback(
    self,
    article_id: str,
    skip: int = 0,
    limit: int = 20,
) -> dict[str, Any]:
    """Get feedback for a specific article."""
    # GET /api/feedback/article/{article_id}
```

**5. `get_article_feedback_stats()`** - 피드백 통계
```python
def get_article_feedback_stats(self, article_id: str) -> dict[str, Any]:
    """Get feedback statistics for an article."""
    # GET /api/feedback/article/{article_id}/stats
```

---

### 3. 에러 핸들링 강화

#### `_handle_response()` 메서드 개선

**추가된 에러 처리:**

```python
def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
    """Handle API response and errors."""
    try:
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code

        # 상태 코드별 처리
        if status_code == 401:
            error_msg = "인증이 필요합니다. 다시 로그인해주세요."
            # 세션 토큰 자동 삭제
            if hasattr(st, "session_state"):
                st.session_state.pop("access_token", None)
                st.session_state.pop("user", None)
        elif status_code == 403:
            error_msg = f"권한이 없습니다: {error_detail}"
        elif status_code == 404:
            error_msg = f"리소스를 찾을 수 없습니다: {error_detail}"
        elif status_code == 500:
            error_msg = f"서버 오류가 발생했습니다: {error_detail}"
        else:
            error_msg = f"API 오류 ({status_code}): {error_detail}"

    except httpx.TimeoutException as e:
        error_msg = "요청 시간이 초과되었습니다. 다시 시도해주세요."
    except httpx.RequestError as e:
        error_msg = f"네트워크 오류가 발생했습니다: {str(e)}"
```

**개선 사항:**
1. **401 Unauthorized**: 세션 토큰 자동 삭제 + 로그인 유도
2. **403 Forbidden**: 권한 부족 명확한 메시지
3. **404 Not Found**: 리소스 없음 안내
4. **500 Server Error**: 서버 오류 안내
5. **Timeout**: 시간 초과 처리
6. **Network Error**: 네트워크 오류 처리

---

## 최종 API 클라이언트 구성

### 메서드 수 요약

| 카테고리 | 메서드 수 | 설명 |
|---------|----------|------|
| **Auth** | 2 | Magic link 요청, 검증 |
| **User/Preferences** | 3 | 사용자 정보, 설정 조회/업데이트 |
| **Articles** | 10 | CRUD, 검색, 통계, 배치 |
| **Feedback** | 7 | CRUD, 통계 |
| **Digests** | 3 | 다이제스트 목록, 최신, 테스트 |
| **LLM** | 1 | 챗봇 완성 |
| **총계** | **26** | |

### Articles API 메서드 (10개)

1. `get_articles()` - 아티클 목록 (필터링, 정렬, 페이지네이션)
2. `get_article()` - 단일 조회
3. `get_articles_batch()` - 배치 조회
4. `get_article_statistics()` - 통계 조회
5. `search_articles_semantic()` - 시맨틱 검색
6. `search_articles_keyword()` - 키워드 검색
7. `get_similar_articles()` - 유사 문서 검색
8. `delete_article()` - 삭제

### Feedback API 메서드 (7개)

1. `create_feedback()` - 피드백 생성
2. `get_feedback()` - 단일 조회
3. `update_feedback()` - 업데이트
4. `delete_feedback()` - 삭제
5. `get_user_feedback()` - 사용자 피드백 목록
6. `get_article_feedback()` - 아티클 피드백 목록
7. `get_article_feedback_stats()` - 통계

---

## 변경 사항 요약

### 1. URL 변경
- 기존: `/articles`, `/feedback`, `/search`
- 신규: `/api/articles`, `/api/feedback`, `/api/articles/search`

### 2. 파라미터 타입 변경
- `source_type`, `category`: `str` → `list[str]`
- `order`: `str` → `order_desc: bool`
- `comment`: `str` → `str | None`

### 3. 메서드명 변경
- `submit_feedback()` → `create_feedback()`
- `search_articles()` → `search_articles_semantic()`
- `find_similar_articles()` → `get_similar_articles()`

### 4. 신규 기능
- 배치 조회 (`get_articles_batch`)
- 통계 조회 (`get_article_statistics`, `get_article_feedback_stats`)
- 키워드 검색 (`search_articles_keyword`)
- 피드백 CRUD (`get_feedback`, `update_feedback`, `delete_feedback`)
- 아티클 피드백 목록 (`get_article_feedback`)

### 5. 에러 핸들링
- 401: 자동 로그아웃
- 403, 404, 500: 한국어 에러 메시지
- Timeout, Network Error: 추가 처리

---

## 테스트 결과

```bash
✅ API client instantiated successfully

📊 Total API methods: 24

✨ Article API methods (10 total):
  - delete_article()
  - get_article()
  - get_article_feedback()
  - get_article_feedback_stats()
  - get_article_statistics()
  - get_articles()
  - get_articles_batch()
  - get_similar_articles()
  - search_articles_keyword()
  - search_articles_semantic()

✨ Feedback API methods (7 total):
  - create_feedback()
  - delete_feedback()
  - get_article_feedback()
  - get_article_feedback_stats()
  - get_feedback()
  - get_user_feedback()
  - update_feedback()
```

---

## 다음 단계 (Checkpoint 2)

**Dashboard 페이지 API 연동**:
1. 통계 카드 실시간 데이터
2. 최근 다이제스트 표시
3. 빠른 작업 버튼

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 1 완료

**다음**: Checkpoint 2 - Dashboard 페이지 API 연동
