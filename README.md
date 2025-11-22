# AI Research curator

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

- Python 3.12.12 (고정 버전)
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




## 작성자

- KMYU (sguys99@gmail.com)
