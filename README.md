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

### 사용자 여정 (User Journey)

Research Curator를 처음 사용하시는 분들을 위한 단계별 가이드입니다.

#### 1단계: 로그인 (매직 링크 인증)

1. Frontend 접속: http://localhost:8501
2. 로그인 화면에서 이메일 주소 입력
3. "매직 링크 발송" 버튼 클릭
4. 이메일에서 링크 클릭 (로컬 환경에서는 터미널에 토큰 출력)
5. 자동으로 로그인 및 기본 사용자 계정 생성

**개발 환경 팁:**
- 로컬에서 테스트 시 "토큰으로 로그인" 확장 메뉴 사용
- 터미널에 출력된 JWT 토큰을 복사하여 직접 입력 가능

#### 2단계: 온보딩 (최초 1회)

로그인 후 처음 사용 시 AI 챗봇이 안내하는 온보딩 진행:

1. **AI 어시스턴트 질문에 답변** (약 2-3분 소요)
   - 연구 분야 입력 (예: Machine Learning, NLP)
   - 관심 키워드 입력 (예: transformer, GPT, BERT)
   - 선호하는 정보 유형 선택 (논문/뉴스/리포트 비율)
   - 이메일 발송 시간 설정
   - 일일 아티클 수 설정

2. **입력 형식 안내:**
   - 여러 항목은 쉼표(,)로 구분
   - 예: "Deep Learning, NLP, Computer Vision"

3. **설정 확인 후 저장**
   - 온보딩 완료 후 대시보드로 자동 이동
   - 언제든 Settings 페이지에서 수정 가능

#### 3단계: 대시보드 사용

온보딩 완료 후 메인 화면으로 사용하는 페이지:

**주요 기능:**
- **통계 카드 확인**
  - 총 아티클 수
  - 받은 이메일 수
  - 평균 피드백 점수

- **최근 받은 이메일 확인**
  - 각 다이제스트별 아티클 목록 표시
  - 아티클 카드로 제목, 요약, 중요도 확인
  - 원문 링크 클릭하여 전체 내용 확인

- **빠른 작업 버튼**
  - 📧 **테스트 이메일 발송**: 즉시 테스트 다이제스트 받기
  - 🔍 **검색하기**: 검색 페이지로 바로 이동
  - ⚙️ **설정 변경**: 설정 페이지로 바로 이동

#### 4단계: 검색 기능 활용

과거에 받은 아티클을 검색하고 재탐색:

**🧠 시맨틱 검색 (추천)**
1. "시맨틱 검색" 탭 선택
2. 자연어로 검색어 입력
   - 예: "transformer 아키텍처 최적화 방법"
   - 예: "GPT-4 성능 평가 결과"
3. 필터 옵션 설정 (선택사항)
   - Source Type: paper, news, report, blog
   - Category: AI, NLP, ML, CV, Robotics
   - 최소 중요도: 0.0 ~ 1.0
   - 날짜 범위 설정
   - 유사도 임계값: 0.0 ~ 1.0
   - 최대 결과 수: 1 ~ 50
4. "🔍 검색" 버튼 클릭
5. 검색 결과 확인 및 원문 읽기

**🔤 키워드 검색**
1. "키워드 검색" 탭 선택
2. 정확한 키워드 입력
   - 예: "GPT-4", "BERT", "attention mechanism"
3. 제목, 요약, 내용에서 키워드 매칭
4. 검색 결과 확인

**💡 검색 예시 활용:**
- 하단에 제공되는 예시 쿼리 버튼 클릭
- 클릭 시 자동으로 검색어가 입력되어 검색 실행

**🔄 검색 초기화:**
- "🔄 초기화" 버튼으로 검색어 및 필터 초기화

**유사 문서 검색:**
- 아티클 카드에서 "유사 문서 찾기" 버튼 클릭
- 해당 아티클과 유사한 문서 자동 검색

#### 5단계: 설정 관리

언제든 사용자 설정 변경 가능:

**📚 연구 분야 및 키워드**
- **연구 분야**: 쉼표로 구분하여 입력
  - 예: "Machine Learning, NLP, Computer Vision"
- **관심 키워드**: 쉼표로 구분하여 입력
  - 예: "transformer, GPT, BERT, attention"

**📰 정보 유형 비율**
- 슬라이더로 논문/뉴스/리포트 비율 설정
- 합계가 100%가 되도록 자동 정규화
- 예: 논문 70%, 뉴스 20%, 리포트 10%

**🌐 추가 소스**
- 특정 웹사이트 추가 모니터링
- 도메인 형식으로 입력 (예: techcrunch.com)

**📧 이메일 설정**
- **발송 시간**: 08:00 ~ 21:00 중 선택
- **일일 아티클 수**: 1 ~ 20개
- **이메일 수신**: 체크박스로 활성화/비활성화

**💾 설정 저장:**
- "💾 설정 저장" 버튼으로 변경사항 저장
- 저장 후 자동으로 페이지 새로고침

**💡 도움말:**
- "설정 가이드" 확장 메뉴에서 상세 설명 확인
- "현재 설정 요약"에서 JSON 형식으로 전체 설정 확인

#### 6단계: 피드백 제출

받은 아티클을 평가하여 추천 알고리즘 개선에 기여:

**📝 피드백 제출 (Tab 1)**

1. **피드백 방법 선택:**
   - **최근 다이제스트에서 선택** (추천)
     - 최근 5개 다이제스트 목록 표시
     - 다이제스트 선택 → 아티클 선택
     - 선택한 아티클 미리보기 확인
   - **아티클 ID 직접 입력**
     - UUID 형식의 아티클 ID 입력
     - 아티클 정보 자동 로드 및 미리보기

2. **평점 선택:**
   - 슬라이더로 1~5점 선택
   - 실시간 별점 표시 (⭐⭐⭐⭐⭐)
   - 평점 기준:
     - 1⭐: 전혀 유용하지 않음
     - 2⭐: 별로 유용하지 않음
     - 3⭐: 보통
     - 4⭐: 유용함
     - 5⭐: 매우 유용함

3. **코멘트 작성 (선택사항):**
   - 최대 500자
   - 유용했던 이유, 개선점 등 자유롭게 작성

4. **피드백 제출:**
   - "📤 피드백 제출" 버튼 클릭
   - 제출 완료 시 축하 애니메이션

**📊 피드백 이력 (Tab 2)**

1. **통계 확인:**
   - 총 피드백 수
   - 평균 평점
   - 최다 평점

2. **평점 분포:**
   - 1~5점별 피드백 개수 및 비율

3. **피드백 목록:**
   - **필터 옵션:**
     - 평점 필터 (멀티셀렉트)
     - 정렬: 최신순, 평점 높은/낮은 순
   - **각 피드백 카드:**
     - 평점, 코멘트, 제출일 표시
     - ✏️ **수정** 버튼: 평점/코멘트 수정
     - 🗑️ **삭제** 버튼: 피드백 삭제

4. **피드백 수정:**
   - 수정 모드에서 새 평점/코멘트 입력
   - 💾 저장 또는 ❌ 취소

**📈 아티클 통계 (Tab 3)**

1. **아티클 ID 입력:**
   - 특정 아티클의 전체 사용자 피드백 통계 조회

2. **아티클 정보 확인:**
   - 제목, 요약, 출처, 카테고리
   - 원문 보기 링크

3. **피드백 통계:**
   - 총 피드백 수
   - 평균 평점
   - 최다 평점
   - 평점 분포 (1~5점별 개수 및 비율)
   - 분포 차트 (막대 그래프)

4. **최근 피드백 확인:**
   - 다른 사용자들의 최근 피드백 10개
   - 평점 및 코멘트 확인

---

## 🎯 페이지별 상세 가이드

### 🔐 로그인 페이지

**목적:** 비밀번호 없는 간편한 이메일 인증

**UI 요소:**
- 이메일 입력 필드
- "매직 링크 발송" 버튼 (Primary)
- "토큰으로 로그인" 확장 메뉴 (개발용)

**사용 방법:**
1. 이메일 주소 입력 (예: user@example.com)
2. "매직 링크 발송" 버튼 클릭
3. 이메일 확인 또는 터미널에서 토큰 복사
4. (개발용) 토큰을 "토큰으로 로그인"에 붙여넣기

**주의사항:**
- 유효한 이메일 형식 필요 (@포함)
- 로컬 환경에서는 실제 이메일 발송 안됨 (토큰만 출력)

---

### 🎯 온보딩 페이지

**목적:** AI 챗봇과 대화하며 맞춤형 설정 완료

**UI 요소:**
- 환영 헤더 (그라데이션 배경)
- 정보 카드 (소요 시간, 질문 수, 맞춤 설정)
- AI 챗봇 인터페이스
- 사이드바 도움말

**진행 단계:**
1. 연구 분야 입력
2. 관심 키워드 입력
3. 정보 유형 비율 선택
4. 이메일 발송 시간 선택
5. 일일 아티클 수 설정
6. 최종 확인 및 저장

**입력 팁:**
- 여러 항목은 쉼표로 구분
- 구체적일수록 정확한 큐레이션 가능
- 나중에 언제든 수정 가능

---

### 📊 대시보드 페이지

**목적:** 최근 받은 다이제스트 및 통계 확인

**UI 요소:**
- **통계 카드 (상단)**
  - 📚 총 아티클
  - 📧 받은 이메일
  - ⭐ 평균 피드백

- **최근 받은 이메일 섹션**
  - 다이제스트별 확장 패널
  - 아티클 카드 (제목, 요약, 중요도, 출처)
  - "유사 문서 찾기" 버튼

- **빠른 작업 버튼 (하단)**
  - 📧 테스트 이메일 발송
  - 🔍 검색하기
  - ⚙️ 설정 변경

**사용 시나리오:**
- 매일 아침 접속하여 받은 다이제스트 확인
- 테스트 이메일로 현재 설정 확인
- 아티클 읽고 피드백 제출

---

### 🔍 검색 페이지

**목적:** 과거 아티클 시맨틱/키워드 검색

**UI 요소:**
- **검색 탭**
  - 🧠 시맨틱 검색
  - 🔤 키워드 검색

- **필터 옵션 (확장 메뉴)**
  - Source Type 멀티셀렉트
  - Category 멀티셀렉트
  - 최소 중요도 슬라이더
  - 날짜 범위 선택
  - 유사도 임계값 슬라이더
  - 최대 결과 수 입력

- **검색 버튼 영역**
  - 🔍 검색 (Primary)
  - 🔄 초기화

- **검색 예시 버튼**
  - 5개의 예시 쿼리 버튼

- **검색 결과**
  - 아티클 카드 목록
  - "유사 문서 찾기" 버튼

**사용 팁:**
- 시맨틱 검색: 자연어로 의미 기반 검색
- 키워드 검색: 정확한 단어 매칭
- 필터 조합으로 정밀한 검색 가능
- 유사 문서 검색으로 관련 자료 확장

---

### ⚙️ 설정 페이지

**목적:** 사용자 맞춤 설정 관리

**UI 요소:**
- **연구 분야 및 키워드 섹션**
  - 연구 분야 텍스트 영역
  - 관심 키워드 텍스트 영역

- **정보 유형 비율 섹션**
  - 📚 논문 슬라이더 (0-100%)
  - 📰 뉴스 슬라이더 (0-100%)
  - 📊 리포트 슬라이더 (0-100%)
  - 합계 표시 (자동 정규화 안내)

- **추가 소스 섹션**
  - 웹사이트 URL 텍스트 영역

- **이메일 설정 섹션**
  - 발송 시간 셀렉트박스
  - 일일 아티클 수 입력
  - 이메일 수신 체크박스

- **저장 버튼**
  - 💾 설정 저장 (Primary)

- **도움말 섹션**
  - 설정 가이드 확장 메뉴
  - 현재 설정 요약 (JSON)

**설정 변경 흐름:**
1. 원하는 항목 수정
2. 변경 내용 확인
3. "💾 설정 저장" 버튼 클릭
4. 성공 메시지 확인
5. 자동 새로고침

---

### 💬 피드백 페이지

**목적:** 아티클 평가 및 피드백 관리

**UI 요소:**

**Tab 1: 📝 피드백 제출**
- 피드백 방법 라디오 버튼
  - 최근 다이제스트에서 선택
  - 아티클 ID 직접 입력
- 다이제스트 셀렉트박스
- 아티클 셀렉트박스
- 아티클 미리보기 확장 메뉴
- 평점 슬라이더 (1-5)
- 별점 표시 (⭐⭐⭐⭐⭐)
- 코멘트 텍스트 영역 (최대 500자)
- 📤 피드백 제출 버튼

**Tab 2: 📊 피드백 이력**
- 통계 카드 (총 피드백, 평균 평점, 최다 평점)
- 평점 분포 (1~5점별 개수 및 비율)
- 필터 옵션 (평점, 정렬)
- 피드백 목록 (확장 패널)
- 각 피드백 카드
  - ✏️ 수정 버튼
  - 🗑️ 삭제 버튼
- 수정 모드 (슬라이더, 텍스트 영역)
  - 💾 저장 버튼
  - ❌ 취소 버튼

**Tab 3: 📈 아티클 통계**
- 아티클 ID 입력 필드
- 아티클 정보 표시
- 원문 보기 링크 버튼
- 통계 카드 (총 피드백, 평균 평점, 최다 평점)
- 평점 분포 (1~5점별)
- 분포 차트 (막대 그래프)
- 최근 피드백 목록 (확장 패널)

**피드백 제출 흐름:**
1. 아티클 선택 (다이제스트 또는 ID)
2. 아티클 미리보기 확인
3. 평점 선택 (1-5)
4. 코멘트 작성 (선택)
5. 피드백 제출
6. 성공 메시지 및 축하 애니메이션

---

## 🧭 사이드바 네비게이션

**고정 요소:**
- 🔬 **Research Curator** (앱 타이틀)
- 👤 **사용자 정보** (이름, 이메일)
- 📑 **메뉴** (페이지 네비게이션 버튼)
- ℹ️ **도움말** (확장 메뉴)
- 🚪 **로그아웃** 버튼

**메뉴 버튼:**
- 온보딩 미완료 시:
  - 🎯 온보딩
- 온보딩 완료 시:
  - 📊 대시보드
  - 🔍 검색
  - ⚙️ 설정
  - 💬 피드백

**도움말 내용:**
1. **대시보드**: 최근 받은 이메일 확인
2. **검색**: 과거 자료 시맨틱 검색
3. **설정**: 키워드, 소스, 발송 시간 변경
4. **피드백**: 받은 아티클 평가

**문의:**
- contact@research-curator.com

---

## ⚡ 팁 & 트릭

### 효율적인 검색 방법
1. **시맨틱 검색 활용**: 자연어로 의미 기반 검색이 정확도가 높음
2. **필터 조합**: Source Type + Category + 중요도로 정밀 검색
3. **유사 문서 검색**: 관심 있는 아티클의 유사 자료 찾기
4. **검색 예시 활용**: 제공되는 예시 쿼리로 빠른 검색

### 설정 최적화
1. **구체적인 키워드**: 일반적인 키워드보다 구체적인 키워드가 정확도 향상
2. **정보 유형 비율**: 논문 중심(70%)이 학술 연구에 유리
3. **일일 아티클 수**: 처음에는 5개로 시작, 필요에 따라 조정
4. **발송 시간**: 출근 시간에 맞춰 설정하면 편리

### 피드백 전략
1. **꾸준한 피드백**: 최소 주 3회 이상 피드백으로 추천 정확도 향상
2. **구체적인 코멘트**: 단순 평점보다 코멘트 작성이 알고리즘 개선에 도움
3. **다양한 평점**: 모든 아티클에 높은 점수보다 변별력 있는 평가가 유용

### 시간 절약 팁
1. **대시보드 빠른 작업**: 자주 사용하는 기능은 빠른 작업 버튼 활용
2. **테스트 이메일**: 설정 변경 후 테스트 이메일로 즉시 확인
3. **검색 예시**: 검색 페이지의 예시 버튼으로 빠른 검색

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
