# Admin Management Page - Simplified Implementation Plan

## 🎯 Overview

**기존 코드 수정 최소화** 전략으로 admin 페이지만 추가합니다.

- **DB 변경 없음** (User 테이블에 is_admin 필드 추가 안함)
- **API 변경 최소화** (기존 API 최대한 활용)
- **하드코딩 권한 체크** (sguys99@gmail.com만 접근 가능)
- **Streamlit 페이지 1개만 추가**

---

## 📝 Implementation Strategy

### ✅ 장점

- 기존 코드 변경 없이 빠른 구현
- DB 마이그레이션 불필요
- 테스트 부담 최소화
- 즉시 사용 가능

### ⚠️ 제약사항

- 관리자 이메일은 하드코딩 (sguys99@gmail.com)
- 관리자 추가/삭제는 코드 수정 필요
- Audit log 없음
- Job execution log 없음 (스케줄러 API 활용)

---

## 🚀 Implementation Plan

### Step 1: Admin Helper Function 추가

**파일**: `src/app/frontend/utils/session.py`

```python
def is_admin_user() -> bool:
    """Check if current user is admin (hardcoded)."""
    ADMIN_EMAILS = ["sguys99@gmail.com"]
    user_email = get_user_email()
    return user_email in ADMIN_EMAILS if user_email else False
```

**변경사항**: 기존 파일에 함수 1개만 추가

---

### Step 2: Admin Page 생성

**파일**: `src/app/frontend/pages/admin.py` (신규 생성)

#### 페이지 구조

```python
import streamlit as st
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import is_authenticated, is_admin_user

def show_admin_page():
    """Admin dashboard page."""
    # 1. 인증 체크
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    # 2. 관리자 권한 체크
    if not is_admin_user():
        st.error("🚫 관리자 권한이 필요합니다.")
        st.stop()

    st.title("🛠️ Admin Dashboard")

    # 3. 탭 구조
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 System Overview",
        "👥 Users",
        "📚 Articles",
        "📧 Digests"
    ])

    with tab1:
        show_system_overview()

    with tab2:
        show_users_section()

    with tab3:
        show_articles_section()

    with tab4:
        show_digests_section()
```

#### Tab 1: System Overview

**기존 API 활용**:

- `GET /api/articles/statistics/summary` - 아티클 통계
- `GET /api/scheduler/status` - 스케줄러 상태
- `GET /api/scheduler/jobs` - Job 목록

**표시 내용**:

```python
def show_system_overview():
    """System-wide statistics."""
    api = get_api_client()

    # 기본 통계 (DB 쿼리 직접)
    st.subheader("📊 System Statistics")

    col1, col2, col3, col4 = st.columns(4)

    # 사용자 통계 (DB 직접 조회 필요)
    with col1:
        user_count = get_total_user_count()  # 새로운 helper
        st.metric("Total Users", user_count)

    with col2:
        article_stats = api.get_article_statistics()
        st.metric("Total Articles", article_stats.get("total", 0))

    with col3:
        digest_count = get_total_digest_count()  # 새로운 helper
        st.metric("Digests Sent", digest_count)

    with col4:
        feedback_count = get_total_feedback_count()  # 새로운 helper
        st.metric("Total Feedback", feedback_count)

    # 스케줄러 상태
    st.subheader("⚙️ Scheduler Status")
    scheduler_status = api.get_scheduler_status()

    if scheduler_status.get("running"):
        st.success("✅ Scheduler is running")
        jobs = scheduler_status.get("jobs", [])

        for job in jobs:
            with st.expander(f"📅 {job.get('name')}"):
                st.write(f"Next run: {job.get('next_run_time', 'N/A')}")
    else:
        st.warning("⚠️ Scheduler is stopped")
```

#### Tab 2: Users Section

**기존 API 활용**:

- DB 직접 쿼리로 모든 사용자 조회

**표시 내용**:

```python
def show_users_section():
    """List all users with their stats."""
    st.subheader("👥 All Users")

    # DB에서 모든 사용자 조회
    users = get_all_users_with_stats()  # 새로운 helper

    # 검색 필터
    search = st.text_input("🔍 Search by email or name")

    # 필터링
    if search:
        users = [u for u in users if search.lower() in u['email'].lower()
                 or search.lower() in u.get('name', '').lower()]

    # 테이블 형태로 표시
    st.write(f"Total: {len(users)} users")

    for user in users:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.write(f"**{user['name']}** ({user['email']})")
                st.caption(f"ID: {user['id']} | Joined: {user['created_at'][:10]}")

            with col2:
                st.write(f"📧 {user['digest_count']} digests")
                st.write(f"💬 {user['feedback_count']} feedbacks")

            with col3:
                st.write(f"Last login: {user.get('last_login', 'N/A')[:10]}")

            st.divider()
```

#### Tab 3: Articles Section

**기존 API 활용**:

- `GET /api/articles/statistics/summary`
- `GET /api/articles` with filters

**표시 내용**:

```python
def show_articles_section():
    """Articles statistics and list."""
    st.subheader("📚 Articles")

    api = get_api_client()

    # 통계
    stats = api.get_article_statistics()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stats.get("total", 0))
    with col2:
        st.metric("By Category", "")
        for cat, count in stats.get("by_category", {}).items():
            st.write(f"{cat}: {count}")
    with col3:
        st.metric("By Source", "")
        for src, count in stats.get("by_source_type", {}).items():
            st.write(f"{src}: {count}")

    # 최근 아티클 목록
    st.subheader("Recent Articles")

    limit = st.slider("Show articles", 10, 100, 20)
    articles_response = api.get_articles(skip=0, limit=limit)
    articles = articles_response.get("articles", [])

    for article in articles:
        with st.expander(f"📄 {article.get('title', 'Untitled')}"):
            st.write(f"**Source**: {article.get('source_type', 'N/A')}")
            st.write(f"**Category**: {article.get('category', 'N/A')}")
            st.write(f"**Importance**: {article.get('importance_score', 0):.2f}")
            st.write(f"**Collected**: {article.get('collected_at', 'N/A')[:10]}")

            if article.get('summary'):
                st.write(f"**Summary**: {article['summary'][:200]}...")
```

#### Tab 4: Digests Section

**기존 API 활용**:

- DB 직접 쿼리로 모든 digest 조회

**표시 내용**:

```python
def show_digests_section():
    """All digest history across all users."""
    st.subheader("📧 Digest History")

    # 모든 digest 조회
    digests = get_all_digests()  # 새로운 helper

    st.write(f"Total: {len(digests)} digests sent")

    # 날짜 필터
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From")
    with col2:
        end_date = st.date_input("To")

    # 필터링
    # ... (날짜 필터 로직)

    # 테이블
    for digest in digests[:50]:  # 최근 50개
        with st.expander(f"📧 {digest['user_email']} - {digest['sent_at'][:10]}"):
            st.write(f"User: {digest['user_name']} ({digest['user_email']})")
            st.write(f"Articles: {len(digest['article_ids'])} articles")
            st.write(f"Sent: {digest['sent_at']}")

            if digest.get('email_opened'):
                st.success(f"✅ Opened at {digest['opened_at']}")
            else:
                st.info("📭 Not opened yet")
```

---

### Step 3: Helper Functions 추가

**파일**: `src/app/frontend/utils/db_helpers.py` (신규 생성)

DB 직접 쿼리를 위한 helper 함수들:

```python
"""Database helper functions for admin page."""

from sqlalchemy import func, select
from app.db.session import get_db
from app.db.models import User, SentDigest, Feedback, CollectedArticle

def get_total_user_count() -> int:
    """Get total number of users."""
    db = next(get_db())
    result = db.execute(select(func.count(User.id)))
    return result.scalar_one()

def get_total_digest_count() -> int:
    """Get total number of digests sent."""
    db = next(get_db())
    result = db.execute(select(func.count(SentDigest.id)))
    return result.scalar_one()

def get_total_feedback_count() -> int:
    """Get total number of feedbacks."""
    db = next(get_db())
    result = db.execute(select(func.count(Feedback.id)))
    return result.scalar_one()

def get_all_users_with_stats() -> list[dict]:
    """Get all users with their statistics."""
    db = next(get_db())

    # User 기본 정보 + digest count + feedback count
    stmt = (
        select(
            User.id,
            User.email,
            User.name,
            User.created_at,
            User.last_login,
            func.count(SentDigest.id).label("digest_count"),
            func.count(Feedback.id).label("feedback_count")
        )
        .outerjoin(SentDigest, User.id == SentDigest.user_id)
        .outerjoin(Feedback, User.id == Feedback.user_id)
        .group_by(User.id)
    )

    result = db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": str(row.id),
            "email": row.email,
            "name": row.name or "N/A",
            "created_at": row.created_at.isoformat(),
            "last_login": row.last_login.isoformat() if row.last_login else None,
            "digest_count": row.digest_count,
            "feedback_count": row.feedback_count
        }
        for row in rows
    ]

def get_all_digests() -> list[dict]:
    """Get all digests with user info."""
    db = next(get_db())

    stmt = (
        select(SentDigest, User.email, User.name)
        .join(User, SentDigest.user_id == User.id)
        .order_by(SentDigest.sent_at.desc())
    )

    result = db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": str(row.SentDigest.id),
            "user_id": str(row.SentDigest.user_id),
            "user_email": row.email,
            "user_name": row.name or "N/A",
            "article_ids": row.SentDigest.article_ids,
            "sent_at": row.SentDigest.sent_at.isoformat(),
            "email_opened": row.SentDigest.email_opened,
            "opened_at": row.SentDigest.opened_at.isoformat() if row.SentDigest.opened_at else None
        }
        for row in rows
    ]
```

---

### Step 4: Navigation 추가

**파일**: `src/app/frontend/main.py`

```python
# Sidebar에 Admin 링크 추가 (관리자에게만 표시)
from app.frontend.utils.session import is_admin_user

if is_admin_user():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ Admin")

    if st.sidebar.button("Admin Dashboard"):
        st.session_state.current_page = "admin"
        st.rerun()
```

**페이지 라우팅에 추가**:

```python
# main.py의 페이지 라우팅 로직에 추가
if current_page == "admin":
    from app.frontend.pages.admin import show_admin_page
    show_admin_page()
```

---

## 📁 Files to Create/Modify

### 신규 파일 (2개)

1. `src/app/frontend/pages/admin.py` - Admin 페이지 메인
2. `src/app/frontend/utils/db_helpers.py` - DB 쿼리 helper 함수들

### 수정 파일 (2개)

1. `src/app/frontend/utils/session.py` - `is_admin_user()` 함수 추가
2. `src/app/frontend/main.py` - Navigation 및 라우팅 추가

---

## 🎯 Implementation Checklist

- [ ] `is_admin_user()` helper 추가 (session.py)
- [ ] DB helper functions 생성 (db_helpers.py)
- [ ] Admin page 생성 (admin.py)
  - [ ] System Overview tab
  - [ ] Users tab
  - [ ] Articles tab
  - [ ] Digests tab
- [ ] Navigation 추가 (main.py)
- [ ] 테스트: sguys99@gmail.com으로 로그인하여 접근 확인
- [ ] 테스트: 다른 이메일로 접근 차단 확인

---

## 🔒 Security

- 하드코딩된 관리자 이메일 리스트 사용
- 프론트엔드 레벨에서만 권한 체크 (백엔드 보호 없음)
- **주의**: 프로덕션 환경에서는 백엔드 권한 체크 추가 필요

---

## 🚀 Future Enhancements (Optional)

추후 필요시 확장 가능:

1. **환경변수로 관리자 이메일 관리** (`.env`에 `ADMIN_EMAILS=sguys99@gmail.com,other@email.com`)
2. **User 테이블에 is_admin 필드 추가** (DB 마이그레이션 필요)
3. **Admin API 엔드포인트 추가** (백엔드 권한 체크)
4. **Audit Log 추가** (관리자 작업 추적)
5. **Job Execution Log** (스케줄러 작업 이력)

하지만 **현재는 최소한의 변경**으로 admin 페이지만 구현합니다.

---

## ✅ Success Criteria

- [ ] sguys99@gmail.com 계정으로 Admin Dashboard 접근 가능
- [ ] 다른 사용자는 접근 불가 (에러 메시지 표시)
- [ ] System Overview에서 전체 통계 확인 가능
- [ ] Users 탭에서 모든 사용자 목록 확인 가능
- [ ] Articles 탭에서 아티클 통계 및 목록 확인 가능
- [ ] Digests 탭에서 전체 발송 이력 확인 가능
