"""최근 다이제스트와 통계를 표시하는 대시보드 페이지."""

import streamlit as st

from app.frontend.components.article_card import show_article_list
from app.frontend.components.sidebar import show_page_header, show_stats_cards
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import get_user_id, is_authenticated


def show_dashboard_page() -> None:
    """최근 다이제스트와 통계를 표시하는 대시보드를 보여준다."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("📊 대시보드", "최근 받은 연구 자료를 확인하세요")

    api = get_api_client()
    user_id = get_user_id()

    # 통계 로드
    with st.spinner("데이터를 불러오는 중..."):
        try:
            # 아티클 통계 조회
            stats_response = api.get_article_statistics()
            total_articles = stats_response.get("total", 0)

            # 최근 다이제스트 조회
            digests_response = api.get_user_digests(user_id, skip=0, limit=3)
            digests = digests_response.get("digests", [])
            total_digests = digests_response.get("total", 0)

            # 사용자 피드백 통계 조회
            feedback_response = api.get_user_feedback(user_id, skip=0, limit=100)
            feedbacks = feedback_response.get("feedback", [])  # 변경: feedbacks → feedback
            avg_rating = (
                sum(f.get("rating", 0) for f in feedbacks) / len(feedbacks) if feedbacks else 0.0
            )

        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")
            digests = []
            total_articles = 0
            total_digests = 0
            avg_rating = 0.0

    # 통계 표시
    show_stats_cards(
        [
            ("총 아티클", str(total_articles), "📚"),
            ("받은 이메일", str(total_digests), "📧"),
            ("평균 피드백", f"{avg_rating:.1f}", "⭐"),
        ],
    )

    st.markdown("---")

    # 최근 다이제스트 섹션
    st.markdown("### 📬 최근 받은 이메일")

    if not digests:
        st.info("아직 받은 이메일이 없습니다. 첫 이메일은 설정하신 시간에 자동으로 발송됩니다.")
    else:
        # 다이제스트별 표시
        for idx, digest in enumerate(digests):
            with st.expander(
                f"📧 다이제스트 {idx + 1} - {digest.get('sent_at', 'N/A')[:10]}",
                expanded=(idx == 0),
            ):
                article_ids = digest.get("article_ids", [])

                if not article_ids:
                    st.info("이 다이제스트에는 아티클이 없습니다.")
                    continue

                st.markdown(f"**포함된 아티클: {len(article_ids)}개**")

                # 배치 API로 아티클 로드
                try:
                    batch_response = api.get_articles_batch(article_ids)
                    articles = batch_response.get("articles", [])

                    # 아티클 표시
                    if articles:
                        show_article_list(articles, show_similar_button=True)
                    else:
                        st.warning("아티클을 불러올 수 없습니다.")
                except Exception as e:
                    st.error(f"아티클 로딩 오류: {str(e)}")

    st.markdown("---")

    # 스케줄러 상태 섹션
    st.markdown("### 🤖 스케줄러 상태")

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
                    scheduler_status = api.get_scheduler_status()
                    jobs = scheduler_status.get("jobs", [])
                    if jobs:
                        with st.expander("📅 예정된 작업 보기"):
                            for job in jobs:
                                next_run = job.get("next_run_time", "N/A")
                                st.markdown(f"- **{job.get('name')}**: {next_run}")
                except Exception:
                    pass
            else:
                st.warning(
                    "⚠️ 스케줄러가 실행되지 않고 있습니다. 서버 관리자에게 문의하세요.",
                )

        with col_status2:
            st.caption("읽기 전용")
            st.button("🔄 새로고침", use_container_width=True, on_click=st.rerun)

    except ImportError:
        st.warning("스케줄러 상태를 확인할 수 없습니다 (psutil 필요)")
    except Exception as e:
        st.error(f"스케줄러 상태를 불러올 수 없습니다: {str(e)}")

    st.markdown("---")

    # 빠른 작업
    st.markdown("### ⚡ 빠른 작업")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📧 이메일 테스트")
        if st.button("테스트 이메일 발송", use_container_width=True, type="primary"):
            with st.spinner("테스트 이메일을 발송하는 중..."):
                try:
                    result = api.send_test_digest(user_id)
                    st.success("✅ 테스트 이메일이 발송되었습니다!")
                    st.info(f"📊 {result.get('article_count', 0)}개의 아티클 전송")
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")

    with col2:
        st.markdown("#### 🔄 수동 실행")
        job_option = st.selectbox(
            "실행할 작업 선택",
            options=[
                ("collect_data", "📚 자료 수집"),
                ("process_articles", "⚙️ 아티클 처리"),
                ("send_digests", "📧 다이제스트 발송"),
            ],
            format_func=lambda x: x[1],
        )

        if st.button("지금 실행", use_container_width=True):
            job_id = job_option[0]
            job_name = job_option[1]

            with st.spinner(f"{job_name} 작업을 실행하는 중..."):
                try:
                    result = api.trigger_job(job_id)
                    if result.get("success"):
                        st.success(f"✅ {job_name} 작업이 완료되었습니다!")
                    else:
                        st.error(f"❌ 실패: {result.get('message')}")
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")

    st.markdown("---")

    # 바로가기
    st.markdown("### 🔗 바로가기")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 검색하기", use_container_width=True):
            st.session_state["nav_target"] = "search"
            st.rerun()

    with col2:
        if st.button("⚙️ 설정 변경", use_container_width=True):
            st.session_state["nav_target"] = "settings"
            st.rerun()


if __name__ == "__main__":
    show_dashboard_page()
