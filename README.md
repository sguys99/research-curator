# ML Project Template

AI 프로젝트를 위한 포괄적인 머신러닝 프로젝트 템플릿으로, 최신 Python 도구와 모범 사례를 적용했습니다.

## 주요 기능

- 🚀 `uv`를 사용한 빠른 의존성 관리
- 🎯 YAML 설정 기반 아키텍처
- 📊 멀티페이지 네비게이션이 있는 Streamlit 데모 애플리케이션
- 📓 Jupyter 노트북 템플릿
- 🔧 코드 품질 관리를 위한 Pre-commit hooks
- 🎨 Ruff를 사용한 코드 포맷팅 (black 호환)
- 🏗️ 구조화된 데이터 파이프라인 (raw/intermediate/processed)
- 🔄 재현 가능성을 위한 랜덤 시드 관리 유틸리티

## 사전 요구사항

- Python 3.12.9 (고정 버전)
- `uv` 패키지 매니저

## 빠른 시작

### 1. 환경 설정

**개발 환경** (pre-commit hooks 및 개발 도구 포함):
```bash
make init-dev
# 또는
bash install.sh --dev
```

**프로덕션 환경**:
```bash
make init
# 또는
bash install.sh
```

**사용 가능한 모든 명령어 보기**:
```bash
make help
```

### 2. 환경 변수 설정

템플릿에서 환경 파일 생성:
```bash
cp .env.example .env
cp .env.dev.example .env.dev
```

### 3. 가상 환경 활성화

```bash
source .venv/bin/activate
```

### 4. 데모 애플리케이션 실행

```bash
cd demo
streamlit run main.py
```

**기본 로그인 정보**:
- 사용자명: `admin`
- 비밀번호: `admin`

> ⚠️ **주의**: 개발용으로 하드코딩된 인증 정보입니다. 배포 전에 환경 변수로 변경해야 합니다.

## 프로젝트 구조

```
ml-project-template/
├── src/my_ml/                # 메인 패키지
│   └── utils/                # 유틸리티 모듈
│       ├── config_loader.py  # YAML 설정 로더
│       ├── path.py          # 경로 상수
│       └── settings.py      # 랜덤 시드 유틸리티
├── configs/                  # YAML 설정 파일
│   ├── data.yaml            # 데이터 경로 설정
│   ├── feature.yaml         # 피처 엔지니어링 설정
│   ├── model.yaml           # 모델 설정
│   └── train.yaml           # 학습 파이프라인 설정
├── demo/                     # Streamlit 데모 애플리케이션
│   ├── main.py              # 메인 진입점
│   ├── page_utils.py        # 로그인/로그아웃 유틸리티
│   ├── home/                # 홈 페이지
│   ├── app1/                # 애플리케이션 페이지 1
│   └── app2/                # 애플리케이션 페이지 2
├── data/                     # 데이터 디렉토리 (git-ignored)
│   ├── raw/                 # 원시 데이터
│   ├── intermediate/        # 중간 처리 결과
│   └── processed/           # 최종 처리된 데이터셋
├── notebooks/                # Jupyter 노트북
│   └── template.ipynb       # 노트북 템플릿
└── logs/                     # 로그 파일 (git-ignored)
```

## 주요 프레임워크 및 라이브러리

### 머신러닝
- **딥러닝**: PyTorch, Lightning
- **전통적 ML**: scikit-learn, XGBoost, statsmodels
- **최적화**: Optuna
- **해석가능성**: SHAP

### LLM & GenAI
- LangChain, LangGraph, LiteLLM
- AWS Bedrock 통합 (langchain-aws)
- 관찰가능성을 위한 Traceloop SDK

### 데이터 처리
- pandas, polars, NumPy, PyArrow

### 클라우드 서비스
- **AWS**: boto3, Amazon Transcribe
- **Azure**: Cognitive Services Speech
- **GCP**: AI Platform

### 웹 & API
- FastAPI, Streamlit
- Streamlit AgGrid, Streamlit Modal

### 데이터베이스
- MongoDB (pymongo, motor)
- PostgreSQL (pg8000, SQLAlchemy)
- Redis, OpenSearch, Vespa

### 관찰가능성
- OpenTelemetry instrumentation
- Prometheus metrics

## 사용법

### 설정 파일 로드

```python
from my_ml.utils.config_loader import load_config
from my_ml.utils.path import DATA_CONFIG_PATH, MODEL_CONFIG_PATH

# 데이터 설정 로드
data_config = load_config(DATA_CONFIG_PATH)

# 모델 설정 로드
model_config = load_config(MODEL_CONFIG_PATH)
```

### 경로 관리

모든 프로젝트 경로는 [src/my_ml/utils/path.py](src/my_ml/utils/path.py)에 중앙 집중화되어 있습니다:

```python
from my_ml.utils.path import (
    REPO_ROOT,
    DATA_PATH,
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    CONFIG_PATH,
    NOTEBOOK_PATH
)
```

### 재현 가능성

재현 가능한 결과를 위한 랜덤 시드 설정:

```python
from my_ml.utils.settings import set_random_seed

# random, numpy, torch의 시드 설정
set_random_seed(random_seed=42, use_torch=True)
```

## 코드 품질

### Pre-commit Hooks

Pre-commit은 다음과 같이 설정되어 있습니다:
- Ruff (포맷팅 및 린팅)
- trailing-whitespace, end-of-file-fixer
- check-added-large-files (최대 30MB)
- requirements-txt-fixer
- add-trailing-comma

`--dev` 설정을 사용하면 커밋 시 자동으로 훅이 실행됩니다.

### 수동 포맷팅

```bash
make format  # ruff format 실행
```

**포맷팅 규칙**:
- 라인 길이: 105자
- 따옴표 스타일: 쌍따옴표
- import 정렬: isort 호환

## 개발 워크플로우

1. **환경 활성화**: `source .venv/bin/activate`
2. **새 기능 생성**: `src/my_ml/utils/`에 유틸리티 추가
3. **설정 변경**: `configs/`의 YAML 파일 수정
4. **새 노트북**: [notebooks/template.ipynb](notebooks/template.ipynb)를 시작점으로 사용
5. **의존성 추가**: `uv add <package>`
6. **코드 포맷**: `make format`
7. **데모 실행**: `cd demo && streamlit run main.py`

## 의존성 추가하기

```bash
# 런타임 의존성 추가
uv add <package>

# 개발 의존성 추가
uv add --dev <package>

# 의존성 동기화
uv sync
```

## 노트북 템플릿

Jupyter 노트북 템플릿에는 다음이 포함되어 있습니다:
- 작성자명 및 날짜 필드
- 수정 이력 섹션
- 자동 `.env` 로딩

새 노트북을 시작할 때는 [notebooks/template.ipynb](notebooks/template.ipynb)를 복사하세요.


## 사용 가능한 Make 명령어

`make help`를 실행하면 모든 사용 가능한 명령어를 볼 수 있습니다:
- `make init` - 프로덕션 환경 초기화
- `make init-dev` - 개발 환경 초기화
- `make format` - ruff로 코드 포맷팅
- `make clean` - 임시 파일 정리
- `make help` - 도움말 메시지 표시


## 작성자

- KMYU (sguys99@gmail.com)
