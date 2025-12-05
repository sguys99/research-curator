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

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.12.9
- Docker & Docker Compose
- OpenAI API Key

### 2. 프로젝트 설정

```bash
# 저장소 클론
git clone <repository-url>
cd research-curator

# 개발 환경 설정 (가상환경 + 의존성 설치)
make init-dev
# 또는
bash install.sh --dev

# 가상환경 활성화
source .venv/bin/activate
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필수 항목)
# - OPENAI_API_KEY: OpenAI API 키
# - DATABASE_URL: PostgreSQL 연결 문자열
# - JWT_SECRET_KEY: JWT 토큰 시크릿 키
```

**필수 환경 변수:**
```bash
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/research_curator
JWT_SECRET_KEY=your-secret-key-change-in-production
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 4. Docker 서비스 시작

```bash
# PostgreSQL & Qdrant 컨테이너 시작
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

### 5. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head
```

### 6. 애플리케이션 실행

**Backend API 서버:**
```bash
# 터미널 1
source .venv/bin/activate
uvicorn src.app.api.main:app --reload

# 서버 실행 확인
# http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

**Frontend 대시보드:**
```bash
# 터미널 2 (새 터미널)
source .venv/bin/activate
streamlit run src/app/frontend/main.py

# 대시보드 접속
# http://localhost:8501
```

### 7. 서비스 확인

1. **Backend API 확인**
   - 브라우저에서 http://localhost:8000/docs 접속
   - Swagger UI에서 API 문서 확인

2. **Frontend 접속**
   - 브라우저에서 http://localhost:8501 접속
   - 매직 링크로 로그인 (이메일 입력)

3. **주요 기능 테스트**
   - 📊 Dashboard: 통계 및 최근 다이제스트 확인
   - 🔍 Search: 시맨틱/키워드 검색
   - 💬 Feedback: 피드백 제출 및 통계 확인
   - ⚙️ Settings: 사용자 설정 변경

---

## 📖 사용 방법

### 1. 온보딩

1. Frontend 접속 (http://localhost:8501)
2. 이메일 입력하여 매직 링크 요청
3. 이메일에서 링크 클릭 (로컬 환경에서는 터미널에 토큰 출력)
4. 자동으로 로그인 및 기본 설정 생성

### 2. 설정 관리

**Settings 페이지**에서:
- 연구 분야 설정 (예: Machine Learning, NLP)
- 관심 키워드 설정 (예: transformer, GPT, BERT)
- 정보 유형 비율 설정 (논문/뉴스/리포트)
- 이메일 발송 시간 및 일일 아티클 수 설정

### 3. 검색 기능

**Search 페이지**에서:
- **시맨틱 검색**: 자연어로 의미 기반 검색
  - 예: "transformer 모델 최적화 기법"
- **키워드 검색**: 정확한 키워드 매칭
  - 예: "GPT-4", "BERT"
- **고급 필터**: Source Type, 카테고리, 중요도, 날짜 범위

### 4. 피드백 제출

**Feedback 페이지**에서:
- 받은 아티클에 대한 평점 및 코멘트 작성
- 내 피드백 이력 확인
- 피드백 수정/삭제
- 아티클별 통계 확인

---

## 🛠️ 개발 명령어

### Make 명령어

```bash
# 도움말 표시
make help

# 개발 환경 초기화
make init-dev

# 프로덕션 환경 초기화
make init

# 코드 포맷팅 (Ruff)
make format

# Docker 서비스 시작
make up

# Docker 서비스 중지
make down
```

### 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 마이그레이션 이력 확인
alembic history
```

### 테스트

```bash
# 전체 테스트 실행
pytest tests/

# 특정 테스트 파일 실행
pytest tests/test_llm_client.py

# 커버리지와 함께 실행
pytest -v --cov=src/app
```

---

## 🔧 문제 해결

### 1. Docker 컨테이너가 시작되지 않을 때

```bash
# 기존 컨테이너 제거
docker-compose down -v

# 다시 시작
docker-compose up -d
```

### 2. 데이터베이스 연결 오류

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs postgres

# 포트 확인 (5433이 사용 중인지)
lsof -i :5433
```

### 3. Qdrant 연결 오류

```bash
# Qdrant 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs qdrant

# 포트 확인 (6333이 사용 중인지)
lsof -i :6333
```

### 4. Frontend 실행 오류

```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# Streamlit 재설치
uv pip install --upgrade streamlit

# 캐시 삭제
rm -rf ~/.streamlit
```

### 5. API 서버 포트 충돌

```bash
# 8000 포트 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 다른 포트로 실행
uvicorn src.app.api.main:app --port 8001 --reload
```

---

## 📁 프로젝트 구조

```
research-curator/
├── src/app/
│   ├── api/                    # FastAPI 백엔드
│   │   ├── main.py            # FastAPI 앱 엔트리포인트
│   │   ├── routers/           # API 라우터
│   │   ├── schemas/           # Pydantic 스키마
│   │   └── dependencies.py    # 의존성 주입
│   ├── db/                    # 데이터베이스
│   │   ├── models.py          # SQLAlchemy 모델
│   │   ├── session.py         # DB 세션
│   │   └── crud/              # CRUD 함수
│   ├── frontend/              # Streamlit 프론트엔드
│   │   ├── main.py            # Streamlit 엔트리포인트
│   │   ├── pages/             # 페이지 컴포넌트
│   │   └── utils/             # 유틸리티
│   ├── llm/                   # LLM 통합
│   ├── collectors/            # 데이터 수집
│   ├── vector_db/             # Qdrant 통합
│   └── scheduler/             # 스케줄러 (추후)
├── alembic/                   # DB 마이그레이션
├── docs/                      # 문서
├── tests/                     # 테스트
├── docker-compose.yml         # Docker 설정
├── pyproject.toml             # Python 프로젝트 설정
└── README.md                  # 이 파일
```

---

## 📚 API 문서

### API 엔드포인트

**인증 (2개)**
- `POST /auth/magic-link` - Magic link 요청
- `GET /auth/verify` - Magic link 검증

**사용자 (3개)**
- `GET /users/me` - 현재 사용자 정보
- `GET /users/{user_id}/preferences` - 사용자 설정 조회
- `PUT /users/{user_id}/preferences` - 사용자 설정 업데이트

**아티클 (9개)**
- `GET /api/articles` - 아티클 목록 (필터링, 페이지네이션)
- `GET /api/articles/{article_id}` - 단일 아티클 조회
- `POST /api/articles/search` - 시맨틱 검색
- `GET /api/articles/{article_id}/similar` - 유사 아티클
- `POST /api/articles/batch` - 배치 조회
- `GET /api/articles/statistics/summary` - 통계
- `GET /api/articles/keyword-search` - 키워드 검색
- `DELETE /api/articles/{article_id}` - 아티클 삭제

**다이제스트 (2개)**
- `GET /users/{user_id}/digests` - 다이제스트 목록

**피드백 (7개)**
- `POST /api/feedback` - 피드백 생성
- `GET /api/feedback/{feedback_id}` - 단일 피드백
- `PUT /api/feedback/{feedback_id}` - 피드백 업데이트
- `DELETE /api/feedback/{feedback_id}` - 피드백 삭제
- `GET /api/feedback/user/{user_id}` - 사용자 피드백
- `GET /api/feedback/article/{article_id}` - 아티클 피드백
- `GET /api/feedback/article/{article_id}/stats` - 통계

**데이터 수집 (3개)**
- `POST /api/collectors/search` - 통합 검색
- `POST /api/collectors/arxiv` - arXiv 논문
- `POST /api/collectors/news` - 뉴스

자세한 API 문서는 http://localhost:8000/docs (Swagger UI) 참조

---

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이센스

This project is licensed under the MIT License.

---

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---
