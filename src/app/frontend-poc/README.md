# Research Curator Frontend

Streamlit 기반 웹 대시보드

## 🚀 실행 방법

### 1. FastAPI 백엔드 시작

```bash
# 터미널 1
cd /Users/sguys99/Desktop/project/research-curator
source .venv/bin/activate
uvicorn src.app.api.main:app --reload
```

### 2. Streamlit 프론트엔드 시작

```bash
# 터미널 2
cd /Users/sguys99/Desktop/project/research-curator
source .venv/bin/activate
streamlit run src/app/frontend/main.py
```

### 3. 브라우저 접속

```
http://localhost:8501
```

---

## 📁 프로젝트 구조

```
src/app/frontend/
├── main.py                    # Streamlit 앱 진입점
├── pages/                     # 각 페이지 모듈
│   ├── 0_onboarding.py        # 온보딩 (Checkpoint 2)
│   ├── 1_dashboard.py         # 대시보드 (Checkpoint 3)
│   ├── 2_search.py            # 검색 (Checkpoint 3)
│   ├── 3_settings.py          # 설정 (Checkpoint 3)
│   └── 4_feedback.py          # 피드백 (Checkpoint 4)
├── components/
│   ├── auth.py                # 인증 컴포넌트
│   ├── sidebar.py             # 사이드바
│   ├── article_card.py        # 아티클 카드
│   └── chatbot.py             # 챗봇
└── utils/
    ├── api_client.py          # FastAPI 클라이언트
    └── session.py             # 세션 관리
```

---

## 🎯 페이지

- **로그인**: 매직 링크 인증
- **온보딩**: AI 챗봇과 대화하며 초기 설정
- **대시보드**: 최근 받은 이메일 확인
- **검색**: 과거 자료 시맨틱 검색
- **설정**: 키워드, 소스, 발송 시간 변경
- **피드백**: 받은 아티클 평가

---

## 🔑 인증

### 매직 링크 플로우

1. 이메일 입력
2. 매직 링크 발송
3. 이메일에서 링크 클릭
4. 자동 로그인

### 개발용 토큰 로그인

개발 환경에서는 토큰을 직접 입력하여 로그인할 수 있습니다.

---

## ⚙️ 설정

### `.streamlit/config.toml`

Streamlit 기본 설정 (테마, 서버 등)

### `.streamlit/secrets.toml`

시크릿 정보 (gitignored)

```toml
environment = "development"
api_base_url = "http://localhost:8000"
```

---

## 🧪 테스트

```bash
# 테스트 노트북 실행
jupyter notebook notebooks/08.test_day8_checkpoint1.ipynb
```

---

## 📝 개발 상태

### ✅ Checkpoint 1: 기본 구조 & 인증 (완료)
- Streamlit 프로젝트 구조
- 세션 관리
- FastAPI 클라이언트
- 인증 시스템
- 사이드바

### ⏳ Checkpoint 2: AI 챗봇 온보딩 (예정)
### ⏳ Checkpoint 3: 대시보드, 검색, 설정 (예정)
### ⏳ Checkpoint 4: 피드백 & 통합 테스트 (예정)

---

**Last Updated**: 2025-12-04
