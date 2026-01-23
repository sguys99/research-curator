"""관리자 대시보드 페이지."""

import streamlit as st

from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.db_helpers import (
    get_all_digests,
    get_all_users_with_stats,
    get_total_digest_count,
    get_total_feedback_count,
    get_total_user_count,
)
from app.frontend.utils.session import is_admin_user, is_authenticated


def show_admin_page() -> None:
    """관리자 대시보드 페이지를 표시한다."""
    # 1. 인증 체크
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    # 2. 관리자 권한 체크
    if not is_admin_user():
        st.error("🚫 관리자 권한이 필요합니다.")
        st.stop()

    st.title("🛠️ Admin Dashboard")

    # 3. 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 System Overview",
            "👥 Users",
            "📚 Articles",
            "📧 Digests",
        ],
    )

    with tab1:
        show_system_overview()

    with tab2:
        show_users_section()

    with tab3:
        show_articles_section()

    with tab4:
        show_digests_section()


def show_system_overview() -> None:
    """시스템 전체 통계를 표시한다."""
    st.subheader("📊 System Statistics")

    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            user_count = get_total_user_count()
            st.metric("Total Users", user_count)
        except Exception as e:
            st.error(f"Error loading user count: {e}")
            st.metric("Total Users", "N/A")

    with col2:
        try:
            api = get_api_client()
            article_stats = api.get_article_statistics()
            st.metric("Total Articles", article_stats.get("total", 0))
        except Exception as e:
            st.error(f"Error loading article stats: {e}")
            st.metric("Total Articles", "N/A")

    with col3:
        try:
            digest_count = get_total_digest_count()
            st.metric("Digests Sent", digest_count)
        except Exception as e:
            st.error(f"Error loading digest count: {e}")
            st.metric("Digests Sent", "N/A")

    with col4:
        try:
            feedback_count = get_total_feedback_count()
            st.metric("Total Feedback", feedback_count)
        except Exception as e:
            st.error(f"Error loading feedback count: {e}")
            st.metric("Total Feedback", "N/A")

    st.markdown("---")

    # 스케줄러 상태
    st.subheader("⚙️ Scheduler Status")

    st.info(
        "ℹ️ **안내**: 스케줄러는 별도의 프로세스로 실행됩니다. "
        "아래 상태는 모니터링 전용이며, 실제 스케줄러는 서버에서 독립적으로 관리됩니다.",
    )

    try:
        # 단독 스케줄러 상태 확인
        import psutil

        scheduler_running = False
        scheduler_pids = []

        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline")
                if cmdline and "scheduler.main" in " ".join(cmdline):
                    scheduler_running = True
                    scheduler_pids.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        col_status1, col_status2 = st.columns([3, 1])

        with col_status1:
            if scheduler_running:
                st.success(
                    f"✅ Standalone 스케줄러가 실행 중입니다 "
                    f"(PID: {', '.join(map(str, scheduler_pids))})",
                )

                # API에서 잡 정보 조회(표시 전용)
                try:
                    api = get_api_client()
                    scheduler_status = api.get_scheduler_status()
                    jobs = scheduler_status.get("jobs", [])

                    if jobs:
                        for job in jobs:
                            with st.expander(f"📅 {job.get('name', 'Unknown')}"):
                                st.write(f"**Next run**: {job.get('next_run_time', 'N/A')}")
                                st.write(f"**Job ID**: {job.get('id', 'N/A')}")
                    else:
                        st.info("No scheduled jobs found")
                except Exception:
                    pass
            else:
                st.warning(
                    "⚠️ 스케줄러가 실행되지 않고 있습니다. 서버에서 스케줄러 프로세스를 시작해야 합니다.",
                )

        with col_status2:
            st.caption("읽기 전용")
            if st.button("🔄 새로고침", use_container_width=True):
                st.rerun()

    except ImportError:
        st.warning("스케줄러 상태를 확인할 수 없습니다 (psutil 필요)")
    except Exception as e:
        st.error(f"Error loading scheduler status: {e}")


def show_users_section() -> None:
    """모든 사용자와 통계를 표시한다."""
    st.subheader("👥 All Users")

    try:
        # DB에서 모든 사용자 조회
        users = get_all_users_with_stats()

        # 검색 필터
        search = st.text_input("🔍 Search by email or name")

        # 필터링
        if search:
            users = [
                u
                for u in users
                if search.lower() in u["email"].lower() or search.lower() in u.get("name", "").lower()
            ]

        # 테이블 형태로 표시
        st.write(f"**Total: {len(users)} users**")

        if not users:
            st.info("No users found")
            return

        st.markdown("---")

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
                    last_login = user.get("last_login")
                    if last_login:
                        st.write(f"Last login: {last_login[:10]}")
                    else:
                        st.write("Last login: Never")

                st.divider()

    except Exception as e:
        st.error(f"Error loading users: {e}")


def show_articles_section() -> None:
    """아티클 통계와 목록을 표시한다."""
    st.subheader("📚 Articles")

    try:
        api = get_api_client()

        # 통계
        stats = api.get_article_statistics()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Articles", stats.get("total", 0))

        with col2:
            st.write("**By Category**")
            by_category = stats.get("by_category", {})
            if by_category:
                for cat, count in by_category.items():
                    st.write(f"- {cat}: {count}")
            else:
                st.write("No data")

        with col3:
            st.write("**By Source**")
            by_source = stats.get("by_source_type", {})
            if by_source:
                for src, count in by_source.items():
                    st.write(f"- {src}: {count}")
            else:
                st.write("No data")

        st.markdown("---")

        # 최근 아티클 목록
        st.subheader("Recent Articles")

        limit = st.slider("Show articles", 10, 100, 20)
        articles_response = api.get_articles(skip=0, limit=limit)
        articles = articles_response.get("articles", [])

        if not articles:
            st.info("No articles found")
            return

        for article in articles:
            with st.expander(f"📄 {article.get('title', 'Untitled')[:100]}..."):
                st.write(f"**Source**: {article.get('source_type', 'N/A')}")
                st.write(f"**Category**: {article.get('category', 'N/A')}")
                st.write(f"**Importance**: {article.get('importance_score', 0):.2f}")
                st.write(f"**Collected**: {article.get('collected_at', 'N/A')[:10]}")

                if article.get("summary"):
                    st.write(f"**Summary**: {article['summary'][:300]}...")

                if article.get("source_url"):
                    st.write(f"**URL**: {article['source_url']}")

    except Exception as e:
        st.error(f"Error loading articles: {e}")


def show_digests_section() -> None:
    """전체 사용자 다이제스트 히스토리를 표시한다."""
    st.subheader("📧 Digest History")

    try:
        # 전체 다이제스트 조회
        digests = get_all_digests()

        st.write(f"**Total: {len(digests)} digests sent** (최근 100개)")

        if not digests:
            st.info("No digests found")
            return

        st.markdown("---")

        # 테이블
        for digest in digests[:50]:  # 최근 50개만 표시
            with st.expander(f"📧 {digest['user_email']} - {digest['sent_at'][:10]}"):
                st.write(f"**User**: {digest['user_name']} ({digest['user_email']})")
                st.write(f"**User ID**: {digest['user_id']}")
                st.write(f"**Articles**: {len(digest['article_ids'])} articles")
                st.write(f"**Sent**: {digest['sent_at']}")

                if digest.get("email_opened"):
                    opened_at = digest.get("opened_at", "N/A")
                    st.success(f"✅ Opened at {opened_at[:19] if opened_at != 'N/A' else 'N/A'}")
                else:
                    st.info("📭 Not opened yet")

                # 아티클 ID 표시
                if digest["article_ids"]:
                    with st.expander("View Article IDs"):
                        for idx, article_id in enumerate(digest["article_ids"][:10], 1):
                            st.caption(f"{idx}. {article_id}")
                        if len(digest["article_ids"]) > 10:
                            st.caption(f"... and {len(digest['article_ids']) - 10} more")

    except Exception as e:
        st.error(f"Error loading digests: {e}")


if __name__ == "__main__":
    show_admin_page()
