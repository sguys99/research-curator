"""온보딩용 AI 챗봇 컴포넌트."""

import streamlit as st

from app.frontend.utils.api_client import get_api_client


class OnboardingChatbot:
    """온보딩 중 사용자 선호도 수집을 위한 AI 챗봇."""

    def __init__(self) -> None:
        self.api = get_api_client()
        self._init_session_state()

    def _init_session_state(self) -> None:
        """챗봇 세션 상태를 초기화한다."""
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        if "chat_step" not in st.session_state:
            st.session_state.chat_step = 0

        if "collected_info" not in st.session_state:
            st.session_state.collected_info = {
                "research_fields": [],
                "keywords": [],
                "info_types": {"paper": 0.5, "news": 0.3, "report": 0.2},
                "sources": [],
                "email_time": "08:00",
                "daily_limit": 5,
            }

    def render(self) -> None:
        """챗봇 UI를 렌더링한다."""
        st.title("🎯 AI 온보딩")
        st.markdown("AI 챗봇과 대화하며 맞춤형 설정을 완료해보세요!")
        st.markdown("---")

        # 채팅 메시지 표시
        self._display_messages()

        # 채팅 입력
        self._handle_user_input()

        # 수집 정보 표시(디버그용)
        if st.session_state.get("debug_mode", False):
            with st.expander("🔧 수집된 정보 (디버그)"):
                st.json(st.session_state.collected_info)

    def _display_messages(self) -> None:
        """채팅 메시지 히스토리를 표시한다."""
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 객관식 질문 옵션 버튼 표시
                if message.get("options"):
                    self._render_options(message["options"])

    def _render_options(self, options: list[str]) -> None:
        """객관식 옵션 버튼을 렌더링한다."""
        cols = st.columns(min(len(options), 3))
        for idx, option in enumerate(options):
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(option, key=f"option_{idx}_{option}"):
                    self._handle_option_selected(option)

    def _handle_option_selected(self, option: str) -> None:
        """옵션 버튼 클릭을 처리한다."""
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": option})

        # 응답 처리
        self._process_response(option)

        st.rerun()

    def _handle_user_input(self) -> None:
        """사용자 텍스트 입력을 처리한다."""
        # 메시지가 없으면 초기 메시지 표시
        if len(st.session_state.chat_messages) == 0:
            self._show_welcome_message()
            return

        # 온보딩 완료 여부 확인
        if st.session_state.chat_step >= 6:
            self._show_completion_message()
            return

        # 채팅 입력
        user_input = st.chat_input("메시지를 입력하세요...")

        if user_input:
            # 사용자 메시지 추가
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            # 응답 처리
            self._process_response(user_input)

            st.rerun()

    def _show_welcome_message(self) -> None:
        """초기 स्वागत 메시지를 표시한다."""
        welcome_msg = """
안녕하세요! 👋

저는 Research Curator의 AI 어시스턴트입니다.
몇 가지 질문을 통해 **맞춤형 리서치 큐레이션**을 설정해드리겠습니다.

질문은 **5가지**이며, 각 질문에 답변해주시면 자동으로 설정이 완료됩니다.

준비되셨나요? 😊
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})

        # 첫 번째 질문 추가
        first_question = (
            "**질문 1/5**: 어떤 연구 분야에 관심이 있으신가요?\n\n"
            "예시: Machine Learning, Natural Language Processing, Computer Vision 등"
        )
        st.session_state.chat_messages.append({"role": "assistant", "content": first_question})

        st.session_state.chat_step = 1
        st.rerun()

    def _process_response(self, user_input: str) -> None:
        """사용자 응답을 처리하고 다음 질문을 한다."""
        step = st.session_state.chat_step

        if step == 1:
            # 연구 분야
            self._extract_research_fields(user_input)
            self._ask_keywords()
        elif step == 2:
            # 키워드
            self._extract_keywords(user_input)
            self._ask_info_types()
        elif step == 3:
            # 정보 유형
            self._extract_info_types(user_input)
            self._ask_sources()
        elif step == 4:
            # 소스
            self._extract_sources(user_input)
            self._ask_email_settings()
        elif step == 5:
            # 이메일 설정
            self._extract_email_settings(user_input)
            self._ask_confirmation()
        elif step == 6:
            # 확인
            if "확인" in user_input or "네" in user_input or "yes" in user_input.lower():
                st.session_state.chat_step = 7
            else:
                # 수정 요청 시 처음으로 되돌리기
                st.session_state.chat_step = 1
                self._show_welcome_message()

    def _extract_research_fields(self, text: str) -> None:
        """사용자 입력에서 연구 분야를 추출한다."""
        # 쉼표로 분리해 다중 단어 구 유지(예: "vector db")
        fields = [field.strip() for field in text.split(",") if len(field.strip()) > 2]

        if not fields:
            fields = ["AI", "Machine Learning"]  # 기본값

        st.session_state.collected_info["research_fields"] = fields[:5]  # 최대 5개

    def _ask_keywords(self) -> None:
        """키워드를 질문한다."""
        question = f"""
좋아요! **{", ".join(st.session_state.collected_info["research_fields"])}** 분야군요.

**질문 2/5**: 특히 관심있는 **키워드**를 알려주세요.

예시: transformer, GPT, BERT, attention mechanism, transfer learning 등
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": question})
        st.session_state.chat_step = 2

    def _extract_keywords(self, text: str) -> None:
        """사용자 입력에서 키워드를 추출한다."""
        # 쉼표로 분리해 다중 단어 구 유지(예: "vector db")
        keywords = [kw.strip() for kw in text.split(",") if len(kw.strip()) > 1]

        if not keywords:
            keywords = ["AI", "research"]

        st.session_state.collected_info["keywords"] = keywords[:10]  # 최대 10개

    def _ask_info_types(self) -> None:
        """선호 정보 유형을 질문한다."""
        question = """
**질문 3/5**: 어떤 유형의 정보를 받고 싶으신가요?

다음 중 선택해주세요:
"""
        options = [
            "📚 논문 위주 (70%)",
            "📰 뉴스 위주 (70%)",
            "📊 리포트 위주 (70%)",
            "⚖️ 균형있게 (논문 50%, 뉴스 30%, 리포트 20%)",
        ]

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": question, "options": options},
        )
        st.session_state.chat_step = 3

    def _extract_info_types(self, text: str) -> None:
        """사용자 입력에서 정보 유형을 추출한다."""
        if "논문" in text or "paper" in text.lower():
            st.session_state.collected_info["info_types"] = {
                "paper": 0.7,
                "news": 0.2,
                "report": 0.1,
            }
        elif "뉴스" in text or "news" in text.lower():
            st.session_state.collected_info["info_types"] = {
                "paper": 0.2,
                "news": 0.7,
                "report": 0.1,
            }
        elif "리포트" in text or "report" in text.lower():
            st.session_state.collected_info["info_types"] = {
                "paper": 0.2,
                "news": 0.1,
                "report": 0.7,
            }
        else:
            # 기본 균형
            st.session_state.collected_info["info_types"] = {
                "paper": 0.5,
                "news": 0.3,
                "report": 0.2,
            }

    def _ask_sources(self) -> None:
        """추가 소스를 질문한다."""
        question = """
**질문 4/5**: 특별히 포함하고 싶은 웹사이트가 있나요?

예시: techcrunch.com, venturebeat.com 등

없으면 "없음" 또는 "기본"이라고 답변해주세요.
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": question})
        st.session_state.chat_step = 4

    def _extract_sources(self, text: str) -> None:
        """사용자 입력에서 소스를 추출한다."""
        if "없음" in text or "기본" in text or "skip" in text.lower():
            st.session_state.collected_info["sources"] = []
        else:
            # URL 또는 도메인 추출
            sources = [src.strip() for src in text.replace(",", " ").split() if "." in src]
            st.session_state.collected_info["sources"] = sources[:5]  # 최대 5개

    def _ask_email_settings(self) -> None:
        """이메일 설정을 질문한다."""
        question = """
**질문 5/5**: 이메일 설정을 선택해주세요.
"""
        options = ["🕗 오전 8시 (기본)", "🕐 오후 1시", "🕕 오후 6시", "🕘 오후 9시"]

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": question, "options": options},
        )
        st.session_state.chat_step = 5

    def _extract_email_settings(self, text: str) -> None:
        """사용자 입력에서 이메일 설정을 추출한다."""
        time_map = {
            "오전 8시": "08:00",
            "오후 1시": "13:00",
            "오후 6시": "18:00",
            "오후 9시": "21:00",
        }

        for key, value in time_map.items():
            if key in text:
                st.session_state.collected_info["email_time"] = value
                break

    def _ask_confirmation(self) -> None:
        """최종 확인을 요청한다."""
        info = st.session_state.collected_info

        # 정보 유형 퍼센트 구성
        paper_pct = int(info["info_types"]["paper"] * 100)
        news_pct = int(info["info_types"]["news"] * 100)
        report_pct = int(info["info_types"]["report"] * 100)

        summary = f"""
완벽합니다! 🎉

설정이 완료되었습니다. 확인해주세요:

**연구 분야**: {", ".join(info["research_fields"])}
**키워드**: {", ".join(info["keywords"])}
**정보 유형**: 논문 {paper_pct}%, 뉴스 {news_pct}%, 리포트 {report_pct}%
**이메일 발송 시간**: {info["email_time"]}
**일일 제공량**: {info["daily_limit"]}개

이대로 저장하시겠습니까?

"확인" 또는 "수정"을 입력해주세요.
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": summary})
        st.session_state.chat_step = 6

    def _show_completion_message(self) -> None:
        """완료 메시지와 저장 버튼을 표시한다."""
        if (
            len(st.session_state.chat_messages) > 0
            and st.session_state.chat_messages[-1].get("role") != "system"
        ):
            completion_msg = """
✅ **설정이 저장되었습니다!**

이제 매일 선택하신 시간에 맞춤형 리서치 자료를 이메일로 받으실 수 있습니다.

대시보드로 이동하시려면 아래 버튼을 클릭해주세요.
"""
            st.session_state.chat_messages.append({"role": "system", "content": completion_msg})

        # 저장 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ 설정 저장 및 대시보드로 이동", type="primary", use_container_width=True):
                if self._save_preferences():
                    from app.frontend.utils.session import mark_onboarding_completed

                    mark_onboarding_completed()
                    st.success("설정이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("설정 저장 중 오류가 발생했습니다.")

    def _save_preferences(self) -> bool:
        """수집된 선호도를 DB에 저장한다."""
        try:
            user_id = st.session_state.get("user_id")
            if not user_id:
                st.error("사용자 ID를 찾을 수 없습니다.")
                return False

            preferences = st.session_state.collected_info

            # API 페이로드 구성
            payload = {
                "research_fields": preferences["research_fields"],
                "keywords": preferences["keywords"],
                "sources": preferences["sources"],
                "info_types": preferences["info_types"],
                "email_time": preferences["email_time"],
                "daily_limit": preferences["daily_limit"],
                "email_enabled": True,
            }

            # API 호출
            self.api.update_user_preferences(user_id, payload)

            return True

        except Exception as e:
            st.error(f"오류: {str(e)}")
            return False


def show_onboarding_chatbot() -> None:
    """온보딩 챗봇 UI를 표시한다."""
    chatbot = OnboardingChatbot()
    chatbot.render()
