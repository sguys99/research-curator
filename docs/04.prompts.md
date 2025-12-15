# 프롬프트 관리 시스템

LLM 프롬프트를 중앙 집중식으로 관리하는 시스템입니다.

## 📁 파일 구조

```
configs/
  └── prompts.yaml          # 모든 LLM 프롬프트 정의

src/app/core/
  └── prompts.py            # 프롬프트 로드 및 관리 유틸리티

notebooks/
  └── test_prompts.ipynb    # 프롬프트 시스템 테스트
```

## 🎯 주요 기능

### 1. 프롬프트 카테고리

| 카테고리 | 설명 | 하위 카테고리 |
|---------|------|-------------|
| `summarize` | 아티클 요약 생성 | korean.short/medium/long, english.short/medium |
| `evaluate_importance` | 중요도 평가 (0.0-1.0) | - |
| `classify_category` | 카테고리 분류 | - |
| `extract_metadata` | 메타데이터 추출 | - |
| `onboarding` | 온보딩 챗봇 | - |
| `common` | 공통 설정 | - |

### 2. 요약 생성 옵션

**한국어 요약**:
- `short`: 2-3문장 (간결한 요약)
- `medium`: 3-5문장 (핵심 아이디어 + 주요 발견)
- `long`: 6-8문장 (배경, 방법론, 결과, 의미)

**영어 요약**:
- `short`: 2-3 sentences
- `medium`: 3-5 sentences

### 3. 중요도 평가 기준

| 기준 | 설명 | 가중치 |
|-----|------|--------|
| `innovation` | 혁신성 (새로운 아이디어, 획기적 개선) | 30% |
| `relevance` | 관련성 (AI 분야 관련성, 실용적 가치) | 25% |
| `impact` | 영향력 (학계/산업계 영향, 응용 가능성) | 30% |
| `timeliness` | 시의성 (현재 중요도, 최신 트렌드) | 15% |

### 4. 분류 카테고리

- `paper`: 학술 논문 (arXiv, 학회, 저널)
- `news`: 뉴스 기사 (언론사, 테크 블로그)
- `report`: 연구 리포트 (기업, 연구소 보고서)
- `blog`: 개인 블로그 포스트
- `other`: 기타

## 🚀 사용법

### 기본 사용

```python
from src.app.core.prompts import get_prompt_manager, build_messages

# PromptManager 인스턴스 가져오기
manager = get_prompt_manager()

# 메시지 빌드
messages = manager.build_messages(
    "summarize",              # 카테고리
    "korean.medium",          # 하위 카테고리
    title="논문 제목",
    content="논문 내용..."
)

# LLM API 호출
# response = llm_client.chat_completion(messages=messages)
```

### 편의 함수 사용

```python
from src.app.core.prompts import build_messages, get_prompt

# 메시지 빌드 (간단한 방법)
messages = build_messages(
    "evaluate_importance",
    title="...",
    content="...",
    metadata="{...}"
)

# 특정 프롬프트 가져오기
default_lang = get_prompt("common.default_language")  # "ko"
categories = get_prompt("classify_category.categories")  # ["paper", "news", ...]
```

### 고급 사용

```python
# 카테고리 목록
categories = manager.get_categories()
# ['summarize', 'evaluate_importance', 'classify_category', ...]

# 요약 길이 옵션
lengths = manager.get_summary_lengths()
# ['short', 'medium', 'long']

# 평가 기준 및 가중치
criteria = manager.get_evaluation_criteria()
weights = manager.get_evaluation_weights()
# criteria = ['innovation', 'relevance', 'impact', 'timeliness']
# weights = {'innovation': 0.3, 'relevance': 0.25, ...}

# 프롬프트 재로드 (파일 수정 후)
manager.reload()
```

## 📝 프롬프트 추가/수정

### 1. 새 프롬프트 추가

`configs/prompts.yaml`에 추가:

```yaml
my_new_task:
  system: |
    당신은 전문가입니다.

  user_template: |
    다음을 처리하세요:
    제목: {title}
    내용: {content}
```

### 2. 프롬프트 사용

```python
messages = build_messages(
    "my_new_task",
    title="...",
    content="..."
)
```

### 3. 하위 카테고리가 있는 프롬프트

```yaml
my_task:
  option1:
    system: "..."
    user_template: "..."
  option2:
    system: "..."
    user_template: "..."
```

```python
messages = build_messages(
    "my_task",
    "option1",  # 하위 카테고리
    title="..."
)
```

## 🔍 프롬프트 템플릿 변수

템플릿에서 `{variable_name}` 형식으로 변수를 사용할 수 있습니다.

**요약 프롬프트 변수**:
- `{title}`: 아티클 제목
- `{content}`: 아티클 내용

**평가 프롬프트 변수**:
- `{title}`: 아티클 제목
- `{content}`: 아티클 내용
- `{metadata}`: 메타데이터 (JSON 문자열)

**분류 프롬프트 변수**:
- `{title}`: 아티클 제목
- `{content}`: 아티클 내용
- `{source_name}`: 소스 이름 (예: "arXiv")
- `{url}`: 원문 URL

## ⚙️ 설정

### 공통 설정

`configs/prompts.yaml`의 `common` 섹션:

```yaml
common:
  default_language: "ko"
  default_summary_length: "medium"

  error_messages:
    invalid_json: "LLM이 유효한 JSON을 반환하지 않았습니다."
    empty_response: "LLM 응답이 비어있습니다."
    rate_limit: "API rate limit에 도달했습니다."
    api_error: "LLM API 호출 중 오류가 발생했습니다."
```

## 🧪 테스트

### 단위 테스트

```bash
# 프롬프트 로더 테스트
python src/app/core/prompts.py
```

### Jupyter 노트북 테스트

```bash
# Jupyter 시작
jupyter notebook notebooks/test_prompts.ipynb
```

## 📊 API 응답 형식

### 중요도 평가 응답

```json
{
  "innovation": 0.85,
  "relevance": 0.90,
  "impact": 0.80,
  "timeliness": 0.75,
  "reasoning": "획기적인 Transformer 아키텍처를 제안...",
  "overall_score": 0.83
}
```

### 카테고리 분류 응답

```json
{
  "category": "paper",
  "confidence": 0.95,
  "keywords": ["Transformer", "Attention", "NMT"],
  "research_field": "Natural Language Processing",
  "sub_fields": ["Machine Translation", "Neural Networks"],
  "reasoning": "arXiv에 게재된 학술 논문..."
}
```

### 메타데이터 추출 응답

```json
{
  "authors": ["Ashish Vaswani", "Noam Shazeer"],
  "affiliations": ["Google Brain", "Google Research"],
  "publication_date": "2017-06-12",
  "technologies": ["Transformer", "Multi-Head Attention"],
  "datasets": ["WMT 2014", "English-German", "English-French"],
  "metrics": {
    "BLEU": "28.4",
    "training_time": "3.5 days"
  },
  "links": {
    "pdf": "https://arxiv.org/pdf/1706.03762"
  },
  "references": ["Neural Machine Translation", "Attention Mechanism"]
}
```

## ✅ 베스트 프랙티스

### 1. 싱글톤 패턴 사용

```python
# ✅ 권장: 싱글톤 인스턴스 재사용
from src.app.core.prompts import get_prompt_manager
manager = get_prompt_manager()

# ❌ 비권장: 매번 새 인스턴스 생성
from src.app.core.prompts import PromptManager
manager = PromptManager()  # 캐싱 안됨
```

### 2. 편의 함수 활용

```python
# ✅ 권장: 간결한 편의 함수
from src.app.core.prompts import build_messages
messages = build_messages("summarize", "korean.medium", ...)

# ❌ 비권장: 매번 manager 가져오기
from src.app.core.prompts import get_prompt_manager
manager = get_prompt_manager()
messages = manager.build_messages("summarize", ...)
```

### 3. 프롬프트 수정 시 재로드

```python
# 프롬프트 파일 수정 후
manager = get_prompt_manager()
manager.reload()  # 변경사항 반영
```

## 🔗 관련 문서

- [LLM Integration Guide](./LLM_INTEGRATION.md)
- [Processors Guide](./PROCESSORS.md)
- [API Documentation](./API.md)

## 📚 참고

### 프롬프트 엔지니어링 원칙

1. **명확성**: 명확하고 구체적인 지시
2. **예시**: Few-shot 예시 제공 (필요시)
3. **구조화**: JSON 등 명확한 출력 형식 지정
4. **일관성**: 동일한 용어와 형식 사용
5. **검증**: 실제 데이터로 프롬프트 품질 검증

### 프롬프트 개선 팁

- 요약 품질이 낮으면 `system` 프롬프트에 더 구체적인 가이드라인 추가
- 평가 점수가 일관성이 없으면 평가 기준을 더 세분화
- JSON 파싱 오류가 발생하면 `json_instruction` 추가
- 특정 도메인에 특화하려면 Few-shot 예시 추가

---

**작성일**: 2025-12-03
**버전**: 1.0.0
