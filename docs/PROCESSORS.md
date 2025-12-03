# 데이터 처리 모듈 (Processors)

LLM을 활용하여 수집된 아티클을 자동으로 처리하는 모듈입니다.

## 📋 목차

- [개요](#개요)
- [모듈 구성](#모듈-구성)
- [사용법](#사용법)
- [API 레퍼런스](#api-레퍼런스)
- [성능 최적화](#성능-최적화)
- [예제](#예제)

---

## 개요

Processors는 5개의 핵심 컴포넌트로 구성됩니다:

| 프로세서 | 기능 | 출력 |
|---------|------|------|
| **ArticleSummarizer** | 한국어/영어 요약 생성 | 요약 문자열 |
| **ImportanceEvaluator** | 중요도 평가 (LLM + 메타데이터) | 0.0-1.0 점수 |
| **ContentClassifier** | 카테고리 분류 + 메타데이터 추출 | 카테고리, 키워드 등 |
| **TextEmbedder** | 임베딩 벡터 생성 | 1536차원 벡터 |
| **ProcessingPipeline** | 통합 파이프라인 (모든 처리 자동화) | ProcessedArticle |

### 주요 특징

- ✅ **비동기 처리**: asyncio 기반 고성능
- ✅ **배치 처리**: 여러 아티클 동시 처리
- ✅ **에러 핸들링**: 부분 실패 허용
- ✅ **캐싱**: 임베딩 캐시로 비용 절감
- ✅ **타입 안전**: 완전한 타입 힌트

---

## 모듈 구성

```
src/app/processors/
├── __init__.py          # 패키지 초기화
├── summarizer.py        # 요약 생성
├── evaluator.py         # 중요도 평가
├── classifier.py        # 카테고리 분류
├── embedder.py          # 임베딩 생성
└── pipeline.py          # 통합 파이프라인
```

---

## 사용법

### 1. ArticleSummarizer

```python
from src.app.processors import ArticleSummarizer

# 초기화
summarizer = ArticleSummarizer(
    provider="openai",
    temperature=0.3  # 낮을수록 일관성↑
)

# 단일 요약
summary = await summarizer.summarize(
    title="Attention Is All You Need",
    content="We propose the Transformer...",
    language="ko",      # "ko" 또는 "en"
    length="medium"     # "short", "medium", "long"
)

# 배치 요약
articles = [
    {"title": "Paper 1", "content": "..."},
    {"title": "Paper 2", "content": "..."},
]
summaries = await summarizer.batch_summarize(
    articles,
    language="ko",
    length="short"
)
```

**요약 길이 옵션**:
- `short`: 2-3문장 (간결한 요약)
- `medium`: 3-5문장 (핵심 아이디어 + 주요 발견)
- `long`: 6-8문장 (배경, 방법론, 결과, 의미)

---

### 2. ImportanceEvaluator

```python
from src.app.processors import ImportanceEvaluator

# 초기화
evaluator = ImportanceEvaluator(
    provider="openai",
    temperature=0.2,
    llm_weight=0.7,        # LLM 평가 가중치
    metadata_weight=0.3    # 메타데이터 가중치
)

# 단일 평가
result = await evaluator.evaluate(
    title="GPT-4 Technical Report",
    content="GPT-4 is a large multimodal model...",
    metadata={
        "citations": 5000,
        "year": 2023,
        "source_name": "OpenAI"
    }
)

print(result["final_score"])  # 0.89
print(result["innovation"])   # 0.95
print(result["relevance"])    # 0.90
print(result["impact"])       # 0.85
print(result["timeliness"])   # 0.80
```

**평가 기준**:
- `innovation` (30%): 혁신성, 새로운 아이디어
- `relevance` (25%): AI 분야 관련성, 실용적 가치
- `impact` (30%): 학계/산업계 영향력
- `timeliness` (15%): 시의성, 최신 트렌드

**메타데이터 평가 요소**:
- 인용수 (citations)
- 출처 신뢰도 (source_name)
- 최신성 (year, publication_date)

---

### 3. ContentClassifier

```python
from src.app.processors import ContentClassifier

# 초기화
classifier = ContentClassifier(
    provider="openai",
    temperature=0.1  # 매우 낮게 설정 (일관성 극대화)
)

# 단일 분류
result = await classifier.classify(
    title="Attention Is All You Need",
    content="We propose the Transformer...",
    source_name="arXiv",
    url="https://arxiv.org/abs/1706.03762"
)

print(result["category"])         # "paper"
print(result["confidence"])       # 0.95
print(result["research_field"])   # "Natural Language Processing"
print(result["keywords"])         # ["Transformer", "Attention", "NMT"]
```

**카테고리**:
- `paper`: 학술 논문 (arXiv, 학회, 저널)
- `news`: 뉴스 기사 (언론사, 테크 블로그)
- `report`: 연구 리포트 (기업, 연구소 보고서)
- `blog`: 개인 블로그 포스트
- `other`: 기타

**반환 데이터**:
```python
{
    "category": "paper",
    "confidence": 0.95,
    "keywords": ["Transformer", "Attention"],
    "research_field": "Natural Language Processing",
    "sub_fields": ["Machine Translation", "Neural Networks"],
    "reasoning": "arXiv에 게재된 학술 논문..."
}
```

---

### 4. TextEmbedder

```python
from src.app.processors import TextEmbedder

# 초기화
embedder = TextEmbedder(
    use_cache=True  # 캐싱 활성화
)

# 단일 임베딩
embedding = await embedder.embed("Attention Is All You Need")
print(len(embedding))  # 1536

# 배치 임베딩
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = await embedder.batch_embed(texts)
print(len(embeddings))  # 3

# 아티클 임베딩 (제목 + 요약 + 내용)
embedding = await embedder.embed_article_async(
    title="GPT-4",
    content="GPT-4 is a large multimodal model...",
    summary="GPT-4는 대규모 멀티모달 모델입니다."
)
```

**캐시 관리**:
```python
# 캐시 크기 확인
print(embedder.get_cache_size())

# 캐시 초기화
embedder.clear_cache()
```

---

## API 레퍼런스

### ArticleSummarizer

#### `summarize(title, content, language, length, max_tokens) -> str`

단일 아티클 요약 생성

**Parameters**:
- `title` (str): 아티클 제목
- `content` (str): 아티클 내용
- `language` (Literal["ko", "en"]): 요약 언어 (기본: "ko")
- `length` (Literal["short", "medium", "long"]): 요약 길이 (기본: "medium")
- `max_tokens` (int): 최대 토큰 수 (기본: 500)

**Returns**: `str` - 요약 문자열

#### `batch_summarize(articles, language, length, max_tokens) -> List[str]`

여러 아티클 동시 요약

**Parameters**:
- `articles` (List[dict]): 아티클 리스트 `[{"title": "...", "content": "..."}, ...]`
- 나머지 파라미터는 `summarize()`와 동일

**Returns**: `List[str]` - 요약 문자열 리스트

---

### ImportanceEvaluator

#### `evaluate(title, content, metadata, max_tokens) -> Dict[str, float]`

단일 아티클 중요도 평가

**Parameters**:
- `title` (str): 아티클 제목
- `content` (str): 아티클 내용
- `metadata` (Optional[Dict[str, Any]]): 메타데이터 (기본: None)
- `max_tokens` (int): 최대 토큰 수 (기본: 500)

**Returns**: `Dict[str, float]`
```python
{
    "innovation": 0.0-1.0,
    "relevance": 0.0-1.0,
    "impact": 0.0-1.0,
    "timeliness": 0.0-1.0,
    "reasoning": "평가 근거",
    "llm_score": 0.0-1.0,
    "metadata_score": 0.0-1.0,
    "final_score": 0.0-1.0
}
```

---

### ContentClassifier

#### `classify(title, content, source_name, url, max_tokens) -> Dict[str, Any]`

단일 아티클 분류 및 메타데이터 추출

**Parameters**:
- `title` (str): 아티클 제목
- `content` (str): 아티클 내용
- `source_name` (str): 소스 이름 (기본: "")
- `url` (str): 원문 URL (기본: "")
- `max_tokens` (int): 최대 토큰 수 (기본: 500)

**Returns**: `Dict[str, Any]` (위 사용법 섹션 참조)

---

### TextEmbedder

#### `embed(text) -> List[float]`

단일 텍스트 임베딩 생성

**Parameters**:
- `text` (str): 임베딩할 텍스트

**Returns**: `List[float]` - 1536차원 벡터

#### `batch_embed(texts, batch_size) -> List[List[float]]`

여러 텍스트 동시 임베딩

**Parameters**:
- `texts` (List[str]): 텍스트 리스트
- `batch_size` (int): 배치 크기 (기본: 100)

**Returns**: `List[List[float]]` - 임베딩 벡터 리스트

---

## 성능 최적화

### 1. 병렬 처리

```python
import asyncio

# ❌ 순차 처리 (느림)
for article in articles:
    summary = await summarizer.summarize(...)

# ✅ 병렬 처리 (빠름)
summaries = await summarizer.batch_summarize(articles)
```

### 2. 임베딩 캐싱

```python
# 캐싱 활성화로 중복 임베딩 방지
embedder = TextEmbedder(use_cache=True)

# 같은 텍스트는 캐시에서 가져옴 (API 호출 없음)
emb1 = await embedder.embed("same text")
emb2 = await embedder.embed("same text")  # 캐시 히트
```

### 3. 온도 설정 최적화

```python
# 요약: 다양성 필요 → 온도 높게
summarizer = ArticleSummarizer(temperature=0.3)

# 분류: 일관성 필요 → 온도 낮게
classifier = ContentClassifier(temperature=0.1)

# 평가: 균형 → 온도 중간
evaluator = ImportanceEvaluator(temperature=0.2)
```

---

## 예제

### 전체 파이프라인

```python
from src.app.processors import (
    ArticleSummarizer,
    ImportanceEvaluator,
    ContentClassifier,
    TextEmbedder,
)

async def process_article(article):
    """단일 아티클 전체 처리"""

    # 1. 요약 생성
    summarizer = ArticleSummarizer()
    summary = await summarizer.summarize(
        title=article["title"],
        content=article["content"],
        language="ko",
        length="medium"
    )

    # 2. 중요도 평가
    evaluator = ImportanceEvaluator()
    eval_result = await evaluator.evaluate(
        title=article["title"],
        content=article["content"],
        metadata=article.get("metadata", {})
    )

    # 3. 카테고리 분류
    classifier = ContentClassifier()
    class_result = await classifier.classify(
        title=article["title"],
        content=article["content"],
        source_name=article.get("source_name", ""),
        url=article.get("url", "")
    )

    # 4. 임베딩 생성
    embedder = TextEmbedder()
    embedding = await embedder.embed_article_async(
        title=article["title"],
        content=article["content"],
        summary=summary
    )

    return {
        "title": article["title"],
        "summary": summary,
        "importance_score": eval_result["final_score"],
        "category": class_result["category"],
        "keywords": class_result["keywords"],
        "embedding": embedding
    }
```

### 배치 처리 (최적화)

```python
async def process_batch(articles):
    """여러 아티클 병렬 처리 (최고 성능)"""

    # 1. 요약, 평가, 분류 동시 실행
    summarizer = ArticleSummarizer()
    evaluator = ImportanceEvaluator()
    classifier = ContentClassifier()

    summaries, eval_results, class_results = await asyncio.gather(
        summarizer.batch_summarize(articles),
        evaluator.batch_evaluate(articles),
        classifier.batch_classify(articles)
    )

    # 2. 임베딩 생성 (요약 사용)
    embedder = TextEmbedder()
    embedding_texts = [
        embedder.embed_article(
            title=article["title"],
            content=article["content"],
            summary=summary
        )
        for article, summary in zip(articles, summaries)
    ]
    embeddings = await embedder.batch_embed(embedding_texts)

    # 3. 결과 결합
    results = []
    for article, summary, eval_res, class_res, embedding in zip(
        articles, summaries, eval_results, class_results, embeddings
    ):
        results.append({
            "title": article["title"],
            "summary": summary,
            "importance_score": eval_res["final_score"],
            "category": class_res["category"],
            "keywords": class_res["keywords"],
            "embedding": embedding
        })

    return results
```

---

## 🚀 ProcessingPipeline (통합 파이프라인)

**가장 권장하는 사용법**: 모든 프로세서를 자동으로 실행하는 통합 파이프라인

### 기본 사용법

```python
from src.app.processors import ProcessingPipeline

# 파이프라인 초기화
pipeline = ProcessingPipeline(
    provider="openai",
    summary_length="medium",  # short, medium, long
    summary_language="ko"     # ko, en
)

# 단일 아티클 처리 (모든 단계 자동 실행)
result = await pipeline.process_article(
    title="Attention Is All You Need",
    content="We propose the Transformer...",
    url="https://arxiv.org/abs/1706.03762",
    source_name="arXiv",
    metadata={"year": 2017, "citations": 50000}
)

# 결과: ProcessedArticle 객체
print(result.summary)           # 한국어 요약
print(result.importance_score)  # 0.94
print(result.category)          # "paper"
print(result.keywords)          # ["Transformer", "Attention", ...]
print(result.embedding)         # [0.1, 0.2, ...] (1536 dims)
```

### 배치 처리 (최고 성능)

```python
articles = [
    {"title": "Paper 1", "content": "...", "url": "...", "metadata": {...}},
    {"title": "Paper 2", "content": "...", "url": "...", "metadata": {...}},
    {"title": "Paper 3", "content": "...", "url": "...", "metadata": {...}},
]

# 병렬 처리 (max_concurrent로 동시 실행 제한)
results = await pipeline.process_batch(
    articles,
    max_concurrent=5  # 동시에 5개까지 처리
)

# 5개 아티클 처리: ~8초 (평균 1.7초/아티클)
```

### ProcessedArticle 데이터 구조

```python
@dataclass
class ProcessedArticle:
    # 원본 데이터
    title: str
    content: str
    url: str
    source_name: str
    source_type: str

    # 처리 결과
    summary: str                 # 한국어 요약
    importance_score: float      # 최종 중요도 (0.0-1.0)
    category: str                # paper/news/report/blog/other
    keywords: List[str]          # 키워드 리스트
    research_field: str          # 연구 분야
    embedding: List[float]       # 1536차원 벡터

    # 상세 평가
    innovation_score: float      # 혁신성 (0.0-1.0)
    relevance_score: float       # 관련성 (0.0-1.0)
    impact_score: float          # 영향력 (0.0-1.0)
    timeliness_score: float      # 시의성 (0.0-1.0)

    # 메타데이터
    metadata: Dict[str, Any]
    processed_at: datetime
```

### 유틸리티 함수

```python
# 상위 N개 아티클 (중요도순)
top_articles = pipeline.get_top_articles(results, top_n=5)

# 카테고리별 필터링
papers = pipeline.filter_by_category(results, category="paper")

# 점수 기준 필터링
high_quality = pipeline.filter_by_score(results, min_score=0.7)

# 통계 정보
stats = pipeline.get_statistics(results)
print(stats)
# {
#     "total": 5,
#     "category_distribution": {"paper": 4, "news": 1},
#     "average_score": 0.89,
#     "max_score": 0.94,
#     "min_score": 0.85,
#     "high_quality_count": 5
# }
```

### 성능 벤치마크

| 작업 | 시간 | 비고 |
|-----|------|------|
| 단일 아티클 처리 | ~3.7초 | 요약+평가+분류+임베딩 |
| 배치 5개 처리 | ~8.6초 | 병렬 처리 (평균 1.7초/개) |
| 배치 10개 처리 | ~15초 | max_concurrent=5 |

**최적화 팁**:
- `max_concurrent` 조정 (권장: 3-5)
- `summary_length="short"` 사용 시 더 빠름
- 임베딩 캐싱 활성화 (기본값)

---

## 🔗 관련 문서

- [프롬프트 관리 시스템](./PROMPTS.md)
- [LLM 통합 가이드](./LLM_INTEGRATION.md)
- [API 문서](./API.md)

---

**작성일**: 2025-12-03
**버전**: 1.1.0 (파이프라인 추가)
