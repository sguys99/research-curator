"""Dashboard page showing recent digests and statistics."""

import streamlit as st

from app.frontend.components.article_card import show_article_list
from app.frontend.components.sidebar import show_page_header, show_stats_cards
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import get_user_id, is_authenticated


def show_dashboard_page():
    """Display dashboard page with recent digests and statistics."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("📊 대시보드", "최근 받은 연구 자료를 확인하세요")

    api = get_api_client()
    user_id = get_user_id()

    # Load statistics
    with st.spinner("데이터를 불러오는 중..."):
        try:
            # Get recent digests
            digests_response = api.get_user_digests(user_id, skip=0, limit=3)
            digests = digests_response.get("digests", [])

            # Get user feedback stats
            feedback_response = api.get_user_feedback(user_id, skip=0, limit=100)
            feedbacks = feedback_response.get("feedbacks", [])

            # Calculate stats
            total_articles = sum(len(d.get("article_ids", [])) for d in digests)
            total_digests = len(digests)
            avg_rating = (
                sum(f.get("rating", 0) for f in feedbacks) / len(feedbacks) if feedbacks else 0.0
            )

        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")
            digests = []
            total_articles = 0
            total_digests = 0
            avg_rating = 0.0

    # Display statistics
    show_stats_cards(
        [
            ("총 아티클", str(total_articles), "📚"),
            ("받은 이메일", str(total_digests), "📧"),
            ("평균 피드백", f"{avg_rating:.1f}", "⭐"),
        ],
    )

    st.markdown("---")

    # Recent digests section
    st.markdown("### 📬 최근 받은 이메일")

    if not digests:
        st.info("아직 받은 이메일이 없습니다. 첫 이메일은 설정하신 시간에 자동으로 발송됩니다.")
    else:
        # Display each digest
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

                # Load articles
                articles = []
                for article_id in article_ids:
                    try:
                        article = api.get_article(article_id)
                        articles.append(article)
                    except Exception:
                        continue

                # Display articles
                if articles:
                    show_article_list(articles, show_similar_button=True)
                else:
                    st.warning("아티클을 불러올 수 없습니다.")

    st.markdown("---")

    # Quick actions
    st.markdown("### ⚡ 빠른 작업")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 테스트 이메일 발송", use_container_width=True):
            with st.spinner("테스트 이메일을 발송하는 중..."):
                try:
                    result = api.send_test_digest(user_id)
                    st.success("✅ 테스트 이메일이 발송되었습니다!")
                    st.json(result)
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")

    with col2:
        if st.button("🔍 검색하기", use_container_width=True):
            # Navigate to search page
            st.session_state["nav_target"] = "search"
            st.rerun()

    with col3:
        if st.button("⚙️ 설정 변경", use_container_width=True):
            # Navigate to settings page
            st.session_state["nav_target"] = "settings"
            st.rerun()


if __name__ == "__main__":
    show_dashboard_page()
