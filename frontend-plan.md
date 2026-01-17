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

## UI/UX 디자인 가이드라인

### 디자인 레퍼런스

참고 디자인: Jay Jhaveri Portfolio, maskara.ai
- 미니멀하고 클린한 화이트 기반 디자인
- 충분한 여백(whitespace)과 넓은 패딩
- 둥근 모서리의 Pill 형태 네비게이션
- 그라데이션 배경 효과 (은은한 파스텔)
- 아이콘 + 텍스트 조합의 깔끔한 카드

### 디자인 원칙

- **미니멀리즘**: 불필요한 요소 제거, 핵심 콘텐츠에 집중
- **여백 활용**: 넉넉한 padding/margin으로 시원한 레이아웃
- **일관된 둥근 모서리**: rounded-xl ~ rounded-2xl 사용
- **미묘한 그림자**: shadow-sm 위주, 과하지 않게
- Streamlit POC의 **기능과 워크플로우**를 참고하되, **배치/레이아웃/색상 테마**는 새롭게 구성

### 색상 테마 (Phase 1)

```
Primary:        Blue (#2563EB / blue-600)
Primary Hover:  Blue (#1D4ED8 / blue-700)
Primary Light:  Blue (#DBEAFE / blue-100)

Background:     White (#FFFFFF)
Surface:        Gray (#F9FAFB / gray-50)
Card BG:        White (#FFFFFF)
Border:         Gray (#E5E7EB / gray-200)

Text Primary:   Gray (#111827 / gray-900)  - 거의 블랙
Text Secondary: Gray (#6B7280 / gray-500)
Text Muted:     Gray (#9CA3AF / gray-400)

Success:        Green (#10B981 / emerald-500)
Warning:        Amber (#F59E0B / amber-500)
Error:          Red (#EF4444 / red-500)
Info:           Blue (#3B82F6 / blue-500)

Accent Gradient: linear-gradient(135deg, #DBEAFE, #FDE7F3, #E0E7FF)
                 (은은한 파스텔 그라데이션 - 히어로 섹션 배경)
```

### 타이포그래피

```
Font Family:    Inter (또는 Pretendard for 한글)
                font-family: 'Inter', 'Pretendard', sans-serif;

Heading 1:      text-4xl md:text-5xl font-bold (48-60px)
Heading 2:      text-2xl md:text-3xl font-semibold (24-30px)
Heading 3:      text-xl font-semibold (20px)
Body:           text-base (16px)
Small:          text-sm (14px)
Caption:        text-xs text-gray-500 (12px)
```

### 레이아웃 구조

#### 1. 공통 Header (모든 페이지)
```
┌──────────────────────────────────────────────────────────────┐
│  Logo          [  About  |  Projects  |  Contact  ]    🔗 🔗 │
│                       (Pill 형태 Nav)              (소셜 링크)│
└──────────────────────────────────────────────────────────────┘
```
- 중앙에 Pill 형태(rounded-full, bg-gray-100) 네비게이션
- 좌측 로고, 우측 소셜/유저 메뉴
- 배경: 투명 or 흰색, 스크롤 시 shadow 추가

#### 2. Landing/Hero 섹션 (로그인 전)
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              "Research Curator"                              │
│         AI 기반 맞춤형 연구 큐레이션 서비스                    │
│                                                              │
│         [ 🚀 시작하기 ]    [ 📖 더 알아보기 ]                  │
│                                                              │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│   │ Feature │  │ Feature │  │ Feature │  │ Feature │        │
│   │  Card   │  │  Card   │  │  Card   │  │  Card   │        │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                  (가로 스크롤 or 그리드)                      │
└──────────────────────────────────────────────────────────────┘
```
- 파스텔 그라데이션 배경
- 큰 타이틀 + 서브텍스트
- CTA 버튼 2개 (Primary + Secondary)
- 하단에 Feature 카드 슬라이드

#### 3. 로그인 페이지
```
┌──────────────────────────────────────────────────────────────┐
│                         Header                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌─────────────────┐                       │
│                    │     🔐 로고      │                       │
│                    │                 │                       │
│                    │  Magic Link     │                       │
│                    │  로그인         │                       │
│                    │                 │                       │
│                    │ [이메일 입력    ]│                       │
│                    │ [ 로그인 링크   ]│                       │
│                    │     전송        │                       │
│                    └─────────────────┘                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```
- 중앙 정렬 카드
- 최소한의 입력 필드
- 깔끔한 CTA 버튼

#### 4. 대시보드 레이아웃 (로그인 후)
```
┌──────────────────────────────────────────────────────────────┐
│  Logo    [대시보드 | 검색 | 설정 | 피드백]      👤 User ▼    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Main Content Area                         │  │
│  │                                                        │  │
│  │   (통계 카드, 다이제스트 목록, 검색 결과 등)            │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```
- 탑 네비게이션 (사이드바 대신)
- 넓은 콘텐츠 영역
- 모바일에서는 햄버거 메뉴

#### 5. AI 챗봇 (온보딩/검색)
```
┌──────────────────────────────────────────────────────────────┐
│  왼쪽 패널 (대화)          │  오른쪽 패널 (상세/결과)        │
│                            │                                │
│  💬 AI 메시지              │   Job Status                   │
│     ┌────────────────────┐ │   ┌──────────────────────────┐ │
│     │ 연구 분야를 알려주세요│ │   │ Status: In progress     │ │
│     └────────────────────┘ │   │ Started: 10:00           │ │
│                            │   └──────────────────────────┘ │
│  👤 사용자 메시지          │                                │
│     ┌────────────────────┐ │   Files                        │
│     │ AI/ML 연구입니다    │ │   ┌──────┐ ┌──────┐          │
│     └────────────────────┘ │   │📄 PDF │ │📊 XLS│          │
│                            │   └──────┘ └──────┘          │
│  [옵션1] [옵션2] [옵션3]   │                                │
│                            │   Preview                      │
│  ┌─────────────────────┐   │   ┌──────────────────────────┐ │
│  │ 메시지 입력...    ➤ │   │   │ Summary content...       │ │
│  └─────────────────────┘   │   └──────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```
- 좌우 분할 레이아웃 (maskara.ai 참고)
- 왼쪽: 채팅 인터페이스
- 오른쪽: 진행 상태, 파일, 결과 미리보기

### 컴포넌트 스타일

#### Button
```tsx
// Primary (파란색 채움)
className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-full
           font-medium transition-colors flex items-center gap-2"

// Secondary (테두리)
className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-900
           px-6 py-3 rounded-full font-medium transition-colors"
```

#### Card
```tsx
className="bg-white rounded-2xl border border-gray-200 p-6
           shadow-sm hover:shadow-md transition-shadow"
```

#### Input
```tsx
className="w-full px-4 py-3 rounded-xl border border-gray-200
           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
           placeholder:text-gray-400"
```

#### Navigation Pill
```tsx
// Container
className="bg-gray-100 rounded-full p-1 flex gap-1"

// Item (비활성)
className="px-4 py-2 rounded-full text-gray-600 hover:text-gray-900 transition-colors"

// Item (활성)
className="px-4 py-2 rounded-full bg-white text-gray-900 shadow-sm font-medium"
```

#### Feature Card (아이콘 + 텍스트)
```tsx
className="bg-white rounded-2xl border border-gray-200 p-6 text-center
           hover:shadow-md transition-shadow"
// 내부: 아이콘(48x48) + 타이틀
```

#### Badge/Chip
```tsx
// 옵션 선택 버튼 (챗봇)
className="px-4 py-2 rounded-full border border-gray-200 bg-white
           hover:bg-gray-50 text-sm flex items-center gap-2 cursor-pointer"
```

### 네비게이션 구조

```
Landing (/) → 로그인 (/login) → 온보딩 (/onboarding) → 대시보드 (/dashboard)
                                         │
                    ┌────────────────────┴────────────────────┐
                    │           Top Navigation                │
                    ├─────────────────────────────────────────┤
                    │ 📊 대시보드 │ 🔍 검색 │ ⚙️ 설정 │ 💬 피드백 │
                    └─────────────────────────────────────────┘
                                         │
                              (ADMIN only: 관리자)
```

### 반응형 브레이크포인트

- **Mobile**: < 768px
  - 탑 네비 → 햄버거 메뉴
  - 2컬럼 → 1컬럼 스택
  - 챗봇 좌우분할 → 탭 전환
- **Tablet**: 768px - 1024px
  - 축소된 네비게이션
  - 2컬럼 그리드 유지
- **Desktop**: > 1024px
  - 전체 네비게이션 표시
  - 최대 너비 제한 (max-w-7xl)

### 애니메이션/트랜지션

- **Hover**: transition-all duration-200
- **Page Transition**: fade-in (optional, framer-motion)
- **Loading**: Skeleton UI (shimmer effect)
- **Toast**: slide-in from top-right

### 향후 개선 예정 (Phase 6+)

- 다크 모드 지원
- 테마 커스터마이징
- 더 정교한 애니메이션
- 접근성(a11y) 강화

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
