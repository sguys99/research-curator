# Scheduler 상태 공유 + 작업 내역 기록 (방법 B)

## Context

대시보드에서 스케줄러가 항상 "Paused"로 표시되는 버그. API 서버와 스케줄러가 별도 프로세스로 실행되어 `scheduler.running` 상태를 공유할 수 없음. 프로세스 분리를 유지하면서 DB를 통해 상태를 공유하고, 작업 실행 내역도 기록하여 모니터링 가능하게 한다.

---

## 단계 1: DB 모델 추가

**파일**: `src/app/db/models.py`

### 1-1. `scheduler_heartbeat` 테이블
스케줄러 프로세스의 생존 여부를 확인하는 heartbeat.

```python
class SchedulerHeartbeat(Base):
    __tablename__ = "scheduler_heartbeat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Seoul")
```
- 단일 행 (id=1)으로 관리
- 스케줄러가 30초마다 `last_heartbeat` 갱신
- API 서버는 `last_heartbeat`이 60초 이내인지 확인 → Running/Paused 판단

### 1-2. `scheduler_runs` 테이블
작업 실행 내역 기록.

```python
class SchedulerRun(Base):
    __tablename__ = "scheduler_runs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    job_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
        # "running" | "completed" | "failed"
    collected_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

---

## 단계 2: Alembic 마이그레이션

```bash
alembic revision --autogenerate -m "Add scheduler_heartbeat and scheduler_runs tables"
alembic upgrade head
```

---

## 단계 3: CRUD 작성

**새 파일**: `src/app/db/crud/scheduler.py`

기존 CRUD 패턴(`_commit_or_rollback`, `select()` 스타일)을 따라 작성:

- `upsert_heartbeat(db)` — heartbeat 갱신 (INSERT ON CONFLICT UPDATE)
- `get_heartbeat(db)` → `SchedulerHeartbeat | None`
- `mark_scheduler_stopped(db)` — `is_running=False` 설정
- `create_run(db, job_id, job_name)` → `SchedulerRun` (status="running")
- `update_run_progress(db, run_id, **counts)` — 카운터 업데이트
- `complete_run(db, run_id, status, error_message=None)` — 완료/실패 처리
- `get_recent_runs(db, limit=10)` → `list[SchedulerRun]`
- `get_latest_run(db, job_id)` → `SchedulerRun | None`

---

## 단계 4: 스케줄러 프로세스 수정

**파일**: `src/app/scheduler/main.py`

### 4-1. Heartbeat 잡 추가
`setup_jobs()`에 30초 간격 heartbeat 잡 등록:

```python
scheduler.add_job(
    func=heartbeat_task,
    trigger=IntervalTrigger(seconds=30),
    id="scheduler_heartbeat",
    name="Scheduler Heartbeat",
    replace_existing=True,
)
```

### 4-2. 시작/종료 시 DB 상태 갱신
- `start_scheduler()`: heartbeat 레코드 생성 (`is_running=True`, `started_at=now`)
- `stop_scheduler()`: `mark_scheduler_stopped()` 호출

### 4-3. `get_scheduler_status()` 수정
DB에서 heartbeat을 읽어 상태 판단:

```python
def get_scheduler_status() -> dict:
    heartbeat = crud.get_heartbeat(db)
    is_alive = (
        heartbeat is not None
        and heartbeat.is_running
        and (now - heartbeat.last_heartbeat).total_seconds() < 60
    )
    ...
```

**파일**: `src/app/scheduler/tasks.py`

### 4-4. 태스크에 실행 내역 기록 추가
`unified_collect_and_send_task` 시작/종료 시:

```python
run = crud.create_run(db, "unified_collect_send", "Unified Collect & Send")
try:
    # ... 기존 로직 ...
    crud.update_run_progress(db, run.id, collected_count=N, ...)
    crud.complete_run(db, run.id, status="completed")
except Exception as e:
    crud.complete_run(db, run.id, status="failed", error_message=str(e))
```

---

## 단계 5: API 엔드포인트 수정/추가

**파일**: `src/app/api/routers/scheduler.py`

### 5-1. `GET /scheduler/status` 수정
기존: `scheduler.running` (in-process) → **변경**: DB heartbeat 기반

### 5-2. 새 엔드포인트 추가
- `GET /scheduler/runs` — 최근 실행 내역 목록
- `GET /scheduler/runs/latest` — 가장 최근 실행 상태

**파일**: `src/app/api/schemas/scheduler.py`
- `SchedulerRunResponse` 스키마 추가
- `SchedulerRunListResponse` 스키마 추가
- `SchedulerStatusResponse` 수정 (heartbeat 기반 필드)

---

## 단계 6: 프론트엔드 (변경 최소화)

**기존 로직 유지**: `schedulerSummary.running` → "Running" / "Paused" 표시는 그대로.
API 응답의 `running` 필드가 이제 DB heartbeat 기반으로 정확한 값을 반환하므로 프론트엔드 수정 불필요.

(작업 내역 표시 UI는 이번 범위에서 제외 — 추후 대시보드에 추가 가능)

---

## 수정 대상 파일 요약

| 파일 | 작업 |
|------|------|
| `src/app/db/models.py` | `SchedulerHeartbeat`, `SchedulerRun` 모델 추가 |
| `src/app/db/crud/scheduler.py` | **신규** — heartbeat/run CRUD |
| `src/app/db/crud/__init__.py` | scheduler CRUD export 추가 |
| `src/app/scheduler/main.py` | heartbeat 잡, 시작/종료 DB 갱신, 상태 조회 수정 |
| `src/app/scheduler/tasks.py` | 태스크에 실행 내역 기록 추가 |
| `src/app/api/routers/scheduler.py` | status 엔드포인트 수정, runs 엔드포인트 추가 |
| `src/app/api/schemas/scheduler.py` | Run 관련 스키마 추가 |
| `alembic/versions/` | 마이그레이션 파일 자동 생성 |

## 검증 방법

1. `docker compose up -d` → PostgreSQL 시작
2. `alembic upgrade head` → 마이그레이션 적용
3. `uvicorn src.app.api.main:app --reload` → API 서버 시작
4. `python -m src.app.scheduler.main` → 스케줄러 별도 시작
5. `curl localhost:8000/api/scheduler/status` → `"running": true` 확인
6. 대시보드에서 "Running" + 녹색 점 확인
7. 스케줄러 프로세스 종료 → 60초 후 "Paused" 전환 확인
8. `curl localhost:8000/api/scheduler/runs` → 실행 내역 확인
