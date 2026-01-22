# 백엔드 코드 리뷰 보고서

**리뷰 일시**: 2026-01-22
**리뷰 대상**: `src/app/` 디렉토리 (frontend-poc 제외)
**리뷰어**: Claude Code (code-reviewer agent)

---

## 📊 종합 요약

| 모듈 | 품질 점수 | 머지 가능 여부 | 주요 이슈 |
|------|----------|---------------|----------|
| scheduler/ | 7.5/10 | 조건부 | DB 트랜잭션, asyncio 패턴 |
| vector_db/ | 8.5/10 | 조건부 | 스레드 안전성, 중복 조회 |
| processors/ | 8.5/10 | 조건부 | 토큰 제한, 가중치 검증 |
| email/ | 8.0/10 | 조건부 | SMTP 보안, 동적 속성 |
| api/routers/ | 7.5/10 | 조건부 | Import 위치, asyncio.run |
| db/ | 7.5/10 | 조건부 | CRUD 중복, 트랜잭션 롤백 |
| collectors/ | 8.0/10 | 조건부 | datetime.utcnow, RateLimiter |
| core/ | 7.5/10 | 조건부 | JWT 기본값, 에러 처리 |
| llm/ | 7.5/10 | 조건부 | 재시도 로직, API 키 검증 |
| api/schemas/ | 8.0/10 | 조건부 | Import 경로, sort_by 검증 |
| utils/ | 3.0/10 | 아니오 | 데드 코드 (삭제 권장) |

**전체 평균**: 7.4/10

---

## 🔴 심각도 높음 - 필수 수정 사항

### 1. scheduler/ - DB 트랜잭션 관리 미흡
- **위치**: `tasks.py` 전체
- **문제**: 에러 발생 시 명시적 `db.rollback()` 누락으로 부분 커밋 가능
- **권장**: try-except-finally 패턴에서 rollback 추가

### 2. scheduler/ - asyncio.run() 남용
- **위치**: `tasks.py:32, 38, 45, 52, 103...`
- **문제**: 매번 새 이벤트 루프 생성으로 성능 저하
- **권장**: async 함수로 전환하고 단일 이벤트 루프 사용

### 3. vector_db/ - zip strict=False 사용
- **위치**: `operations.py:193`
- **문제**: 리스트 길이 불일치 시 데이터 손실 가능
- **권장**: `strict=True`로 변경

### 4. vector_db/ - 스레드 안전성 부재
- **위치**: `client.py:260-273`
- **문제**: 싱글톤에 락 없음, 멀티스레드에서 race condition
- **권장**: `threading.Lock()` 추가

### 5. processors/ - 토큰 제한 하드코딩
- **위치**: `embedder.py:32`
- **문제**: 모델별 토큰 제한이 다름
- **권장**: 모델별 설정으로 분리

### 6. email/ - SMTP 보안 설정 부족
- **위치**: `sender.py:94-101`
- **문제**: TLS 인증서 검증, timeout 미설정
- **권장**: `validate_certs=True`, `timeout=30` 추가

### 7. api/routers/ - Import 문이 함수 내부에 위치
- **위치**: `articles.py:187, 275`, `feedback.py:52, 306, 358`
- **문제**: PEP 8 위반, 성능 저하
- **권장**: 파일 상단으로 이동

### 8. api/routers/ - asyncio.run() 사용
- **위치**: `auth.py:56`
- **문제**: FastAPI는 이미 async 컨텍스트 제공
- **권장**: `async def`로 변경 후 `await` 직접 사용

### 9. db/ - CRUD 코드 중복
- **위치**: `crud.py` vs `crud/*.py`
- **문제**: 동일 기능이 두 곳에 존재, 로직 불일치
- **권장**: `crud.py` 삭제 또는 deprecated 처리

### 10. db/ - 트랜잭션 롤백 처리 부재
- **위치**: 모든 CRUD 함수
- **문제**: commit 실패 시 일관성 문제
- **권장**: try-except에서 rollback 추가

### 11. collectors/ - datetime.utcnow() Deprecated
- **위치**: `base.py:30`
- **문제**: Python 3.12부터 deprecated
- **권장**: `datetime.now(timezone.utc)` 사용

### 12. core/ - JWT SECRET 기본값 보안 취약점
- **위치**: `config.py:68`
- **문제**: 프로덕션에서 기본값 사용 시 치명적
- **권장**: 기본값 제거 또는 환경별 검증 추가

### 13. llm/ - 재시도 로직 부재
- **위치**: `client.py:108-134`
- **문제**: API 호출 실패 시 즉시 예외
- **권장**: tenacity로 exponential backoff 구현

### 14. api/schemas/ - SQL Injection 위험
- **위치**: `articles.py:154-157`
- **문제**: `sort_by` 필드에 제한 없음
- **권장**: `Literal["collected_at", "importance_score", "published_at"]` 사용

### 15. utils/ - 데드 코드
- **위치**: `src/app/utils/` 전체
- **문제**: 프로젝트에서 전혀 사용되지 않음
- **권장**: 디렉토리 전체 삭제

---

## 🟡 심각도 중간 - 권장 수정 사항

### scheduler/
- 로깅 레벨 일관성 부족
- 메타데이터 필드명 불일치 (`metadata` vs `article_metadata`)
- 유니파이드 태스크의 메모리 관리 개선 필요
- 타입 힌팅 불완전
- 매직 넘버 하드코딩

### vector_db/
- `RuntimeError` 대신 커스텀 예외 클래스 사용
- `find_similar_articles`의 중복 벡터 조회 제거
- `collected_at` 인덱스 타입 문서화

### processors/
- heapq.nlargest() 사용으로 정렬 최적화
- 가중치 검증 로직 추가
- 하드코딩된 딜레이 설정화

### email/
- selection.py의 `_semantic_score` 동적 속성 제거
- asyncio.run 이벤트 루프 충돌 해결
- VectorOperations 캡슐화 개선
- 요약문 잘림 로직 개선

### api/routers/
- 한국어 주석 추가 (프로젝트 표준)
- UUID 비교 시 문자열 변환 제거
- import 경로 통일 (`src.app` → `app`)

### db/
- 쿼리 스타일 통일 (`select()` vs `query()`)
- 페이지네이션 반환 타입 일관성
- 기본값 불일치 (`limit=100` vs `limit=20`)
- N+1 쿼리 대응 (joinedload 추가)

### collectors/
- 재시도 예외 타입 범위 축소
- API별 별도 RateLimiter 사용
- Serper 응답 파싱 시 로깅 강화

### core/
- API 키 검증 로직 추가
- prompts.py의 format_prompt 예외 처리 개선
- retry.py 중복 import 제거

### llm/
- 에러 타입 세분화 (LLMRateLimitError 등)
- API 키 초기화 시 검증
- 타입 힌팅 개선 (overload 사용)

### api/schemas/
- Pydantic v2 `model_config` 방식으로 통일
- `info_types` 합계 검증 추가
- `feedback.py`의 max_length 불일치 수정
- Import 경로를 상대 경로로 변경

---

## 🟢 심각도 낮음 - 선택적 개선 사항

### 전체 공통
- 한국어/영어 주석 혼용 → 한국어로 통일
- 라인 길이 105자 제한 일부 초과
- Docstring 스타일 일관성
- 불필요한 `pass` 문 제거

### 모듈별
- **scheduler/**: 이모지 로깅 가이드라인 정립, 중복 코드 DRY 원칙 적용
- **vector_db/**: 주석 처리된 예시 코드 별도 문서화
- **processors/**: `get_embedder()` __all__에 추가
- **email/**: 매직 링크 템플릿화, PII 마스킹 로깅
- **api/routers/**: Query 파라미터 description 한국어화
- **collectors/**: URL 상수화, `__all__` 완성
- **core/**: 토큰 타입 상수화
- **api/schemas/**: Enum 활용 고려

---

## 📈 개선 로드맵

### Phase 1: 즉시 수정 (1주차)
1. `utils/` 디렉토리 삭제
2. JWT_SECRET_KEY 보안 강화
3. `datetime.utcnow()` → `datetime.now(timezone.utc)`
4. SMTP 보안 설정 추가
5. DB 트랜잭션 롤백 추가
6. Import 문 파일 상단으로 이동

### Phase 2: 단기 개선 (2주차)
1. asyncio.run() 패턴 개선
2. 재시도 로직 추가 (llm, collectors)
3. CRUD 중복 제거
4. 스레드 안전성 확보
5. 타입 힌팅 강화

### Phase 3: 중기 개선 (3-4주차)
1. 커스텀 예외 클래스 도입
2. 성능 최적화 (heapq, 캐싱)
3. 한국어 주석 통일
4. 테스트 커버리지 확대

---

## 💡 추가 제안

### 아키텍처
- Circuit Breaker 패턴 적용 (외부 API 장애 대응)
- 데드 레터 큐 (DLQ) 패턴 도입
- 성능 메트릭 수집 (Prometheus)

### 모니터링
- 슬로우 쿼리 로깅
- LLM 토큰 사용량 추적
- 이메일 전송률 모니터링

### 테스트
- 통합 테스트 확대
- Mock API 응답을 사용한 단위 테스트
- 엣지 케이스 테스트 추가

### 보안
- 토큰 블랙리스트 구현
- API 키 암호화 저장
- Rate Limiting 구현

---

## 📝 결론

전반적으로 **잘 구조화된 코드베이스**입니다. 특히 다음 부분이 우수합니다:
- 명확한 모듈 분리와 책임 분리
- 일관된 타입 힌팅
- 상세한 문서화 (docstring)
- 비동기 처리 및 병렬화

주요 개선 영역:
1. **보안**: JWT 기본값, SMTP 설정, SQL Injection 방지
2. **안정성**: 트랜잭션 관리, 재시도 로직, 에러 처리
3. **성능**: asyncio 패턴, 쿼리 최적화
4. **유지보수성**: 코드 중복 제거, 일관성 향상

위 필수 수정 사항들을 반영하면 **프로덕션 환경에 배포 가능한 수준**이 될 것입니다.
