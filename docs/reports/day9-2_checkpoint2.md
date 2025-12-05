# Day 9-2 Checkpoint 2: Dashboard 페이지 API 연동

## 작업 개요

**목표**: Dashboard 페이지를 실제 Backend API와 연동

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. 통계 카드 실시간 데이터 연동

#### 변경 전
```python
# Calculate stats
total_articles = sum(len(d.get("article_ids", [])) for d in digests)
total_digests = len(digests)
avg_rating = (
    sum(f.get("rating", 0) for f in feedbacks) / len(feedbacks) if feedbacks else 0.0
)
```

**문제점:**
- 다이제스트에서 역산한 아티클 수 (부정확)
- 다이제스트 개수를 로컬에서 계산

#### 변경 후
```python
# Get article statistics from API
stats_response = api.get_article_statistics()
total_articles = stats_response.get("total", 0)

# Get recent digests with total count
digests_response = api.get_user_digests(user_id, skip=0, limit=3)
digests = digests_response.get("digests", [])
total_digests = digests_response.get("total", 0)

# Get user feedback stats
feedback_response = api.get_user_feedback(user_id, skip=0, limit=100)
feedbacks = feedback_response.get("feedback", [])  # 변경: feedbacks → feedback
avg_rating = (
    sum(f.get("rating", 0) for f in feedbacks) / len(feedbacks) if feedbacks else 0.0
)
```

**개선 사항:**
1. **총 아티클 수**: `GET /api/articles/statistics/summary` API 사용
   - 전체 시스템의 정확한 아티클 수
2. **받은 이메일 수**: 응답의 `total` 필드 사용
   - 페이지네이션된 전체 개수
3. **평균 피드백**: 응답 필드명 수정 (`feedbacks` → `feedback`)
   - Backend API 스키마에 맞춤

---

### 2. 최근 다이제스트 표시 개선

#### 변경 전 (비효율적)
```python
# Load articles one by one
articles = []
for article_id in article_ids:
    try:
        article = api.get_article(article_id)
        articles.append(article)
    except Exception:
        continue
```

**문제점:**
- N개의 아티클 → N번의 API 호출
- 네트워크 오버헤드 큰 증가
- 속도 느림

#### 변경 후 (배치 API 사용)
```python
# Load articles using batch API
try:
    batch_response = api.get_articles_batch(article_ids)
    articles = batch_response.get("articles", [])

    # Display articles
    if articles:
        show_article_list(articles, show_similar_button=True)
    else:
        st.warning("아티클을 불러올 수 없습니다.")
except Exception as e:
    st.error(f"아티클 로딩 오류: {str(e)}")
```

**개선 사항:**
1. **배치 API 사용**: `POST /api/articles/batch`
   - N개의 아티클 → 1번의 API 호출
   - 최대 50개까지 한 번에 조회 가능
2. **에러 핸들링 강화**: 상세한 에러 메시지 표시
3. **성능 향상**: 네트워크 요청 수 대폭 감소

---

### 3. 빠른 작업 버튼 (기존 유지)

이미 잘 구현되어 있어 변경 없음:

**1. 테스트 이메일 발송 버튼**
```python
if st.button("📧 테스트 이메일 발송", use_container_width=True):
    with st.spinner("테스트 이메일을 발송하는 중..."):
        try:
            result = api.send_test_digest(user_id)
            st.success("✅ 테스트 이메일이 발송되었습니다!")
            st.json(result)
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
```

**2. 검색하기 버튼**
```python
if st.button("🔍 검색하기", use_container_width=True):
    # Navigate to search page
    st.session_state["nav_target"] = "search"
    st.rerun()
```

**3. 설정 변경 버튼**
```python
if st.button("⚙️ 설정 변경", use_container_width=True):
    # Navigate to settings page
    st.session_state["nav_target"] = "settings"
    st.rerun()
```

---

## 사용된 API 엔드포인트

### 1. 통계 조회
```http
GET /api/articles/statistics/summary
```
**응답:**
```json
{
  "total": 1000,
  "by_source_type": {"paper": 600, "news": 300, "report": 100},
  "by_category": {"AI": 500, "ML": 300, "NLP": 200},
  "average_importance_score": 0.75
}
```

### 2. 다이제스트 목록
```http
GET /users/{user_id}/digests?skip=0&limit=3
```
**응답:**
```json
{
  "digests": [
    {
      "id": "...",
      "user_id": "...",
      "article_ids": ["...", "..."],
      "sent_at": "2025-12-05T08:00:00Z",
      "email_opened": false
    }
  ],
  "total": 15
}
```

### 3. 사용자 피드백
```http
GET /api/feedback/user/{user_id}?skip=0&limit=100
```
**응답:**
```json
{
  "feedback": [
    {
      "id": "...",
      "user_id": "...",
      "article_id": "...",
      "rating": 5,
      "comment": "Very useful!",
      "created_at": "2025-12-05T10:00:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 100
}
```

### 4. 배치 아티클 조회
```http
POST /api/articles/batch
Content-Type: application/json

{
  "article_ids": ["id1", "id2", "id3", ...]
}
```
**응답:**
```json
{
  "articles": [
    {
      "id": "...",
      "title": "...",
      "summary": "...",
      ...
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 10
}
```

### 5. 테스트 이메일 발송
```http
POST /users/{user_id}/digests/test
```

---

## 성능 개선

### Before (개별 조회)
```
아티클 10개 조회:
- API 호출: 10번
- 네트워크 왕복: 10 RTT
- 예상 시간: ~1-2초
```

### After (배치 조회)
```
아티클 10개 조회:
- API 호출: 1번
- 네트워크 왕복: 1 RTT
- 예상 시간: ~0.1-0.2초

성능 향상: 약 10배
```

---

## Dashboard 페이지 구조

### 1. 헤더
```
📊 대시보드
최근 받은 연구 자료를 확인하세요
```

### 2. 통계 카드 (3개)
```
┌─────────────┬─────────────┬─────────────┐
│ 📚 총 아티클 │ 📧 받은 이메일 │ ⭐ 평균 피드백 │
│    1,000    │     15      │    4.2     │
└─────────────┴─────────────┴─────────────┘
```

### 3. 최근 받은 이메일 (최대 3개)
```
📬 최근 받은 이메일

📧 다이제스트 1 - 2025-12-05
  포함된 아티클: 10개
  ┌───────────────────────────┐
  │ Article Card 1            │
  │ - Title                   │
  │ - Summary                 │
  │ - Source, Category        │
  │ - Importance Score        │
  │ [원문 보기] [유사 논문]      │
  └───────────────────────────┘
  ...
```

### 4. 빠른 작업
```
⚡ 빠른 작업

┌────────────┬────────────┬────────────┐
│ 📧 테스트   │ 🔍 검색하기 │ ⚙️ 설정 변경 │
│ 이메일 발송 │            │            │
└────────────┴────────────┴────────────┘
```

---

## 에러 핸들링

### 1. 데이터 로딩 실패
```python
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")
    digests = []
    total_articles = 0
    total_digests = 0
    avg_rating = 0.0
```

### 2. 배치 아티클 로딩 실패
```python
except Exception as e:
    st.error(f"아티클 로딩 오류: {str(e)}")
```

### 3. 테스트 이메일 발송 실패
```python
except Exception as e:
    st.error(f"❌ 오류: {str(e)}")
```

---

## 변경 파일

```
src/app/frontend/pages/dashboard.py
```

**주요 변경사항:**
1. `api.get_article_statistics()` 사용
2. `feedbacks` → `feedback` 필드명 수정
3. `api.get_articles_batch()` 사용
4. 에러 핸들링 개선

---

## 테스트 시나리오

### 시나리오 1: 통계 카드 로딩
1. Dashboard 페이지 접속
2. 로딩 스피너 표시
3. 3개 통계 카드 표시:
   - 총 아티클 수 (전체 시스템)
   - 받은 이메일 수 (전체)
   - 평균 피드백 점수

### 시나리오 2: 다이제스트 표시
1. 최근 3개 다이제스트 로딩
2. 각 다이제스트 expandable
3. 첫 번째 다이제스트 자동 확장
4. 배치 API로 아티클 로딩
5. 아티클 카드 렌더링

### 시나리오 3: 빠른 작업
1. **테스트 이메일**: 클릭 → 발송 → 성공 메시지
2. **검색하기**: 클릭 → Search 페이지 이동
3. **설정 변경**: 클릭 → Settings 페이지 이동

---

## 다음 단계 (Checkpoint 3)

**Search 페이지 API 연동**:
1. 시맨틱 검색 구현
2. 키워드 검색 구현
3. 유사 문서 검색
4. 고급 필터 연동

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 2 완료

**다음**: Checkpoint 3 - Search 페이지 API 연동
