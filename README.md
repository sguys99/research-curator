# AI Research Curator

AI 연구자를 위한 맞춤형 리서치 큐레이션 서비스입니다. LLM과 웹 검색 기술을 활용하여 특정 연구 분야의 트렌드 정보를 주기적으로 수집하고, 한국어로 요약하여 이메일로 전송합니다.

## 주요 기능

- 🤖 **자동 데이터 수집**: arXiv, Google Scholar, TechCrunch 등에서 논문/뉴스/리포트 자동 수집
- 🧠 **LLM 기반 처리**: GPT-4를 활용한 한국어 요약, 중요도 평가, 카테고리 분류
- 🔍 **Vector DB 검색**: Qdrant를 사용한 시맨틱 검색 및 과거 자료 재검색
- 📧 **이메일 큐레이션**: 매일 상위 N개 자료를 HTML 이메일로 전송
- 🎨 **웹 대시보드**: Streamlit 기반 설정 관리 및 검색 인터페이스
- 🔐 **매직 링크 인증**: 비밀번호 없는 간편한 이메일 인증

## 기술 스택

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Vector DB**: Qdrant
- **LLM**: OpenAI GPT-4o via LiteLLM
- **Frontend**: Streamlit
- **Scheduler**: APScheduler
- **Package Manager**: uv

---
