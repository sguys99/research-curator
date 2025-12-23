"""AI Chatbot component for onboarding."""

import streamlit as st

from app.frontend.utils.api_client import get_api_client


class OnboardingChatbot:
    """AI chatbot for collecting user preferences during onboarding."""

    def __init__(self):
        self.api = get_api_client()
        self._init_session_state()

    def _init_session_state(self):
        """Initialize chatbot session state."""
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

    def render(self):
        """Render chatbot UI."""
        st.title("🎯 AI 온보딩")
        st.markdown("AI 챗봇과 대화하며 맞춤형 설정을 완료해보세요!")
        st.markdown("---")

        # Display chat messages
        self._display_messages()

        # Chat input
        self._handle_user_input()

        # Show collected info (for debugging)
        if st.session_state.get("debug_mode", False):
            with st.expander("🔧 수집된 정보 (디버그)"):
                st.json(st.session_state.collected_info)

    def _display_messages(self):
        """Display chat message history."""
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show buttons for multiple choice questions
                if message.get("options"):
                    self._render_options(message["options"])

    def _render_options(self, options: list[str]):
        """Render option buttons for multiple choice."""
        cols = st.columns(min(len(options), 3))
        for idx, option in enumerate(options):
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(option, key=f"option_{idx}_{option}"):
                    self._handle_option_selected(option)

    def _handle_option_selected(self, option: str):
        """Handle option button click."""
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": option})

        # Process the response
        self._process_response(option)

        st.rerun()

    def _handle_user_input(self):
        """Handle user text input."""
        # Show initial message if no messages yet
        if len(st.session_state.chat_messages) == 0:
            self._show_welcome_message()
            return

        # Check if onboarding is complete
        if st.session_state.chat_step >= 6:
            self._show_completion_message()
            return

        # Chat input
        user_input = st.chat_input("메시지를 입력하세요...")

        if user_input:
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            # Process the response
            self._process_response(user_input)

            st.rerun()

    def _show_welcome_message(self):
        """Show initial welcome message."""
        welcome_msg = """
안녕하세요! 👋

저는 Research Curator의 AI 어시스턴트입니다.
몇 가지 질문을 통해 **맞춤형 리서치 큐레이션**을 설정해드리겠습니다.

질문은 **5가지**이며, 각 질문에 답변해주시면 자동으로 설정이 완료됩니다.

준비되셨나요? 😊
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})

        # Add first question
        first_question = (
            "**질문 1/5**: 어떤 연구 분야에 관심이 있으신가요?\n\n"
            "예시: Machine Learning, Natural Language Processing, Computer Vision 등"
        )
        st.session_state.chat_messages.append({"role": "assistant", "content": first_question})

        st.session_state.chat_step = 1
        st.rerun()

    def _process_response(self, user_input: str):
        """Process user response and ask next question."""
        step = st.session_state.chat_step

        if step == 1:
            # Research fields
            self._extract_research_fields(user_input)
            self._ask_keywords()
        elif step == 2:
            # Keywords
            self._extract_keywords(user_input)
            self._ask_info_types()
        elif step == 3:
            # Info types
            self._extract_info_types(user_input)
            self._ask_sources()
        elif step == 4:
            # Sources
            self._extract_sources(user_input)
            self._ask_email_settings()
        elif step == 5:
            # Email settings
            self._extract_email_settings(user_input)
            self._ask_confirmation()
        elif step == 6:
            # Confirmation
            if "확인" in user_input or "네" in user_input or "yes" in user_input.lower():
                st.session_state.chat_step = 7
            else:
                # User wants to modify, go back to start
                st.session_state.chat_step = 1
                self._show_welcome_message()

    def _extract_research_fields(self, text: str):
        """Extract research fields from user input."""
        # Split by comma to preserve multi-word phrases (e.g., "vector db")
        fields = [field.strip() for field in text.split(",") if len(field.strip()) > 2]

        if not fields:
            fields = ["AI", "Machine Learning"]  # Default

        st.session_state.collected_info["research_fields"] = fields[:5]  # Max 5 fields

    def _ask_keywords(self):
        """Ask for keywords."""
        question = f"""
좋아요! **{", ".join(st.session_state.collected_info['research_fields'])}** 분야군요.

**질문 2/5**: 특히 관심있는 **키워드**를 알려주세요.

예시: transformer, GPT, BERT, attention mechanism, transfer learning 등
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": question})
        st.session_state.chat_step = 2

    def _extract_keywords(self, text: str):
        """Extract keywords from user input."""
        # Split by comma to preserve multi-word phrases (e.g., "vector db")
        keywords = [kw.strip() for kw in text.split(",") if len(kw.strip()) > 1]

        if not keywords:
            keywords = ["AI", "research"]

        st.session_state.collected_info["keywords"] = keywords[:10]  # Max 10 keywords

    def _ask_info_types(self):
        """Ask for preferred information types."""
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

    def _extract_info_types(self, text: str):
        """Extract info types from user input."""
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
            # Default balanced
            st.session_state.collected_info["info_types"] = {
                "paper": 0.5,
                "news": 0.3,
                "report": 0.2,
            }

    def _ask_sources(self):
        """Ask for additional sources."""
        question = """
**질문 4/5**: 특별히 포함하고 싶은 웹사이트가 있나요?

예시: techcrunch.com, venturebeat.com 등

없으면 "없음" 또는 "기본"이라고 답변해주세요.
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": question})
        st.session_state.chat_step = 4

    def _extract_sources(self, text: str):
        """Extract sources from user input."""
        if "없음" in text or "기본" in text or "skip" in text.lower():
            st.session_state.collected_info["sources"] = []
        else:
            # Extract URLs or domain names
            sources = [src.strip() for src in text.replace(",", " ").split() if "." in src]
            st.session_state.collected_info["sources"] = sources[:5]  # Max 5 sources

    def _ask_email_settings(self):
        """Ask for email settings."""
        question = """
**질문 5/5**: 이메일 설정을 선택해주세요.
"""
        options = ["🕗 오전 8시 (기본)", "🕐 오후 1시", "🕕 오후 6시", "🕘 오후 9시"]

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": question, "options": options},
        )
        st.session_state.chat_step = 5

    def _extract_email_settings(self, text: str):
        """Extract email settings from user input."""
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

    def _ask_confirmation(self):
        """Ask for confirmation."""
        info = st.session_state.collected_info

        # Format info types percentages
        paper_pct = int(info["info_types"]["paper"] * 100)
        news_pct = int(info["info_types"]["news"] * 100)
        report_pct = int(info["info_types"]["report"] * 100)

        summary = f"""
완벽합니다! 🎉

설정이 완료되었습니다. 확인해주세요:

**연구 분야**: {", ".join(info['research_fields'])}
**키워드**: {", ".join(info['keywords'])}
**정보 유형**: 논문 {paper_pct}%, 뉴스 {news_pct}%, 리포트 {report_pct}%
**이메일 발송 시간**: {info['email_time']}
**일일 제공량**: {info['daily_limit']}개

이대로 저장하시겠습니까?

"확인" 또는 "수정"을 입력해주세요.
"""
        st.session_state.chat_messages.append({"role": "assistant", "content": summary})
        st.session_state.chat_step = 6

    def _show_completion_message(self):
        """Show completion message and save button."""
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

        # Save button
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
        """Save collected preferences to database."""
        try:
            user_id = st.session_state.get("user_id")
            if not user_id:
                st.error("사용자 ID를 찾을 수 없습니다.")
                return False

            preferences = st.session_state.collected_info

            # Prepare API payload
            payload = {
                "research_fields": preferences["research_fields"],
                "keywords": preferences["keywords"],
                "sources": preferences["sources"],
                "info_types": preferences["info_types"],
                "email_time": preferences["email_time"],
                "daily_limit": preferences["daily_limit"],
                "email_enabled": True,
            }

            # Call API
            self.api.update_user_preferences(user_id, payload)

            return True

        except Exception as e:
            st.error(f"오류: {str(e)}")
            return False


def show_onboarding_chatbot():
    """Show onboarding chatbot UI."""
    chatbot = OnboardingChatbot()
    chatbot.render()
