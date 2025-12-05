# Day 9-2 Checkpoint 4: Feedback 페이지 API 연동

## 작업 개요

**목표**: Feedback 페이지를 실제 Backend API와 연동

**작업 시간**: 2025-12-05

**상태**: ✅ **완료**

---

## 구현 내용

### 1. 피드백 제출 API 연동

#### 변경 전 (잘못된 메서드명 + 파라미터)
```python
# Load articles individually (N API calls)
articles = []
for aid in article_ids:
    try:
        article = api.get_article(aid)
        articles.append(article)
    except Exception:
        continue

# Submit feedback with user_id
result = api.submit_feedback(
    user_id=user_id,  # 제거 필요
    article_id=article_id,
    rating=rating,
    comment=comment,
)
```

**문제점:**
1. 아티클 로딩: N번의 개별 API 호출 (성능 문제)
2. 메서드명: `submit_feedback` (일관성 부족)
3. `user_id` 파라미터: JWT에서 자동 할당되므로 불필요

#### 변경 후 (배치 API + 올바른 메서드)
```python
# Load articles using batch API (1 API call)
try:
    batch_response = api.get_articles_batch(article_ids)
    articles = batch_response.get("articles", [])

    if not articles:
        st.warning("아티클을 불러올 수 없습니다.")
        return
except Exception as e:
    st.error(f"아티클 로딩 오류: {str(e)}")
    return

# Create feedback (user_id from JWT)
result = api.create_feedback(
    article_id=article_id,
    rating=rating,
    comment=comment if comment else None,
)
```

**개선 사항:**
1. **배치 API 사용**: N개 아티클 → 1번 API 호출 (성능 향상)
2. **메서드명 수정**: `submit_feedback` → `create_feedback`
3. **파라미터 정리**: `user_id` 제거 (JWT에서 자동 처리)
4. **빈 코멘트 처리**: 빈 문자열 대신 `None` 전달

---

### 2. 피드백 이력 조회 API 연동

#### 변경 전 (잘못된 필드명)
```python
feedback_response = api.get_user_feedback(user_id, skip=0, limit=50)
feedbacks = feedback_response.get("feedbacks", [])  # 잘못된 필드명
```

**문제점:**
- Backend API 응답 필드: `feedback` (단수형)
- 코드에서 사용: `feedbacks` (복수형)
- 필드명 불일치로 빈 리스트 반환

#### 변경 후 (올바른 필드명)
```python
feedback_response = api.get_user_feedback(user_id, skip=0, limit=50)
feedbacks = feedback_response.get("feedback", [])  # 수정
```

**개선 사항:**
- Backend API 스키마에 맞는 필드명 사용
- 정확한 데이터 로딩

---

### 3. 피드백 수정/삭제 기능 추가 (신규)

#### 이전 상태
- 피드백 조회만 가능
- 수정/삭제 기능 없음

#### 추가된 기능

**1. 수정 버튼 및 인라인 편집 UI**
```python
# Action buttons
action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("✏️ 수정", key=f"edit_{idx}", use_container_width=True):
        st.session_state[f"edit_feedback_{feedback.get('id')}"] = True
        st.rerun()

with action_col2:
    if st.button("🗑️ 삭제", key=f"delete_{idx}", use_container_width=True):
        with st.spinner("삭제 중..."):
            try:
                api.delete_feedback(feedback.get("id"))
                st.success("피드백이 삭제되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 실패: {str(e)}")
```

**2. 인라인 편집 모드**
```python
# Edit mode
if st.session_state.get(f"edit_feedback_{feedback.get('id')}"):
    st.markdown("---")
    st.markdown("**✏️ 피드백 수정**")

    new_rating = st.select_slider(
        "새 평점",
        options=[1, 2, 3, 4, 5],
        value=feedback.get("rating", 3),
        key=f"new_rating_{idx}",
    )

    new_comment = st.text_area(
        "새 코멘트",
        value=feedback.get("comment", ""),
        max_chars=1000,
        key=f"new_comment_{idx}",
    )

    update_col1, update_col2 = st.columns(2)

    with update_col1:
        if st.button("💾 저장", key=f"save_{idx}", use_container_width=True):
            with st.spinner("업데이트 중..."):
                try:
                    api.update_feedback(
                        feedback_id=feedback.get("id"),
                        rating=new_rating,
                        comment=new_comment if new_comment else None,
                    )
                    st.success("피드백이 업데이트되었습니다.")
                    st.session_state.pop(f"edit_feedback_{feedback.get('id')}")
                    st.rerun()
                except Exception as e:
                    st.error(f"업데이트 실패: {str(e)}")

    with update_col2:
        if st.button("❌ 취소", key=f"cancel_{idx}", use_container_width=True):
            st.session_state.pop(f"edit_feedback_{feedback.get('id')}")
            st.rerun()
```

**개선 사항:**
1. **수정 기능**: 인라인 편집 모드로 평점과 코멘트 수정
2. **삭제 기능**: 즉시 삭제 및 페이지 리로드
3. **UX 개선**: 편집 모드 토글, 취소 버튼, 즉각적인 피드백

---

### 4. 아티클별 통계 탭 추가 (신규)

#### 이전 상태
- 탭: "📝 피드백 제출", "📊 피드백 이력" (2개)
- 아티클별 통계 조회 기능 없음

#### 추가된 기능

**1. 새로운 탭 추가**
```python
# Tab selection
tab1, tab2, tab3 = st.tabs(["📝 피드백 제출", "📊 피드백 이력", "📈 아티클 통계"])

with tab1:
    _show_feedback_submission(api, user_id)

with tab2:
    _show_feedback_history(api, user_id)

with tab3:
    _show_article_stats(api)  # 신규
```

**2. 아티클 통계 조회 기능**
```python
def _show_article_stats(api):
    """Show article feedback statistics."""
    # Article ID input
    article_id = st.text_input(
        "아티클 ID 입력",
        placeholder="예: 123e4567-e89b-12d3-a456-426614174000",
    )

    if not article_id:
        return

    # Load article info
    article = api.get_article(article_id)

    # Load feedback statistics
    stats = api.get_article_feedback_stats(article_id)

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 피드백 수", stats.get("count", 0))

    with col2:
        avg_rating = stats.get("average_rating", 0.0)
        st.metric("평균 평점", f"{avg_rating:.2f} ⭐")

    with col3:
        rating_dist = stats.get("rating_distribution", {})
        if rating_dist:
            most_common = max(rating_dist.items(), key=lambda x: x[1])
            st.metric("최다 평점", f"{most_common[0]} ⭐ ({most_common[1]}개)")
```

**3. 평점 분포 시각화**
```python
# Rating distribution
rating_dist = stats.get("rating_distribution", {})
total = stats.get("count", 0)

if total > 0:
    dist_cols = st.columns(5)
    for i in range(1, 6):
        count = rating_dist.get(str(i), 0)
        pct = (count / total * 100) if total > 0 else 0

        with dist_cols[i - 1]:
            st.metric(f"{i}⭐", f"{count}개", f"{pct:.1f}%")

    # Visual bar chart
    for i in range(5, 0, -1):  # 5 to 1
        count = rating_dist.get(str(i), 0)
        pct = (count / total * 100) if total > 0 else 0
        bar_length = int(pct / 2)  # Scale to 50 chars max
        bar = "█" * bar_length
        st.text(f"{i}⭐ │{bar} {pct:.1f}% ({count}개)")
```

**4. 최근 피드백 표시**
```python
# Load recent feedbacks for this article
feedback_response = api.get_article_feedback(article_id, skip=0, limit=10)
feedbacks = feedback_response.get("feedback", [])

if feedbacks:
    for idx, fb in enumerate(feedbacks):
        with st.expander(
            f"{'⭐' * fb.get('rating', 0)} - {fb.get('created_at', 'N/A')[:10]}",
            expanded=(idx < 3),
        ):
            st.markdown(f"**평점**: {'⭐' * fb.get('rating', 0)}")

            if fb.get("comment"):
                st.markdown(f"**코멘트**: {fb.get('comment')}")

            st.caption(f"사용자 ID: `{str(fb.get('user_id', 'N/A'))[:8]}...`")
```

**개선 사항:**
1. **아티클별 통계**: 전체 사용자의 피드백 집계
2. **평점 분포**: 시각적 바 차트로 표시
3. **최근 피드백**: 아티클에 대한 최신 피드백 10개
4. **아티클 정보**: 제목, 요약, 출처 표시

---

## 사용된 API 엔드포인트

### 1. 피드백 생성
```http
POST /api/feedback
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "article_id": "uuid",
  "rating": 5,
  "comment": "매우 유용한 아티클입니다!"
}
```

**응답:**
```json
{
  "id": "feedback-uuid",
  "user_id": "user-uuid",  // JWT에서 자동 할당
  "article_id": "article-uuid",
  "rating": 5,
  "comment": "매우 유용한 아티클입니다!",
  "created_at": "2025-12-05T10:00:00Z"
}
```

### 2. 사용자 피드백 목록
```http
GET /api/feedback/user/{user_id}?skip=0&limit=50
Authorization: Bearer <JWT_TOKEN>
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
      "comment": "...",
      "created_at": "2025-12-05T10:00:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 50
}
```

### 3. 피드백 수정
```http
PUT /api/feedback/{feedback_id}
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "rating": 4,
  "comment": "수정된 코멘트"
}
```

### 4. 피드백 삭제
```http
DELETE /api/feedback/{feedback_id}
Authorization: Bearer <JWT_TOKEN>
```

**응답:**
```json
{
  "message": "Feedback deleted successfully"
}
```

### 5. 아티클 피드백 통계
```http
GET /api/feedback/article/{article_id}/stats
Authorization: Bearer <JWT_TOKEN>
```

**응답:**
```json
{
  "article_id": "uuid",
  "count": 100,
  "average_rating": 4.25,
  "rating_distribution": {
    "1": 2,
    "2": 5,
    "3": 18,
    "4": 35,
    "5": 40
  }
}
```

### 6. 아티클별 피드백 목록
```http
GET /api/feedback/article/{article_id}?skip=0&limit=10
Authorization: Bearer <JWT_TOKEN>
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
      "comment": "...",
      "created_at": "2025-12-05T10:00:00Z"
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 10
}
```

### 7. 아티클 배치 조회
```http
POST /api/articles/batch
Content-Type: application/json

{
  "article_ids": ["id1", "id2", "id3"]
}
```

---

## Feedback 페이지 구조

### 1. 헤더
```
💬 피드백
받은 아티클을 평가해주세요
```

### 2. 탭 (3개)
```
┌───────────┬───────────┬───────────┐
│ 📝 피드백 │ 📊 피드백 │ 📈 아티클 │
│   제출    │   이력    │   통계    │
└───────────┴───────────┴───────────┘
```

### 3. 탭 1: 피드백 제출
```
📝 아티클 피드백 제출

피드백 방법 선택:
○ 최근 다이제스트에서 선택
○ 아티클 ID 직접 입력

[다이제스트 선택]
다이제스트 1 - 2025-12-05 ▼

[아티클 선택]
Transformer Architecture... ▼

📄 선택한 아티클 미리보기
제목: ...
요약: ...
출처: ...

---

⭐ 평가

평점 (1-5): ━━━○━━ 3
⭐⭐⭐☆☆

💭 코멘트 (선택사항)
[텍스트 입력창]
0/500 자

---

        [📤 피드백 제출]
```

### 4. 탭 2: 피드백 이력
```
📊 피드백 이력

📈 통계
┌────────────┬────────────┬────────────┐
│ 총 피드백 수│ 평균 평점   │ 최다 평점   │
│     25     │  4.2 ⭐    │   5 ⭐     │
└────────────┴────────────┴────────────┘

📊 평점 분포
┌───┬───┬───┬───┬───┐
│1⭐│2⭐│3⭐│4⭐│5⭐│
│2개│3개│5개│7개│8개│
│8% │12%│20%│28%│32%│
└───┴───┴───┴───┴───┘

---

📝 피드백 목록

평점 필터: [1⭐, 2⭐, 3⭐, 4⭐, 5⭐]
정렬: [최신순 ▼]

25개의 피드백

⭐⭐⭐⭐⭐ - 2025-12-05
  아티클 ID: `abc123...`
  평점: ⭐⭐⭐⭐⭐
  코멘트: 매우 유용했습니다!

  제출일: 2025-12-05
  피드백 ID: `def456...`

  [✏️ 수정] [🗑️ 삭제]

  ✏️ 피드백 수정
  새 평점: ━━━━○ 4
  새 코멘트: [수정된 내용]

  [💾 저장] [❌ 취소]
```

### 5. 탭 3: 아티클 통계 (신규)
```
📈 아티클 피드백 통계

아티클 ID 입력: [uuid 입력창]

---

📄 아티클 정보           🔗 링크
제목: ...                [원문 보기]
요약: ...
출처: paper
카테고리: AI

---

📊 피드백 통계

┌────────────┬────────────┬────────────┐
│ 총 피드백 수│ 평균 평점   │ 최다 평점   │
│    100     │  4.25 ⭐   │ 5 ⭐ (40개)│
└────────────┴────────────┴────────────┘

---

⭐ 평점 분포

┌───┬───┬───┬───┬───┐
│1⭐│2⭐│3⭐│4⭐│5⭐│
│2개│5개│18개│35개│40개│
│2% │5% │18% │35% │40% │
└───┴───┴───┴───┴───┘

분포 차트
5⭐ │████████████████████ 40.0% (40개)
4⭐ │█████████████████ 35.0% (35개)
3⭐ │█████████ 18.0% (18개)
2⭐ │██ 5.0% (5개)
1⭐ │█ 2.0% (2개)

---

💬 최근 피드백
최근 10개의 피드백

⭐⭐⭐⭐⭐ - 2025-12-05
  평점: ⭐⭐⭐⭐⭐
  코멘트: 매우 유용했습니다!
  사용자 ID: `abc123...`
```

---

## 성능 개선

### Before (개별 아티클 조회)
```
다이제스트 아티클 10개 로딩:
- API 호출: 10번
- 네트워크 왕복: 10 RTT
- 예상 시간: ~1-2초
```

### After (배치 조회)
```
다이제스트 아티클 10개 로딩:
- API 호출: 1번
- 네트워크 왕복: 1 RTT
- 예상 시간: ~0.1-0.2초

성능 향상: 약 10배
```

---

## 변경 파일

```
src/app/frontend/pages/feedback.py
```

**주요 변경사항:**
1. 아티클 로딩을 배치 API로 변경
2. `api.submit_feedback()` → `api.create_feedback()` 메서드명 수정
3. `user_id` 파라미터 제거 (JWT 자동 할당)
4. `feedbacks` → `feedback` 필드명 수정
5. 피드백 수정/삭제 기능 추가
6. 아티클별 통계 탭 추가 (신규)
7. 평점 분포 시각화

---

## 테스트 시나리오

### 시나리오 1: 피드백 제출
1. Feedback 페이지 접속
2. "📝 피드백 제출" 탭 선택
3. "최근 다이제스트에서 선택" 선택
4. 다이제스트 및 아티클 선택
5. 평점 설정: 5⭐
6. 코멘트 입력: "매우 유용했습니다!"
7. "📤 피드백 제출" 버튼 클릭
8. 성공 메시지 및 풍선 효과 표시

### 시나리오 2: 피드백 이력 조회
1. "📊 피드백 이력" 탭 클릭
2. 통계 카드 확인 (총 피드백, 평균 평점, 최다 평점)
3. 평점 분포 확인
4. 필터 설정: 4⭐, 5⭐만 선택
5. 정렬: "평점 높은 순"
6. 필터링된 피드백 목록 확인

### 시나리오 3: 피드백 수정
1. 피드백 이력에서 특정 피드백 선택
2. "✏️ 수정" 버튼 클릭
3. 편집 모드 활성화
4. 새 평점: 4⭐
5. 새 코멘트: "수정된 내용"
6. "💾 저장" 버튼 클릭
7. 업데이트 성공 메시지
8. 페이지 리로드하여 변경사항 확인

### 시나리오 4: 피드백 삭제
1. 피드백 이력에서 특정 피드백 선택
2. "🗑️ 삭제" 버튼 클릭
3. 삭제 진행 중 스피너 표시
4. 삭제 성공 메시지
5. 페이지 리로드하여 피드백 제거 확인

### 시나리오 5: 아티클 통계 조회
1. "📈 아티클 통계" 탭 클릭
2. 아티클 ID 입력
3. 아티클 정보 로딩
4. 통계 카드 확인 (총 피드백, 평균 평점, 최다 평점)
5. 평점 분포 확인 (숫자 + 바 차트)
6. 최근 피드백 목록 확인

---

## 다음 단계 (Checkpoint 5)

**Settings 페이지 API 연동**:
1. 사용자 설정 조회
2. 설정 업데이트
3. 이메일 발송 시간 설정
4. 관심 분야/키워드 설정

---

**작성일**: 2025-12-05
**작성자**: Claude Code
**상태**: ✅ Checkpoint 4 완료

**다음**: Checkpoint 5 - Settings 페이지 API 연동
