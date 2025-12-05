# Day 9-2 Checkpoint 3: Search 페이지 API 연동

## 작업 개요

**목표**: Search 페이지를 실제 Backend API와 연동

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. 시맨틱 검색과 키워드 검색 탭 분리

#### 변경 전
```python
# Single search input
query = st.text_input(
    "검색어를 입력하세요",
    placeholder="예: transformer 모델 최적화 기법",
    key="search_query",
)

# Single search API call
response = api.search_articles(**search_params)
```

**문제점:**
- 시맨틱 검색과 키워드 검색이 구분되지 않음
- 사용자가 검색 방식을 선택할 수 없음
- 잘못된 API 메서드명 사용 (`search_articles`)

#### 변경 후
```python
# Search mode tabs
search_tab1, search_tab2 = st.tabs(["🧠 시맨틱 검색", "🔤 키워드 검색"])

# Tab 1: Semantic Search
with search_tab1:
    query = st.text_input(
        "검색어를 입력하세요 (자연어)",
        placeholder="예: transformer 모델 최적화 기법",
        key="semantic_search_query",
    )
    search_mode = "semantic"

# Tab 2: Keyword Search
with search_tab2:
    query = st.text_input(
        "키워드를 입력하세요",
        placeholder="예: GPT-4, BERT, attention mechanism",
        key="keyword_search_query",
        help="제목, 요약, 내용에서 키워드를 검색합니다",
    )
    search_mode = "keyword"
```

**개선 사항:**
1. **탭으로 검색 방식 구분**: 시맨틱 vs 키워드 검색 명확히 구분
2. **각 탭에 맞는 placeholder**: 사용 방법을 직관적으로 안내
3. **독립적인 검색창**: 각 모드별로 별도의 session state 사용

---

### 2. 검색 모드별 API 호출 분기

#### 변경 전 (잘못된 메서드명)
```python
# Call search API
response = api.search_articles(**search_params)
articles = response.get("results", [])
```

#### 변경 후 (모드별 분기)
```python
if search_mode == "semantic":
    # Prepare semantic search parameters
    search_params = {
        "query": query,
        "limit": limit,
        "score_threshold": score_threshold,
    }

    if source_types:
        search_params["source_type"] = source_types

    if categories:
        search_params["category"] = categories

    if min_importance > 0:
        search_params["min_importance_score"] = min_importance

    if date_from:
        search_params["date_from"] = date_from.isoformat()

    if date_to:
        search_params["date_to"] = date_to.isoformat()

    # Call semantic search API
    response = api.search_articles_semantic(**search_params)
    articles = response.get("results", [])

else:  # keyword search
    # Call keyword search API (simpler, no advanced filters)
    response = api.search_articles_keyword(
        query=query,
        skip=0,
        limit=limit,
    )
    articles = response.get("articles", [])
```

**개선 사항:**
1. **시맨틱 검색**:
   - API: `POST /api/articles/search`
   - 메서드: `api.search_articles_semantic()`
   - 고급 필터 모두 적용 가능
   - 응답 필드: `results`

2. **키워드 검색**:
   - API: `GET /api/articles/keyword-search`
   - 메서드: `api.search_articles_keyword()`
   - 간단한 키워드 매칭 (ILIKE)
   - 응답 필드: `articles`

---

### 3. 유사 문서 검색 API 업데이트

#### 변경 전 (잘못된 메서드명 + 불필요한 파라미터)
```python
# Search parameters with unnecessary threshold slider
col1, col2 = st.columns(2)

with col1:
    limit = st.number_input("최대 결과 수", min_value=1, max_value=20, value=5)

with col2:
    score_threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.7, 0.05)

response = api.find_similar_articles(
    article_id=article_id,
    limit=limit,
    score_threshold=score_threshold,  # Backend에서 지원하지 않음
)
```

**문제점:**
- 잘못된 메서드명 (`find_similar_articles`)
- Backend API가 `score_threshold`를 지원하지 않음 (고정값 0.7)
- 불필요한 UI 컨트롤 (사용자에게 혼란)

#### 변경 후 (단순화)
```python
# Search parameters (only limit)
limit = st.number_input("최대 결과 수", min_value=1, max_value=20, value=5)

if st.button("🔍 유사 문서 검색", type="primary"):
    with st.spinner("유사 문서를 찾는 중..."):
        try:
            response = api.get_similar_articles(
                article_id=article_id,
                limit=limit,
            )

            articles = response.get("results", [])
            # ... display results
```

**개선 사항:**
1. **메서드명 수정**: `find_similar_articles` → `get_similar_articles`
2. **파라미터 제거**: `score_threshold` 제거 (Backend 고정값 0.7)
3. **UI 단순화**: 불필요한 슬라이더 제거

---

### 4. 세션 상태 관리 개선

#### 검색창 초기화
```python
# Before
if st.button("🔄 초기화", use_container_width=True):
    st.session_state.search_query = ""  # 단일 키
    st.rerun()

# After
if st.button("🔄 초기화", use_container_width=True):
    st.session_state.semantic_search_query = ""  # 두 개 모두
    st.session_state.keyword_search_query = ""
    st.rerun()
```

#### 예시 쿼리 클릭
```python
# Before
if st.button(f"💬 {example}", ...):
    st.session_state.search_query = example
    st.rerun()

# After
if st.button(f"💬 {example}", ...):
    st.session_state.semantic_search_query = example  # 시맨틱 검색창으로
    st.rerun()
```

---

## 사용된 API 엔드포인트

### 1. 시맨틱 검색 (Vector DB)
```http
POST /api/articles/search
Content-Type: application/json

{
  "query": "transformer 아키텍처 최적화",
  "limit": 10,
  "score_threshold": 0.7,
  "source_type": ["paper", "news"],
  "category": ["AI", "NLP"],
  "min_importance_score": 0.5,
  "date_from": "2024-01-01",
  "date_to": "2025-12-05"
}
```

**응답:**
```json
{
  "results": [
    {
      "id": "...",
      "title": "...",
      "summary": "...",
      "similarity_score": 0.92,
      ...
    }
  ],
  "total": 10
}
```

### 2. 키워드 검색 (ILIKE)
```http
GET /api/articles/keyword-search?query=GPT-4&skip=0&limit=20
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
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

### 3. 유사 문서 검색
```http
GET /api/articles/{article_id}/similar?limit=5
```

**응답:**
```json
{
  "results": [
    {
      "id": "...",
      "title": "...",
      "summary": "...",
      "similarity_score": 0.85,
      ...
    }
  ],
  "reference_article": {
    "id": "...",
    "title": "..."
  }
}
```

---

## 검색 기능 비교

| 기능 | 시맨틱 검색 | 키워드 검색 |
|-----|-----------|-----------|
| **검색 방식** | Vector DB (임베딩 유사도) | 텍스트 매칭 (ILIKE) |
| **입력** | 자연어 문장 | 키워드 |
| **검색 대상** | 전체 내용 (임베딩) | 제목, 요약, 내용 |
| **고급 필터** | ✅ 지원 | ❌ 미지원 |
| **유사도 임계값** | ✅ 조정 가능 | ❌ 해당 없음 |
| **정렬** | 유사도 순 | 수집 날짜 순 |
| **사용 예시** | "transformer 최적화 기법" | "GPT-4" |

---

## Search 페이지 구조

### 1. 헤더
```
🔍 시맨틱 검색
과거 자료를 자연어로 검색하세요
```

### 2. 검색 탭 (2개)
```
┌─────────────────────┬─────────────────────┐
│ 🧠 시맨틱 검색       │ 🔤 키워드 검색       │
└─────────────────────┴─────────────────────┘

[시맨틱 검색 탭]
검색어 입력: "transformer 모델 최적화 기법"

[키워드 검색 탭]
키워드 입력: "GPT-4, BERT, attention"
```

### 3. 고급 필터 (시맨틱 검색만 적용)
```
🔧 필터 옵션 (접기/펼치기)

┌────────────┬────────────┬────────────┐
│ Source Type│ Category   │ 최소 중요도 │
│ □ paper    │ □ AI       │ ━━━○━━━   │
│ □ news     │ □ NLP      │   0.5      │
│ □ report   │ □ ML       │            │
│ □ blog     │ □ CV       │            │
└────────────┴────────────┴────────────┘

시작 날짜: 2024-01-01
종료 날짜: 2025-12-05
유사도 임계값: ━━━━━━○━━ 0.7
최대 결과 수: 10
```

### 4. 검색 버튼
```
┌────────────┬────────────┐
│ 🔍 검색     │ 🔄 초기화   │
└────────────┴────────────┘
```

### 5. 검색 결과
```
📋 검색 결과
✅ 10개의 아티클을 찾았습니다.

┌───────────────────────────┐
│ Article Card 1            │
│ - Title                   │
│ - Summary                 │
│ - Similarity: 0.92        │ (시맨틱 검색만)
│ - Source, Category        │
│ - Importance Score        │
│ [원문 보기] [유사 논문]      │
└───────────────────────────┘
...
```

### 6. 검색 예시
```
💡 검색 예시

┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ 💬      │ 💬      │ 💬      │ 💬      │ 💬      │
│ trans-  │ GPT-4   │ BERT    │ atten-  │ few-shot│
│ former  │ 성능    │ 파인    │ tion    │ learning│
│ 최적화  │ 평가    │ 튜닝    │ 개선    │ 기법    │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

---

## 유사 문서 검색 플로우

### 사용자 시나리오
1. 검색 결과에서 아티클 카드 확인
2. "유사 논문" 버튼 클릭
3. `st.session_state["search_similar_id"] = article_id` 설정
4. 페이지 리로드 → `_show_similar_search()` 함수 호출
5. 유사 문서 검색 UI 표시
6. 검색 실행 → 결과 표시
7. "← 검색으로 돌아가기" 버튼으로 복귀

### 유사 문서 검색 UI
```
🔍 유사 문서 검색

← 검색으로 돌아가기

참조 아티클 ID: `abc123...`

최대 결과 수: 5

┌────────────────────┐
│ 🔍 유사 문서 검색   │
└────────────────────┘

📋 유사 문서
✅ 5개의 유사 문서를 찾았습니다.

┌───────────────────────────┐
│ Similar Article Card 1    │
│ - Similarity: 0.89        │
│ ...                       │
└───────────────────────────┘
```

---

## 에러 핸들링

### 1. 검색 실패
```python
except Exception as e:
    st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")
```

### 2. 빈 검색어
```python
elif search_button and not query:
    st.warning("⚠️ 검색어를 입력해주세요.")
```

### 3. 검색 결과 없음
```python
if articles:
    st.success(f"✅ {len(articles)}개의 아티클을 찾았습니다.")
    show_article_list(articles, show_similar_button=True)
else:
    st.warning("검색 결과가 없습니다. 다른 키워드를 시도하거나 필터를 조정해보세요.")
```

### 4. 유사 문서 검색 실패
```python
except Exception as e:
    st.error(f"❌ 오류: {str(e)}")
```

---

## 변경 파일

```
src/app/frontend/pages/search.py
```

**주요 변경사항:**
1. 검색 모드 탭 추가 (시맨틱 vs 키워드)
2. `api.search_articles()` → `api.search_articles_semantic()` 메서드명 수정
3. 키워드 검색 API 호출 추가 (`api.search_articles_keyword()`)
4. `api.find_similar_articles()` → `api.get_similar_articles()` 메서드명 수정
5. 유사 문서 검색에서 `score_threshold` 파라미터 제거
6. 세션 상태 키 분리 (`semantic_search_query`, `keyword_search_query`)

---

## 테스트 시나리오

### 시나리오 1: 시맨틱 검색
1. Search 페이지 접속
2. "🧠 시맨틱 검색" 탭 선택 (기본값)
3. 검색어 입력: "transformer 아키텍처 최적화"
4. 필터 설정:
   - Source Type: paper, news
   - Category: AI, NLP
   - 최소 중요도: 0.5
   - 유사도 임계값: 0.7
5. "🔍 검색" 버튼 클릭
6. 검색 결과 표시 (유사도 점수 포함)

### 시나리오 2: 키워드 검색
1. "🔤 키워드 검색" 탭 클릭
2. 키워드 입력: "GPT-4"
3. "🔍 검색" 버튼 클릭
4. 검색 결과 표시 (제목/요약/내용에서 매칭)

### 시나리오 3: 유사 문서 검색
1. 검색 결과에서 아티클 카드 확인
2. "유사 논문" 버튼 클릭
3. 유사 문서 검색 UI로 전환
4. 최대 결과 수: 5
5. "🔍 유사 문서 검색" 버튼 클릭
6. 유사 문서 목록 표시
7. "← 검색으로 돌아가기" 클릭하여 복귀

### 시나리오 4: 검색 예시 클릭
1. 하단 검색 예시 확인
2. "💬 transformer 최적화" 버튼 클릭
3. 시맨틱 검색창에 자동 입력
4. "🔍 검색" 버튼 클릭
5. 검색 결과 표시

### 시나리오 5: 초기화
1. 검색어 입력 및 검색 실행
2. "🔄 초기화" 버튼 클릭
3. 두 검색창 모두 비워짐
4. 페이지 리로드

---

## 다음 단계 (Checkpoint 4)

**Feedback 페이지 API 연동**:
1. 피드백 제출 구현
2. 피드백 목록 조회
3. 피드백 수정/삭제
4. 아티클별 통계 표시

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 3 완료

**다음**: Checkpoint 4 - Feedback 페이지 API 연동
