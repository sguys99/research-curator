# JS 프론트엔드 구현 계획

## 개요
기존 Streamlit 기반 프론트엔드를 Next.js 14 기반 production-grade 프론트엔드로 고도화합니다.

### 제약 조건
- 백엔드(FastAPI), 스케줄러(APScheduler) 수정 없음
- 기존 Streamlit 프론트엔드는 `src/frontend-poc`로 이동하여 보존

## 기술 스택

| 항목 | 기술 |
|------|------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5.x |
| UI | shadcn/ui + Tailwind CSS |
| State | Zustand (global) + TanStack Query (server) |
| Forms | React Hook Form + Zod |
| HTTP | Axios |
| Package Manager | pnpm |
| Testing | Vitest + Playwright |

## 디렉토리 구조

### 변경 사항
```
src/app/frontend/  → src/app/frontend-poc/  (기존 Streamlit 이름 변경)
frontend/          ← 새로운 Next.js 프론트엔드 (프로젝트 루트)
```

### 전체 프로젝트 구조
```
research-curator/
├── src/app/                          # Python 백엔드 (유지)
│   ├── api/                          # FastAPI
│   ├── scheduler/                    # APScheduler
│   ├── db/                           # Database
│   ├── collectors/                   # Data collectors
│   ├── processors/                   # LLM processors
│   └── frontend-poc/                 # 기존 Streamlit (이름 변경)
│
├── frontend/                         # 새로운 Next.js 프론트엔드
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── .env.example
│   ├── .eslintrc.json
│   │
│   ├── public/
│   │   └── logo.png
│   │
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # Root layout
│   │   ├── page.tsx                  # Landing → Login redirect
│   │   ├── globals.css
│   │   │
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx        # Magic link 로그인
│   │   │   └── verify/page.tsx       # 토큰 검증
│   │   │
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx            # 사이드바 레이아웃
│   │   │   ├── dashboard/page.tsx    # 메인 대시보드
│   │   │   ├── onboarding/page.tsx   # AI 챗봇 온보딩
│   │   │   ├── search/page.tsx       # 시맨틱/키워드 검색
│   │   │   ├── settings/page.tsx     # 사용자 설정
│   │   │   └── feedback/page.tsx     # 피드백 관리
│   │   │
│   │   └── (admin)/
│   │       └── admin/page.tsx        # 관리자 대시보드
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui 컴포넌트
│   │   ├── layout/                   # Sidebar, Header
│   │   ├── auth/                     # LoginForm, AuthGuard
│   │   ├── dashboard/                # StatsCards, DigestList
│   │   ├── articles/                 # ArticleCard, ArticleList
│   │   ├── search/                   # SearchForm, Filters
│   │   ├── onboarding/               # Chatbot, ChatMessage
│   │   ├── settings/                 # PreferencesForm
│   │   ├── feedback/                 # FeedbackForm, RatingStars
│   │   └── admin/                    # SystemOverview, UsersTable
│   │
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-articles.ts
│   │   ├── use-search.ts
│   │   ├── use-preferences.ts
│   │   ├── use-feedback.ts
│   │   └── use-chat-stream.ts        # SSE 스트리밍
│   │
│   ├── lib/
│   │   ├── api/                      # API 클라이언트
│   │   │   ├── client.ts             # Axios 설정
│   │   │   ├── auth.ts
│   │   │   ├── users.ts
│   │   │   ├── articles.ts
│   │   │   ├── feedback.ts
│   │   │   └── llm.ts                # 챗봇 스트리밍
│   │   └── utils/
│   │
│   ├── stores/
│   │   ├── auth-store.ts
│   │   └── onboarding-store.ts
│   │
│   ├── types/
│   │   └── *.ts                      # API 타입 정의
│   │
│   └── providers/
│       ├── query-provider.tsx
│       └── auth-provider.tsx
│
└── configs/                          # 기존 설정 (유지)
```

## 구현 단계

### Phase 1: 프로젝트 설정 및 인프라
1. 기존 `src/frontend/` → `src/frontend-poc/` 이동
2. Next.js 14 프로젝트 초기화
3. shadcn/ui + Tailwind CSS 설정
4. ESLint, Prettier 설정
5. API 클라이언트 구현 (Axios + JWT 인터셉터)
6. 기본 레이아웃 (Root, Dashboard, Sidebar)

**수정 파일:**

- `src/app/frontend/` → `src/app/frontend-poc/` (이름 변경)
- `frontend/` (프로젝트 루트에 새로 생성)

### Phase 2: 인증 및 온보딩
1. Magic Link 로그인 페이지
2. 토큰 검증 페이지
3. Auth Guard 컴포넌트
4. Zustand auth store
5. AI 챗봇 온보딩 (5단계 질문)
   - SSE 스트리밍 지원
   - 다중 선택 옵션 버튼
   - Preference 저장

**API 연동:**
- `POST /auth/magic-link`
- `GET /auth/verify?token=`
- `GET /users/me`
- `PUT /users/{user_id}/preferences`
- `POST /api/llm/chat/completions` (stream)

### Phase 3: 대시보드 및 검색
1. 대시보드
   - 통계 카드 (총 아티클, 다이제스트, 평균 평점)
   - 최근 다이제스트 목록
   - 스케줄러 상태 (읽기 전용)
   - Quick Actions (테스트 이메일, 수동 트리거)
2. 검색 페이지
   - 시맨틱 검색 (벡터 DB)
   - 키워드 검색
   - 필터 (source_type, category, date, importance)
   - 유사 아티클 찾기
3. Article Card 컴포넌트

**API 연동:**
- `GET /api/articles`
- `POST /api/articles/search`
- `GET /api/articles/{id}/similar`
- `GET /api/articles/keyword-search`
- `GET /api/articles/statistics/summary`
- `GET /users/{user_id}/digests`
- `POST /users/{user_id}/digests/test`
- `GET /api/scheduler/status`
- `POST /api/scheduler/jobs/trigger`

### Phase 4: 설정 및 피드백
1. 설정 페이지
   - 연구 분야, 키워드 입력
   - 정보 유형 비율 (paper/news/report)
   - 이메일 설정 (시간, 일일 한도, 활성화)
   - Zod 스키마 검증
2. 피드백 페이지
   - 피드백 제출 (별점 + 코멘트)
   - 피드백 이력 (수정/삭제)
   - 아티클 통계

**API 연동:**
- `GET /users/{user_id}/preferences`
- `PUT /users/{user_id}/preferences`
- `POST /api/feedback`
- `GET /api/feedback/user/{user_id}`
- `PUT /api/feedback/{feedback_id}`
- `DELETE /api/feedback/{feedback_id}`
- `GET /api/feedback/article/{article_id}/stats`

### Phase 5: 관리자 대시보드
1. 관리자 권한 체크 (ADMIN_EMAILS)
2. 시스템 개요 탭
   - 전체 사용자, 아티클, 다이제스트, 피드백 수
   - 스케줄러 상태
3. 사용자 관리 탭
4. 아티클 관리 탭
5. 다이제스트 이력 탭

**API 연동:**
- 기존 API 활용 (별도 admin API 없음)

### Phase 6: 마무리 및 최적화
1. 에러 바운더리 및 로딩 UI
2. Toast 알림 시스템
3. 반응형 디자인 (모바일)
4. 테스트 작성 (Unit, E2E)
5. 빌드 최적화
6. Docker 설정 (선택)

## API 클라이언트 패턴

```typescript
// lib/api/client.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// JWT 토큰 자동 주입
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 에러 시 로그아웃
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## 환경 변수

```bash
# src/frontend/.env.example
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ADMIN_EMAILS=admin@example.com
NEXT_PUBLIC_ENVIRONMENT=development
```

## 검증 계획

### 개발 중 검증
1. 각 Phase 완료 후 로컬에서 기능 테스트
2. `pnpm dev`로 개발 서버 실행
3. API 연동 확인 (백엔드 `uvicorn` 실행 필요)

### 최종 검증
1. **인증 플로우**: 이메일 입력 → Magic Link → 로그인 완료
2. **온보딩**: 5단계 챗봇 대화 → 설정 저장
3. **대시보드**: 통계 표시, 다이제스트 목록, 스케줄러 상태
4. **검색**: 시맨틱/키워드 검색, 필터, 유사 아티클
5. **설정**: Preference 수정 및 저장
6. **피드백**: 별점/코멘트 제출, 이력 관리
7. **관리자**: 관리자 계정으로 admin 대시보드 접근

### 테스트 실행
```bash
cd src/frontend
pnpm test        # Unit tests (Vitest)
pnpm test:e2e    # E2E tests (Playwright)
```

## 참고 파일

기존 Streamlit 구현 참고:

- [api_client.py](src/app/frontend-poc/utils/api_client.py) - API 엔드포인트 및 요청 패턴
- [chatbot.py](src/app/frontend-poc/components/chatbot.py) - 온보딩 챗봇 로직 (5단계)
- [dashboard.py](src/app/frontend-poc/pages/dashboard.py) - 대시보드 기능
- [search.py](src/app/frontend-poc/pages/search.py) - 검색 기능
- [settings.py](src/app/frontend-poc/pages/settings.py) - 설정 페이지
- [feedback.py](src/app/frontend-poc/pages/feedback.py) - 피드백 기능
- [admin.py](src/app/frontend-poc/pages/admin.py) - 관리자 대시보드

백엔드 API 스키마:

- [src/app/api/schemas/](src/app/api/schemas/) - 모든 API 요청/응답 타입 정의
