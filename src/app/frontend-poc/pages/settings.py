"""사용자 선호도를 관리하는 설정 페이지."""

import streamlit as st

from app.frontend.components.sidebar import show_page_header
from app.frontend.utils.api_client import get_api_client
from app.frontend.utils.session import get_user_id, is_authenticated


def show_settings_page() -> None:
    """선호도 관리 설정 페이지를 표시한다."""
    if not is_authenticated():
        st.warning("⚠️ 로그인이 필요합니다.")
        st.stop()

    show_page_header("⚙️ 설정", "연구 분야, 키워드, 발송 시간 등을 변경하세요")

    api = get_api_client()
    user_id = get_user_id()

    # 현재 선호도 로드
    with st.spinner("설정을 불러오는 중..."):
        try:
            preferences = api.get_user_preferences(user_id)
        except Exception as e:
            st.error(f"설정을 불러오는 중 오류가 발생했습니다: {str(e)}")
            preferences = {}

    # 설정 폼
    with st.form("settings_form"):
        st.markdown("### 📚 연구 분야 및 키워드")

        col1, col2 = st.columns(2)

        with col1:
            research_fields_input = st.text_area(
                "연구 분야",
                value=", ".join(preferences.get("research_fields", [])),
                placeholder="예: Machine Learning, NLP, Computer Vision",
                help="쉼표(,)로 구분하여 입력하세요",
                height=100,
            )

        with col2:
            keywords_input = st.text_area(
                "관심 키워드",
                value=", ".join(preferences.get("keywords", [])),
                placeholder="예: transformer, GPT, BERT, attention",
                help="쉼표(,)로 구분하여 입력하세요",
                height=100,
            )

        st.markdown("---")
        st.markdown("### 📰 정보 유형 비율")

        st.caption("각 유형의 비율을 설정하세요. 합계가 100%가 되도록 조정됩니다.")

        col1, col2, col3 = st.columns(3)

        current_info_types = preferences.get("info_types", {})

        with col1:
            paper_ratio = st.slider(
                "📚 논문",
                0,
                100,
                int(current_info_types.get("paper", 0.5) * 100),
                5,
                help="학술 논문 비율",
            )

        with col2:
            news_ratio = st.slider(
                "📰 뉴스",
                0,
                100,
                int(current_info_types.get("news", 0.3) * 100),
                5,
                help="기술 뉴스 비율",
            )

        with col3:
            report_ratio = st.slider(
                "📊 리포트",
                0,
                100,
                int(current_info_types.get("report", 0.2) * 100),
                5,
                help="연구 리포트 비율",
            )

        # 합계 퍼센트 표시
        total_pct = paper_ratio + news_ratio + report_ratio
        if total_pct != 100:
            st.warning(f"⚠️ 현재 합계: {total_pct}%. 저장 시 자동으로 100%로 정규화됩니다.")
        else:
            st.success(f"✅ 합계: {total_pct}%")

        st.markdown("---")
        st.markdown("### 🌐 추가 소스")

        sources_input = st.text_area(
            "웹사이트 URL",
            value=", ".join(preferences.get("sources", [])),
            placeholder="예: techcrunch.com, venturebeat.com",
            help="쉼표(,)로 구분하여 입력하세요. 비워두면 기본 소스만 사용합니다.",
            height=80,
        )

        st.markdown("---")
        st.markdown("### 📧 이메일 설정")

        col1, col2, col3 = st.columns(3)

        with col1:
            email_time = st.selectbox(
                "발송 시간",
                ["08:00", "09:00", "10:00", "13:00", "18:00", "21:00"],
                index=["08:00", "09:00", "10:00", "13:00", "18:00", "21:00"].index(
                    preferences.get("email_time", "08:00"),
                ),
                help="매일 이메일을 받을 시간",
            )

        with col2:
            daily_limit = st.number_input(
                "일일 아티클 수",
                min_value=1,
                max_value=20,
                value=preferences.get("daily_limit", 5),
                help="하루에 받을 최대 아티클 수",
            )

        with col3:
            email_enabled = st.checkbox(
                "이메일 수신",
                value=preferences.get("email_enabled", True),
                help="이메일 수신 여부",
            )

        st.markdown("---")

        # 제출 버튼
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            submit_button = st.form_submit_button(
                "💾 설정 저장",
                type="primary",
                use_container_width=True,
            )

    # 폼 제출 처리
    if submit_button:
        with st.spinner("설정을 저장하는 중..."):
            try:
                # 입력 파싱
                research_fields = [
                    field.strip() for field in research_fields_input.split(",") if field.strip()
                ]
                keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
                sources = [src.strip() for src in sources_input.split(",") if src.strip()]

                # info_types 합계가 1.0이 되도록 정규화
                total = paper_ratio + news_ratio + report_ratio
                if total > 0:
                    info_types = {
                        "paper": paper_ratio / total,
                        "news": news_ratio / total,
                        "report": report_ratio / total,
                    }
                else:
                    info_types = {"paper": 0.5, "news": 0.3, "report": 0.2}

                # 페이로드 구성
                payload = {
                    "research_fields": research_fields,
                    "keywords": keywords,
                    "sources": sources,
                    "info_types": info_types,
                    "email_time": email_time,
                    "daily_limit": daily_limit,
                    "email_enabled": email_enabled,
                }

                # 선호도 저장
                api.update_user_preferences(user_id, payload)

                st.success("✅ 설정이 저장되었습니다!")

                # 선호도 재로드를 위해 리런
                st.rerun()

            except Exception as e:
                st.error(f"❌ 설정 저장 중 오류가 발생했습니다: {str(e)}")

    # 도움말 섹션
    st.markdown("---")
    st.markdown("### 💡 도움말")

    with st.expander("설정 가이드"):
        st.markdown(
            """
            **연구 분야 및 키워드**
            - 관심있는 연구 분야와 키워드를 입력하세요
            - 여러 항목은 쉼표(,)로 구분합니다
            - 예: "Machine Learning, Deep Learning"

            **정보 유형 비율**
            - 논문, 뉴스, 리포트의 비율을 설정합니다
            - 합계가 100%가 되도록 자동 정규화됩니다
            - 예: 논문 70%, 뉴스 20%, 리포트 10%

            **추가 소스**
            - 특정 웹사이트를 추가로 모니터링할 수 있습니다
            - 도메인 형식으로 입력하세요
            - 예: "techcrunch.com, venturebeat.com"

            **이메일 설정**
            - 매일 받을 시간과 아티클 수를 설정합니다
            - 이메일 수신을 일시적으로 중단할 수도 있습니다
            """,
        )

    # 현재 설정 요약 표시
    with st.expander("현재 설정 요약"):
        st.json(preferences)


if __name__ == "__main__":
    show_settings_page()
