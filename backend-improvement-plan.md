# 백엔드 코드 개선 계획

**작성일**: 2026-01-22
**기반 문서**: code-review-report.md
**대상**: `src/app/` 디렉토리

---

## 개선 원칙

1. **우선순위**: 보안 > 안정성 > 성능 > 유지보수성
2. **접근 방식**: 작은 단위로 분리하여 단계적 적용
3. **검증**: 각 단계 완료 후 테스트 실행

---

## Phase 1: 즉시 수정 (보안 및 데드 코드)

### 1.1 utils/ 디렉토리 삭제
- **파일**: `src/app/utils/` 전체
- **이유**: 프로젝트에서 전혀 사용되지 않는 데드 코드
- **작업**:
  1. utils 모듈의 import 여부 최종 확인
  2. 디렉토리 전체 삭제
- **위험도**: 낮음

### 1.2 JWT SECRET 기본값 보안 강화
- **파일**: `src/app/core/config.py:68`
- **문제**: 프로덕션에서 기본값 사용 시 치명적 보안 취약점
- **작업**:
  1. 기본값 제거
  2. 환경 변수 필수 검증 추가
  3. 개발/프로덕션 환경별 검증 로직 추가
- **위험도**: 높음 (보안)

### 1.3 datetime.utcnow() Deprecated 수정
- **파일**: `src/app/collectors/base.py:30`
- **문제**: Python 3.12부터 deprecated
- **작업**:
  1. `datetime.utcnow()` → `datetime.now(timezone.utc)` 변경
  2. 관련 모든 파일 검색하여 일괄 수정
- **위험도**: 낮음

### 1.4 SMTP 보안 설정 추가
- **파일**: `src/app/email/sender.py:94-101`
- **문제**: TLS 인증서 검증, timeout 미설정
- **작업**:
  1. `validate_certs=True` 설정 추가
  2. `timeout=30` 설정 추가
  3. SSL/TLS 컨텍스트 명시적 설정
- **위험도**: 중간

### 1.5 SQL Injection 위험 방지
- **파일**: `src/app/api/schemas/articles.py:154-157`
- **문제**: `sort_by` 필드에 제한 없음
- **작업**:
  1. `Literal["collected_at", "importance_score", "published_at"]` 타입으로 변경
  2. 관련 쿼리에서 검증 로직 확인
- **위험도**: 높음 (보안)

### 1.6 Import 문 파일 상단으로 이동
- **파일**:
  - `src/app/api/routers/articles.py:187, 275`
  - `src/app/api/routers/feedback.py:52, 306, 358`
- **문제**: PEP 8 위반, 성능 저하
- **작업**:
  1. 함수 내부 import를 파일 상단으로 이동
  2. 순환 참조 발생 시 대안 검토
- **위험도**: 중간

---

## Phase 2: 트랜잭션 및 에러 처리 개선

### 2.1 DB 트랜잭션 롤백 추가
- **파일**:
  - `src/app/scheduler/tasks.py` 전체
  - `src/app/db/crud/*.py` 모든 CRUD 함수
- **문제**: commit 실패 시 rollback 누락으로 데이터 일관성 문제
- **작업**:
  1. try-except-finally 패턴 적용
  2. except 블록에 `db.rollback()` 추가
  3. 트랜잭션 컨텍스트 매니저 도입 검토
- **위험도**: 중간

### 2.2 CRUD 코드 중복 제거
- **파일**:
  - `src/app/db/crud.py` vs `src/app/db/crud/*.py`
- **문제**: 동일 기능이 두 곳에 존재, 로직 불일치 가능
- **작업**:
  1. 양쪽 함수 비교 분석
  2. `crud.py`를 deprecated 처리 또는 삭제
  3. 기존 참조를 `crud/*.py`로 마이그레이션
- **위험도**: 중간

---

## Phase 3: asyncio 패턴 개선

### 3.1 asyncio.run() 남용 수정
- **파일**:
  - `src/app/scheduler/tasks.py:32, 38, 45, 52, 103...`
  - `src/app/api/routers/auth.py:56`
- **문제**: 매번 새 이벤트 루프 생성으로 성능 저하
- **작업**:
  1. 스케줄러 태스크를 async 함수로 전환
  2. 단일 이벤트 루프에서 실행되도록 구조 변경
  3. FastAPI 라우터에서 `await` 직접 사용
- **위험도**: 높음 (구조 변경)

---

## Phase 4: 스레드 안전성 및 데이터 무결성

### 4.1 Vector DB 스레드 안전성 확보
- **파일**: `src/app/vector_db/client.py:260-273`
- **문제**: 싱글톤에 락 없음, 멀티스레드에서 race condition
- **작업**:
  1. `threading.Lock()` 추가
  2. 더블 체크 락킹 패턴 적용
- **위험도**: 중간

### 4.2 zip strict=True 적용
- **파일**: `src/app/vector_db/operations.py:193`
- **문제**: 리스트 길이 불일치 시 데이터 손실 가능
- **작업**:
  1. `zip(..., strict=True)` 로 변경
  2. 예외 발생 시 적절한 에러 메시지 추가
- **위험도**: 낮음

---

## Phase 5: 재시도 로직 및 복원력 강화

### 5.1 LLM 클라이언트 재시도 로직 추가
- **파일**: `src/app/llm/client.py:108-134`
- **문제**: API 호출 실패 시 즉시 예외
- **작업**:
  1. tenacity 라이브러리 사용
  2. exponential backoff 구현
  3. 재시도 가능한 예외 타입 정의
- **위험도**: 중간

### 5.2 Collectors 재시도 로직 강화
- **파일**: `src/app/collectors/base.py`
- **문제**: 재시도 예외 타입이 너무 넓음
- **작업**:
  1. 재시도 대상 예외 타입 구체화
  2. API별 별도 RateLimiter 설정
- **위험도**: 낮음

---

## Phase 6: 토큰 및 설정 관리 개선

### 6.1 토큰 제한 설정화
- **파일**: `src/app/processors/embedder.py:32`
- **문제**: 모델별 토큰 제한이 하드코딩됨
- **작업**:
  1. 모델별 토큰 제한 설정 파일로 분리
  2. 동적 토큰 제한 로드 로직 구현
- **위험도**: 낮음

### 6.2 API 키 검증 로직 추가
- **파일**:
  - `src/app/core/config.py`
  - `src/app/llm/client.py`
- **작업**:
  1. 초기화 시 API 키 유효성 검증
  2. 빈 값 또는 잘못된 형식 체크
- **위험도**: 낮음

---

## Phase 7: 중간 우선순위 개선

### 7.1 커스텀 예외 클래스 도입
- **파일**: `src/app/vector_db/` 전체
- **문제**: `RuntimeError` 등 일반 예외 사용
- **작업**:
  1. 도메인별 예외 클래스 정의
  2. 기존 예외를 커스텀 예외로 교체
- **위험도**: 낮음

### 7.2 Email 모듈 개선
- **파일**:
  - `src/app/email/selection.py`
- **문제**: `_semantic_score` 동적 속성 사용
- **작업**:
  1. 동적 속성 제거
  2. 명시적 데이터 클래스 또는 딕셔너리 사용
- **위험도**: 낮음

### 7.3 쿼리 스타일 통일
- **파일**: `src/app/db/crud/*.py`
- **문제**: `select()` vs `query()` 혼용
- **작업**:
  1. SQLAlchemy 2.0 스타일 (`select()`)로 통일
  2. N+1 쿼리 대응 (joinedload 추가)
- **위험도**: 중간

---

## Phase 8: 낮은 우선순위 개선

### 8.1 한국어 주석 통일
- **파일**: 전체
- **작업**: 영어/한국어 혼용 → 한국어 통일

### 8.2 타입 힌팅 강화
- **파일**: 전체
- **작업**: 불완전한 타입 힌팅 보완

### 8.3 Pydantic v2 스타일 통일
- **파일**: `src/app/api/schemas/*.py`
- **작업**: `model_config` 방식으로 통일

### 8.4 Import 경로 통일
- **파일**: 전체
- **작업**: `src.app` → `app` 또는 상대 경로로 통일

---

## 체크리스트

### Phase 1 (즉시)
- [x] 1.1 utils/ 디렉토리 삭제
- [x] 1.2 JWT SECRET 보안 강화
- [x] 1.3 datetime.utcnow() 수정
- [x] 1.4 SMTP 보안 설정
- [x] 1.5 SQL Injection 방지
- [x] 1.6 Import 문 이동

### Phase 2 (트랜잭션)
- [x] 2.1 DB 롤백 추가
- [x] 2.2 CRUD 중복 제거

### Phase 3 (asyncio)
- [x] 3.1 asyncio.run() 패턴 개선

### Phase 4 (스레드 안전성)
- [x] 4.1 Vector DB 락 추가
- [x] 4.2 zip strict=True

### Phase 5 (재시도)
- [x] 5.1 LLM 재시도 로직
- [x] 5.2 Collectors 재시도 개선

### Phase 6 (설정)
- [x] 6.1 토큰 제한 설정화
- [x] 6.2 API 키 검증

### Phase 7 (중간)
- [x] 7.1 커스텀 예외
- [x] 7.2 Email 동적 속성 제거
- [x] 7.3 쿼리 스타일 통일

### Phase 8 (낮음)
- [ ] 8.1 한국어 주석
- [ ] 8.2 타입 힌팅
- [ ] 8.3 Pydantic v2
- [ ] 8.4 Import 경로

---

## 참고 사항

- 각 Phase는 독립적으로 실행 가능
- Phase 1은 보안 이슈이므로 우선 적용 권장
- Phase 3 (asyncio)는 구조 변경이 크므로 신중히 진행
- 모든 변경 후 테스트 실행 필수: `pytest tests/`
