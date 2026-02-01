# Next.js 프론트엔드 다국어(i18n) 구현 계획

## 현재 상황 분석

### 프로젝트 환경

- Next.js 16.1.3 (App Router)
- React 19.2.3
- i18n 라이브러리 미설치
- 텍스트가 컴포넌트에 하드코딩됨

### 현재 텍스트 상태

| 페이지       | 상태       |
| ------------ | ---------- |
| 메인 페이지  | 완전 영문  |
| 온보딩       | 완전 한글  |
| 로그인/설정  | 한/영 혼합 |

---

## 기술 선택

### 라이브러리: **next-intl v4.x**

- Next.js 16 App Router 완벽 호환
- Server/Client Components 모두 지원
- 쿠키 기반 로케일 감지 내장
- TypeScript 완벽 지원

### 라우팅 방식: **localePrefix: 'never'** (쿠키 기반)

- 기존 URL 구조 유지 (`/dashboard`, `/settings`)
- `[locale]` 동적 세그먼트 불필요
- 마이그레이션 비용 최소화

### 기본 언어: **영어 (en)**

- 글로벌 서비스 지향
- 메인 페이지가 이미 영문으로 작성됨

### 언어 전환 UI: **버튼 그룹 (KO | EN)**

- 토글 형태로 직관적
- 2개 언어에 최적화

---

## 디렉토리 구조

```
frontend/
├── i18n/
│   ├── config.ts           # locales, defaultLocale 상수
│   ├── routing.ts          # defineRouting 설정
│   └── request.ts          # getRequestConfig 설정
├── messages/
│   ├── ko.json             # 한국어 번역
│   └── en.json             # 영어 번역
├── proxy.ts                # next-intl 미들웨어
└── components/layout/
    └── LanguageSwitcher.tsx  # 언어 전환 UI
```

---

## 단계별 구현 절차

### Phase 1: 기본 설정

#### Step 1.1: 패키지 설치

```bash
cd frontend
pnpm add next-intl
```

#### Step 1.2: i18n 설정 파일 생성

**i18n/config.ts**:

```typescript
export const locales = ['en', 'ko'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';  // 기본 언어: 영어
```

**i18n/routing.ts**:

```typescript
import { defineRouting } from 'next-intl/routing';
import { locales, defaultLocale } from './config';

export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: 'never',
  localeCookie: {
    name: 'NEXT_LOCALE',
    maxAge: 60 * 60 * 24 * 365,
  },
});
```

**i18n/request.ts**:

```typescript
import { cookies } from 'next/headers';
import { getRequestConfig } from 'next-intl/server';
import { defaultLocale, locales, type Locale } from './config';

export default getRequestConfig(async () => {
  const store = await cookies();
  const cookieLocale = store.get('NEXT_LOCALE')?.value;
  const locale: Locale =
    cookieLocale && locales.includes(cookieLocale as Locale)
      ? (cookieLocale as Locale)
      : defaultLocale;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
```

#### Step 1.3: next.config.ts 수정

```typescript
import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n/request.ts');

const nextConfig: NextConfig = {
  // 기존 설정 유지
};

export default withNextIntl(nextConfig);
```

#### Step 1.4: proxy.ts 생성

```typescript
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)',
};
```

---

### Phase 2: Provider 설정

#### Step 2.1: app/layout.tsx 수정

```typescript
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          {/* 기존 Provider들 */}
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

---

### Phase 3: 언어 전환 UI 구현

#### Step 3.1: LanguageSwitcher 컴포넌트 생성

```typescript
"use client";

import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useTransition } from 'react';

export default function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleChange = (newLocale: string) => {
    document.cookie = `NEXT_LOCALE=${newLocale};path=/;max-age=31536000`;
    startTransition(() => {
      router.refresh();
    });
  };

  return (
    <div className="flex rounded-lg border border-slate-200 p-0.5">
      <button
        onClick={() => handleChange('ko')}
        disabled={isPending}
        className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
          locale === 'ko'
            ? 'bg-blue-600 text-white'
            : 'text-slate-600 hover:text-slate-900'
        }`}
      >
        KO
      </button>
      <button
        onClick={() => handleChange('en')}
        disabled={isPending}
        className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
          locale === 'en'
            ? 'bg-blue-600 text-white'
            : 'text-slate-600 hover:text-slate-900'
        }`}
      >
        EN
      </button>
    </div>
  );
}
```

#### Step 3.2: 헤더에 통합

- `DashboardHeader.tsx`
- `MarketingHeader.tsx`

---

### Phase 4: 번역 파일 작성

#### Step 4.1: messages/en.json

```json
{
  "common": {
    "loading": "Loading...",
    "save": "Save",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "edit": "Edit",
    "delete": "Delete",
    "search": "Search",
    "logout": "Logout"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "search": "Search",
    "settings": "Settings",
    "feedback": "Feedback"
  },
  "home": {
    "hero": {
      "badge": "AI Research Concierge",
      "title": "Curate the research you actually need, delivered on schedule.",
      "description": "Research Curator blends automated crawling, LLM summarization, and semantic retrieval so your team stays ahead without manual triage."
    },
    "cta": {
      "magicLink": "Start with magic link",
      "workflow": "See the workflow"
    }
  }
}
```

#### Step 4.2: messages/ko.json

```json
{
  "common": {
    "loading": "로딩 중...",
    "save": "저장",
    "cancel": "취소",
    "confirm": "확인",
    "edit": "수정",
    "delete": "삭제",
    "search": "검색",
    "logout": "로그아웃"
  },
  "navigation": {
    "dashboard": "대시보드",
    "search": "검색",
    "settings": "설정",
    "feedback": "피드백"
  },
  "home": {
    "hero": {
      "badge": "AI 연구 컨시어지",
      "title": "필요한 연구를 큐레이션하여 정해진 일정에 전달합니다.",
      "description": "Research Curator는 자동 수집, LLM 요약, 시맨틱 검색을 결합하여 팀이 수동 분류 없이 앞서 나갈 수 있게 합니다."
    },
    "cta": {
      "magicLink": "매직 링크로 시작",
      "workflow": "워크플로우 보기"
    }
  }
}
```

---

### Phase 5: 컴포넌트 마이그레이션

#### 마이그레이션 우선순위

1. **공통 컴포넌트** - DashboardHeader, MarketingHeader
2. **메인 페이지** - app/page.tsx
3. **온보딩** - OnboardingChat.tsx, OnboardingSidebar.tsx
4. **대시보드/설정/검색** 페이지

#### Server Component 패턴

```typescript
import { getTranslations } from 'next-intl/server';

export default async function Page() {
  const t = await getTranslations('home');
  return <h1>{t('hero.title')}</h1>;
}
```

#### Client Component 패턴

```typescript
"use client";
import { useTranslations } from 'next-intl';

export default function Component() {
  const t = useTranslations('common');
  return <button>{t('save')}</button>;
}
```

---

### Phase 6: 동적 콘텐츠 처리

#### 날짜/숫자 포맷팅

```typescript
import { useFormatter } from 'next-intl';

const format = useFormatter();
format.dateTime(date, { dateStyle: 'medium' });
format.number(1234.56);
```

---

## 수정 대상 주요 파일

| 파일                                       | 작업 내용                    |
| ------------------------------------------ | ---------------------------- |
| `next.config.ts`                           | next-intl 플러그인 추가      |
| `app/layout.tsx`                           | NextIntlClientProvider 래핑  |
| `app/page.tsx`                             | 마케팅 텍스트 번역 적용      |
| `components/onboarding/OnboardingChat.tsx` | 챗봇 메시지 번역             |
| `components/layout/DashboardHeader.tsx`    | 네비게이션 번역              |
| `components/layout/MarketingHeader.tsx`    | 네비게이션 번역              |
| `app/(dashboard)/settings/page.tsx`        | 설정 UI 번역                 |

---

## 검증 방법

### 수동 테스트 체크리스트

- [ ] 초기 로드시 기본 로케일(en) 적용
- [ ] 언어 전환시 즉시 UI 변경
- [ ] 새로고침 후 선택 언어 유지
- [ ] Server/Client Components 모두 번역 동작

### 자동화 테스트

```bash
pnpm test
```

- NextIntlClientProvider로 컴포넌트 래핑하여 테스트

---

## 주의사항

1. **온보딩 챗봇**: 동적 메시지 생성 로직에서 `t()` 함수 사용 필요
2. **Toast 메시지**: useToast 훅에서 번역 함수 접근 방법 검토
3. **API 에러 메시지**: 백엔드 응답은 별도 처리 필요
4. **번역 키 누락**: TypeScript 설정으로 빌드 시 오류 감지 권장
