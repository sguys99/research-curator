# Day 8 - Checkpoint 3: Dashboard, Search, Settings Pages

**날짜**: 2025-12-05
**작성자**: Research Curator Team
**상태**: ✅ 완료

## 📋 개요

Checkpoint 3에서는 Streamlit 프론트엔드의 핵심 사용자 페이지를 구현했습니다:
- **Dashboard**: 최근 다이제스트와 통계 표시
- **Search**: 시맨틱 검색 및 필터링
- **Settings**: 사용자 설정 관리

## 🎯 구현 목표

1. ✅ 아티클 카드 컴포넌트 생성
2. ✅ Dashboard 페이지 구현
3. ✅ Search 페이지 구현
4. ✅ Settings 페이지 구현
5. ✅ 메인 앱 라우팅 업데이트

## 📂 구현된 파일

### 1. Article Card Component
**파일**: `src/app/frontend/components/article_card.py`

재사용 가능한 아티클 표시 컴포넌트:

```python
def show_article_card(
    title: str,
    summary: str,
    source_type: str,
    category: str,
    importance_score: float,
    url: str,
    collected_at: str | None = None,
    metadata: dict | None = None,
    show_similar_button: bool = False,
    article_id: str | None = None,
)
```

**주요 기능**:
- 아티클 제목, 요약, 메타데이터 표시
- Source type별 이모지 배지 (📚 논문, 📰 뉴스, 📊 리포트)
- 중요도 점수를 별(⭐) 개수로 시각화
- "원문 보기", "유사 논문" 액션 버튼
- 상세 메타데이터 expander

**추가 함수**:
- `show_article_list()`: 아티클 목록 표시
- `show_compact_article_card()`: 컴팩트한 카드 버전 (사이드바용)

### 2. Dashboard Page
**파일**: `src/app/frontend/pages/dashboard.py`

사용자의 최근 다이제스트와 통계를 표시하는 대시보드:

**주요 기능**:
- **통계 카드**: 총 아티클 수, 받은 이메일 수, 평균 피드백 점수
- **최근 이메일**: 최근 3개 다이제스트 표시 (expandable)
- **빠른 작업**: 테스트 이메일 발송, 검색, 설정 이동

**데이터 로딩**:
```python
# 최근 다이제스트 3개 가져오기
digests_response = api.get_user_digests(user_id, skip=0, limit=3)

# 사용자 피드백 가져오기 (평균 계산용)
feedback_response = api.get_user_feedback(user_id, skip=0, limit=100)
```

**통계 계산**:
- 총 아티클 수: 모든 다이제스트의 article_ids 합계
- 받은 이메일: 다이제스트 개수
- 평균 피드백: 피드백 rating의 평균값

### 3. Search Page
**파일**: `src/app/frontend/pages/search.py`

시맨틱 검색 및 유사 문서 검색 페이지:

**주요 기능**:
- **자연어 검색**: 사용자 쿼리로 시맨틱 검색
- **고급 필터**:
  - Source Type: paper, news, report, blog
  - Category: AI, NLP, ML, CV, Robotics, Other
  - 최소 중요도 슬라이더 (0.0 ~ 1.0)
  - 날짜 범위 (시작일, 종료일)
  - 유사도 임계값 (0.0 ~ 1.0)
  - 최대 결과 수 (1 ~ 50)
- **예시 쿼리**: 클릭 가능한 예시 버튼
- **유사 문서 검색**: 아티클 카드에서 "유사 논문" 버튼 클릭 시

**검색 API 호출**:
```python
search_params = {
    "query": query,
    "limit": limit,
    "score_threshold": score_threshold,
    "source_type": source_types,  # optional
    "category": categories,  # optional
    "min_importance_score": min_importance,  # optional
    "date_from": date_from.isoformat(),  # optional
    "date_to": date_to.isoformat(),  # optional
}
response = api.search_articles(**search_params)
```

**유사 문서 검색**:
```python
response = api.find_similar_articles(
    article_id=article_id,
    limit=limit,
    score_threshold=score_threshold,
)
```

### 4. Settings Page
**파일**: `src/app/frontend/pages/settings.py`

사용자 설정 관리 페이지:

**주요 기능**:
- **연구 분야 및 키워드**: 텍스트 영역으로 편집 (쉼표 구분)
- **정보 유형 비율**: 슬라이더로 조정 (논문/뉴스/리포트)
  - 자동 정규화: 합계가 100%가 되도록 조정
  - 합계 표시: 현재 합계가 100%인지 실시간 확인
- **추가 소스**: 웹사이트 URL 입력 (쉼표 구분)
- **이메일 설정**:
  - 발송 시간 선택 (08:00, 09:00, 10:00, 13:00, 18:00, 21:00)
  - 일일 아티클 수 (1 ~ 20)
  - 이메일 수신 여부 체크박스

**설정 로딩**:
```python
preferences = api.get_user_preferences(user_id)
```

**설정 저장**:
```python
# 입력값 파싱
research_fields = [field.strip() for field in input.split(",") if field.strip()]

# 비율 정규화
total = paper_ratio + news_ratio + report_ratio
info_types = {
    "paper": paper_ratio / total,
    "news": news_ratio / total,
    "report": report_ratio / total,
}

# API 호출
api.update_user_preferences(user_id, payload)
```

**도움말 섹션**:
- 설정 가이드 expander
- 현재 설정 요약 (JSON 형식)

### 5. Main App Updates
**파일**: `src/app/frontend/main.py`

라우팅 함수 업데이트:

**변경 전** (Placeholder):
```python
def _show_search_page() -> None:
    show_page_header("🔍 시맨틱 검색", "...")
    st.info("⚠️ 검색 페이지는 Checkpoint 3에서 구현됩니다.")
```

**변경 후** (실제 페이지):
```python
def _show_search_page() -> None:
    from app.frontend.pages.search import show_search_page
    show_search_page()

def _show_settings_page() -> None:
    from app.frontend.pages.settings import show_settings_page
    show_settings_page()
```

## 🔧 기술적 특징

### 1. State Management
- **Session State 활용**: `st.session_state`로 페이지 간 데이터 공유
- **유사 검색 상태**: `search_similar_id`로 유사 문서 검색 모드 전환
- **Navigation State**: `nav_target`으로 페이지 전환

### 2. API Integration
모든 페이지가 FastAPI 백엔드와 통신:
- `api.get_user_digests()`: 다이제스트 목록
- `api.get_user_feedback()`: 피드백 목록
- `api.search_articles()`: 시맨틱 검색
- `api.find_similar_articles()`: 유사 문서 검색
- `api.get_user_preferences()`: 설정 조회
- `api.update_user_preferences()`: 설정 저장
- `api.send_test_digest()`: 테스트 이메일 발송

### 3. UI/UX 패턴
- **Expander**: 긴 콘텐츠 숨기기 (다이제스트, 도움말)
- **Columns**: 레이아웃 정렬 (통계 카드, 필터, 버튼)
- **Spinner**: 로딩 상태 표시 (`st.spinner()`)
- **Form**: 설정 변경 시 일괄 제출 (`st.form()`)
- **Rerun**: 상태 변경 후 페이지 새로고침 (`st.rerun()`)

### 4. Error Handling
모든 API 호출에 try-except 적용:
```python
try:
    response = api.search_articles(**search_params)
    articles = response.get("results", [])
    # Success handling
except Exception as e:
    st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")
```

## 📊 페이지 플로우

### Dashboard Flow
```
1. 로그인 확인
2. 다이제스트 및 피드백 데이터 로딩
3. 통계 계산 및 표시
4. 최근 3개 다이제스트 표시
   - 각 다이제스트의 아티클 로딩
   - 아티클 카드 렌더링
5. 빠른 작업 버튼
   - 테스트 이메일 발송
   - 검색/설정 페이지 이동
```

### Search Flow
```
1. 로그인 확인
2. 유사 검색 모드 확인
   - Yes: 유사 문서 검색 UI
   - No: 일반 검색 UI
3. 검색 입력 및 필터 설정
4. 검색 버튼 클릭
5. API 호출 및 결과 표시
6. 아티클 카드 렌더링
   - "유사 논문" 버튼 → 유사 검색 모드로 전환
```

### Settings Flow
```
1. 로그인 확인
2. 현재 설정 로딩
3. Form 렌더링
   - 연구 분야/키워드 입력
   - 비율 슬라이더 조정
   - 이메일 설정 변경
4. "설정 저장" 버튼 클릭
5. 입력값 파싱 및 검증
6. API 호출 (update_user_preferences)
7. 성공 시 페이지 새로고침
```

## 🎨 UI 컴포넌트

### Statistics Cards
```python
show_stats_cards([
    ("총 아티클", str(total_articles), "📚"),
    ("받은 이메일", str(total_digests), "📧"),
    ("평균 피드백", f"{avg_rating:.1f}", "⭐"),
])
```

### Article Card
- **Header**: 제목, 중요도 별, Source type 배지
- **Summary**: 요약 텍스트
- **Metadata**: 카테고리, 중요도 점수, 날짜
- **Details**: 상세 정보 expander
- **Actions**: 원문 보기, 유사 논문 버튼

### Filter Panel
- **Basic Filters**: Source type, Category 멀티셀렉트
- **Range Filters**: 중요도, 유사도 슬라이더
- **Date Filters**: 시작일, 종료일 date input
- **Limit**: 최대 결과 수 number input

## ✅ 테스트 시나리오

### Dashboard 테스트
1. ✅ 로그인 후 대시보드 접근
2. ✅ 통계 카드 정상 표시
3. ✅ 다이제스트 expander 확장/축소
4. ✅ 아티클 카드 렌더링
5. ✅ 테스트 이메일 발송 버튼
6. ✅ 검색/설정 페이지 이동

### Search 테스트
1. ✅ 검색어 입력 및 검색
2. ✅ 필터 적용 후 검색
3. ✅ 예시 쿼리 버튼 클릭
4. ✅ 검색 결과 표시
5. ✅ "유사 논문" 버튼 클릭
6. ✅ 유사 문서 검색 결과 표시
7. ✅ "검색으로 돌아가기" 버튼

### Settings 테스트
1. ✅ 현재 설정 로딩
2. ✅ 연구 분야/키워드 편집
3. ✅ 비율 슬라이더 조정
4. ✅ 합계 100% 검증
5. ✅ 이메일 설정 변경
6. ✅ "설정 저장" 버튼
7. ✅ 설정 재로딩 확인

## 🐛 알려진 이슈 및 제한사항

### 현재 제한사항
1. **오프라인 모드**: API 서버가 실행 중이어야 함
2. **실시간 검증**: 키워드/URL 형식 검증 없음
3. **파일 업로드**: 대량 키워드 업로드 미지원
4. **다국어**: 현재 한국어만 지원

### 향후 개선사항
1. **검색 히스토리**: 최근 검색어 저장
2. **필터 프리셋**: 자주 사용하는 필터 저장
3. **설정 백업**: 설정 내보내기/가져오기
4. **다크 모드**: 테마 전환 지원

## 📈 성능 고려사항

### API 호출 최적화
- Dashboard: 초기 로딩 시 2개 API 호출 (digests, feedback)
- Search: 검색 버튼 클릭 시에만 호출
- Settings: 페이지 로드 시 1개, 저장 시 1개 호출

### 데이터 캐싱
- Session state로 중복 API 호출 방지
- `st.spinner()`로 로딩 상태 명시

### 렌더링 최적화
- Expander로 긴 콘텐츠 지연 렌더링
- 페이지네이션 대신 limit 파라미터 사용

## 🔐 보안 고려사항

1. **인증 확인**: 모든 페이지에서 `is_authenticated()` 검사
2. **User ID 검증**: 세션에서 user_id 추출하여 API 호출
3. **입력 검증**: API 서버에서 Pydantic 스키마로 검증
4. **에러 메시지**: 민감한 정보 노출 방지

## 📝 커밋 내역

```bash
✨ Implement Search and Settings pages for Checkpoint 3

Complete the main user-facing pages for the Streamlit frontend.

**Search Page (pages/search.py)**
- Semantic search with natural language queries
- Advanced filters: source_type, category, importance, date range
- Similar document search feature
- Example query buttons for quick testing
- Integration with vector DB search API

**Settings Page (pages/settings.py)**
- Research fields and keywords editor
- Info type ratio sliders (paper/news/report)
- Custom source URL management
- Email settings (time, daily limit, enable/disable)
- Auto-normalization of percentages to 100%
- Current settings summary view

**Main App Updates**
- Route search page to actual implementation
- Route settings page to actual implementation
- Remove placeholder pages
```

## 🎓 학습 포인트

### Streamlit 활용
1. **Form 컴포넌트**: 일괄 제출로 UX 개선
2. **Session State**: 페이지 간 상태 공유
3. **Rerun 패턴**: 상태 변경 후 UI 갱신
4. **Dynamic UI**: 조건부 렌더링과 모드 전환

### API 통합
1. **HTTPx 클라이언트**: 비동기 미사용, 동기 호출
2. **에러 핸들링**: try-except로 안전한 API 호출
3. **Pydantic 스키마**: 타입 안전성 보장

### UX 패턴
1. **Progressive Disclosure**: Expander로 정보 계층화
2. **Immediate Feedback**: Spinner, Success/Error 메시지
3. **Guided Actions**: 예시 쿼리, 도움말 섹션

## 📚 참고 자료

- [Streamlit Documentation](https://docs.streamlit.io)
- [FastAPI Client Integration](https://fastapi.tiangolo.com/advanced/client/)
- [Qdrant Vector Search](https://qdrant.tech/documentation/)

## ✅ 완료 체크리스트

- [x] Article Card 컴포넌트 구현
- [x] Dashboard 페이지 구현
- [x] Search 페이지 구현
- [x] Settings 페이지 구현
- [x] Main 라우팅 업데이트
- [x] Pre-commit 검사 통과
- [x] 커밋 및 푸시
- [x] 문서화 완료

## 🚀 다음 단계 (Checkpoint 4)

1. **Feedback 페이지**: 아티클 평가 및 피드백 제출
2. **Integration Testing**: 전체 플로우 테스트
3. **E2E 테스트**: Selenium/Playwright로 자동화 테스트
4. **배포 준비**: Docker 컨테이너화, 환경 변수 설정

---

**작성 완료**: 2025-12-05
**소요 시간**: 약 1시간
**난이도**: ⭐⭐⭐ (중)
