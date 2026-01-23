"""아티클 평점/코멘트를 남기는 피드백 페이지."""

import streamlit as st

from app.frontend.components.sidebar import show_page_header
from app.frontend.utils.api_client import APIClient, get_api_client
from app.frontend.utils.session import get_user_id, is_authenticated


def show_feedback_page() -> None:
    """아티클 평점/코멘트 제출 화면을 표시한다."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("💬 피드백", "받은 아티클을 평가해주세요")

    api = get_api_client()
    user_id = get_user_id()

    # 탭 선택
    tab1, tab2, tab3 = st.tabs(["📝 피드백 제출", "📊 피드백 이력", "📈 아티클 통계"])

    with tab1:
        _show_feedback_submission(api, user_id)

    with tab2:
        _show_feedback_history(api, user_id)

    with tab3:
        _show_article_stats(api)


def _show_feedback_submission(api: APIClient, user_id: str) -> None:
    """피드백 제출 폼을 표시한다."""
    st.markdown("### 📝 아티클 피드백 제출")

    st.markdown(
        """
        받으신 아티클에 대해 피드백을 남겨주세요.
        여러분의 의견은 추천 알고리즘을 개선하는 데 활용됩니다.
        """,
    )

    st.markdown("---")

    # 방법 선택
    method = st.radio(
        "피드백 방법 선택",
        ["최근 다이제스트에서 선택", "아티클 ID 직접 입력"],
        horizontal=True,
    )

    article_id = None

    if method == "최근 다이제스트에서 선택":
        # 최근 다이제스트 로드
        with st.spinner("최근 다이제스트를 불러오는 중..."):
            try:
                digests_response = api.get_user_digests(user_id, skip=0, limit=5)
                digests = digests_response.get("digests", [])

                if not digests:
                    st.info("아직 받은 다이제스트가 없습니다.")
                    return

                # 다이제스트 선택
                digest_options = [
                    f"다이제스트 {idx + 1} - {d.get('sent_at', 'N/A')[:10]}"
                    for idx, d in enumerate(digests)
                ]

                selected_digest_idx = st.selectbox(
                    "다이제스트 선택",
                    range(len(digest_options)),
                    format_func=lambda x: digest_options[x],
                )

                selected_digest = digests[selected_digest_idx]
                article_ids = selected_digest.get("article_ids", [])

                if not article_ids:
                    st.info("이 다이제스트에는 아티클이 없습니다.")
                    return

                # 배치 API로 아티클 로드
                try:
                    batch_response = api.get_articles_batch(article_ids)
                    articles = batch_response.get("articles", [])

                    if not articles:
                        st.warning("아티클을 불러올 수 없습니다.")
                        return
                except Exception as e:
                    st.error(f"아티클 로딩 오류: {str(e)}")
                    return

                # 아티클 선택
                article_options = [
                    f"{a.get('title', '제목 없음')[:50]}..."
                    if len(a.get("title", "")) > 50
                    else a.get("title", "제목 없음")
                    for a in articles
                ]

                selected_article_idx = st.selectbox(
                    "아티클 선택",
                    range(len(article_options)),
                    format_func=lambda x: article_options[x],
                )

                selected_article = articles[selected_article_idx]
                article_id = selected_article.get("id")

                # 아티클 미리보기 표시
                with st.expander("📄 선택한 아티클 미리보기"):
                    st.markdown(f"**제목**: {selected_article.get('title', 'N/A')}")
                    st.markdown(f"**요약**: {selected_article.get('summary', 'N/A')}")
                    st.markdown(f"**출처**: {selected_article.get('source_url', 'N/A')}")

            except Exception as e:
                st.error(f"다이제스트를 불러오는 중 오류가 발생했습니다: {str(e)}")
                return

    else:
        # 아티클 ID 직접 입력
        article_id_input = st.text_input(
            "아티클 ID",
            placeholder="예: 123e4567-e89b-12d3-a456-426614174000",
            help="아티클 ID는 이메일이나 대시보드에서 확인할 수 있습니다.",
        )

        if article_id_input:
            article_id = article_id_input.strip()

            # ID 검증을 위해 아티클 조회
            try:
                article = api.get_article(article_id)

                with st.expander("📄 아티클 미리보기"):
                    st.markdown(f"**제목**: {article.get('title', 'N/A')}")
                    st.markdown(f"**요약**: {article.get('summary', 'N/A')}")
                    st.markdown(f"**출처**: {article.get('source_url', 'N/A')}")

            except Exception as e:
                st.error(f"아티클을 찾을 수 없습니다: {str(e)}")
                article_id = None

    # 피드백 폼
    if article_id:
        st.markdown("---")
        st.markdown("### ⭐ 평가")

        col1, col2 = st.columns([1, 2])

        with col1:
            rating = st.select_slider(
                "평점 (1-5)",
                options=[1, 2, 3, 4, 5],
                value=3,
                help="1: 전혀 유용하지 않음, 5: 매우 유용함",
            )

        with col2:
            # 평점 시각화 표시
            star_display = "⭐" * rating + "☆" * (5 - rating)
            st.markdown(f"### {star_display}")

        st.markdown("### 💭 코멘트 (선택사항)")

        comment = st.text_area(
            "피드백 내용",
            placeholder="이 아티클에 대한 의견을 자유롭게 남겨주세요.",
            height=100,
            max_chars=500,
        )

        st.caption(f"{len(comment)}/500 자")

        st.markdown("---")

        # 제출 버튼
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            if st.button("📤 피드백 제출", type="primary", use_container_width=True):
                with st.spinner("피드백을 제출하는 중..."):
                    try:
                        result = api.create_feedback(
                            article_id=article_id,
                            rating=rating,
                            comment=comment if comment else None,
                        )

                        st.success("✅ 피드백이 제출되었습니다!")
                        st.balloons()

                        # 결과 표시
                        with st.expander("제출된 피드백 확인"):
                            st.json(result)

                    except Exception as e:
                        st.error(f"❌ 피드백 제출 중 오류가 발생했습니다: {str(e)}")


def _show_feedback_history(api: APIClient, user_id: str) -> None:
    """피드백 이력을 표시한다."""
    st.markdown("### 📊 피드백 이력")

    # 피드백 이력 로드
    with st.spinner("피드백 이력을 불러오는 중..."):
        try:
            feedback_response = api.get_user_feedback(user_id, skip=0, limit=50)
            feedbacks = feedback_response.get("feedback", [])

            if not feedbacks:
                st.info("아직 제출한 피드백이 없습니다.")
                return

            # 통계
            st.markdown("#### 📈 통계")

            col1, col2, col3 = st.columns(3)

            total_feedbacks = len(feedbacks)
            avg_rating = sum(f.get("rating", 0) for f in feedbacks) / total_feedbacks
            rating_counts = {}
            for f in feedbacks:
                r = f.get("rating", 0)
                rating_counts[r] = rating_counts.get(r, 0) + 1

            with col1:
                st.metric("총 피드백 수", total_feedbacks)

            with col2:
                st.metric("평균 평점", f"{avg_rating:.1f} ⭐")

            with col3:
                most_common_rating = max(rating_counts, key=rating_counts.get)
                st.metric("최다 평점", f"{most_common_rating} ⭐")

            st.markdown("---")

            # 평점 분포
            st.markdown("#### 📊 평점 분포")

            rating_dist_cols = st.columns(5)
            for i in range(1, 6):
                count = rating_counts.get(i, 0)
                pct = (count / total_feedbacks * 100) if total_feedbacks > 0 else 0
                with rating_dist_cols[i - 1]:
                    st.metric(f"{i}⭐", f"{count}개", f"{pct:.0f}%")

            st.markdown("---")

            # 피드백 목록
            st.markdown("#### 📝 피드백 목록")

            # 필터 옵션
            col1, col2 = st.columns(2)

            with col1:
                filter_rating = st.multiselect(
                    "평점 필터",
                    [1, 2, 3, 4, 5],
                    default=[1, 2, 3, 4, 5],
                    format_func=lambda x: f"{x}⭐",
                )

            with col2:
                sort_order = st.selectbox(
                    "정렬",
                    ["최신순", "평점 높은 순", "평점 낮은 순"],
                )

            # 피드백 필터링
            filtered_feedbacks = [f for f in feedbacks if f.get("rating") in filter_rating]

            # 피드백 정렬
            if sort_order == "평점 높은 순":
                filtered_feedbacks = sorted(
                    filtered_feedbacks,
                    key=lambda x: x.get("rating", 0),
                    reverse=True,
                )
            elif sort_order == "평점 낮은 순":
                filtered_feedbacks = sorted(filtered_feedbacks, key=lambda x: x.get("rating", 0))
            else:
                # API에서 최신순으로 이미 정렬됨
                pass

            if not filtered_feedbacks:
                st.info("필터 조건에 맞는 피드백이 없습니다.")
                return

            st.caption(f"{len(filtered_feedbacks)}개의 피드백")

            # 피드백 표시
            for idx, feedback in enumerate(filtered_feedbacks):
                with st.expander(
                    f"{'⭐' * feedback.get('rating', 0)} - " f"{feedback.get('created_at', 'N/A')[:10]}",
                    expanded=(idx < 3),
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**아티클 ID**: `{feedback.get('article_id', 'N/A')}`")
                        st.markdown(f"**평점**: {'⭐' * feedback.get('rating', 0)}")

                        if feedback.get("comment"):
                            st.markdown(f"**코멘트**: {feedback.get('comment')}")
                        else:
                            st.caption("(코멘트 없음)")

                    with col2:
                        st.caption(f"제출일: {feedback.get('created_at', 'N/A')[:10]}")
                        st.caption(f"피드백 ID: `{str(feedback.get('id', 'N/A'))[:8]}...`")

                        # 액션 버튼
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

                    # 수정 모드
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
                            if st.button(
                                "❌ 취소",
                                key=f"cancel_{idx}",
                                use_container_width=True,
                            ):
                                st.session_state.pop(f"edit_feedback_{feedback.get('id')}")
                                st.rerun()

        except Exception as e:
            st.error(f"피드백 이력을 불러오는 중 오류가 발생했습니다: {str(e)}")

    # 도움말 섹션
    st.markdown("---")
    st.markdown("### 💡 도움말")

    with st.expander("피드백 가이드"):
        st.markdown(
            """
            **피드백 제출**
            - 최근 받은 다이제스트에서 아티클을 선택하거나
            - 아티클 ID를 직접 입력하여 피드백 제출

            **평점 기준**
            - 1⭐: 전혀 유용하지 않음
            - 2⭐: 별로 유용하지 않음
            - 3⭐: 보통
            - 4⭐: 유용함
            - 5⭐: 매우 유용함

            **코멘트**
            - 아티클이 유용했던 이유
            - 개선이 필요한 부분
            - 원하는 추가 정보 등

            **피드백 활용**
            - 추천 알고리즘 개선
            - 중요도 평가 정확도 향상
            - 개인화 큐레이션 강화
            """,
        )


def _show_article_stats(api: APIClient) -> None:
    """아티클 피드백 통계를 표시한다."""
    st.markdown("### 📈 아티클 피드백 통계")

    st.markdown(
        """
        특정 아티클에 대한 전체 사용자의 피드백 통계를 확인할 수 있습니다.
        """,
    )

    st.markdown("---")

    # 아티클 ID 입력
    article_id = st.text_input(
        "아티클 ID 입력",
        placeholder="예: 123e4567-e89b-12d3-a456-426614174000",
        help="통계를 확인하고 싶은 아티클의 ID를 입력하세요.",
    )

    if not article_id:
        st.info("아티클 ID를 입력하여 통계를 조회하세요.")
        return

    # 아티클 정보 로드
    col1, col2 = st.columns([2, 1])

    with col1:
        with st.spinner("아티클 정보를 불러오는 중..."):
            try:
                article = api.get_article(article_id)

                st.markdown("#### 📄 아티클 정보")
                st.markdown(f"**제목**: {article.get('title', 'N/A')}")
                st.markdown(f"**요약**: {article.get('summary', 'N/A')[:200]}...")
                st.markdown(f"**출처**: {article.get('source_type', 'N/A')}")
                st.markdown(f"**카테고리**: {article.get('category', 'N/A')}")

            except Exception as e:
                st.error(f"아티클을 찾을 수 없습니다: {str(e)}")
                return

    with col2:
        if article.get("source_url"):
            st.markdown("#### 🔗 링크")
            st.link_button("원문 보기", article.get("source_url"))

    st.markdown("---")

    # 피드백 통계 로드
    with st.spinner("피드백 통계를 불러오는 중..."):
        try:
            stats = api.get_article_feedback_stats(article_id)

            st.markdown("#### 📊 피드백 통계")

            # 요약 지표
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
                else:
                    st.metric("최다 평점", "N/A")

            st.markdown("---")

            # 평점 분포
            st.markdown("#### ⭐ 평점 분포")

            rating_dist = stats.get("rating_distribution", {})
            total = stats.get("count", 0)

            if total > 0:
                dist_cols = st.columns(5)
                for i in range(1, 6):
                    count = rating_dist.get(str(i), 0)  # API는 문자열 키 반환
                    pct = (count / total * 100) if total > 0 else 0

                    with dist_cols[i - 1]:
                        st.metric(f"{i}⭐", f"{count}개", f"{pct:.1f}%")

                # 시각적 막대 차트
                st.markdown("---")
                st.markdown("**분포 차트**")

                for i in range(5, 0, -1):  # 5 to 1
                    count = rating_dist.get(str(i), 0)
                    pct = (count / total * 100) if total > 0 else 0
                    bar_length = int(pct / 2)  # 최대 50자 기준 스케일
                    bar = "█" * bar_length
                    st.text(f"{i}⭐ │{bar} {pct:.1f}% ({count}개)")

            else:
                st.info("아직 이 아티클에 대한 피드백이 없습니다.")

            st.markdown("---")

            # 해당 아티클의 최근 피드백 로드
            st.markdown("#### 💬 최근 피드백")

            try:
                feedback_response = api.get_article_feedback(article_id, skip=0, limit=10)
                feedbacks = feedback_response.get("feedback", [])

                if feedbacks:
                    st.caption(f"최근 {len(feedbacks)}개의 피드백")

                    for idx, fb in enumerate(feedbacks):
                        with st.expander(
                            f"{'⭐' * fb.get('rating', 0)} - {fb.get('created_at', 'N/A')[:10]}",
                            expanded=(idx < 3),
                        ):
                            st.markdown(f"**평점**: {'⭐' * fb.get('rating', 0)}")

                            if fb.get("comment"):
                                st.markdown(f"**코멘트**: {fb.get('comment')}")
                            else:
                                st.caption("(코멘트 없음)")

                            st.caption(f"사용자 ID: `{str(fb.get('user_id', 'N/A'))[:8]}...`")
                else:
                    st.info("최근 피드백이 없습니다.")

            except Exception as e:
                st.warning(f"최근 피드백을 불러올 수 없습니다: {str(e)}")

        except Exception as e:
            st.error(f"통계를 불러오는 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    show_feedback_page()
