# LLM Integration Guide

## Overview

이 프로젝트는 LiteLLM을 사용하여 여러 LLM 제공자(OpenAI, Claude 등)를 통합적으로 관리합니다. 모든 LLM 호출은 OpenAI 포맷을 따르므로, 제공자 간 전환이 쉽습니다.

## Setup

### Environment Variables

`.env` 파일에 다음 환경 변수를 설정하세요:

```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # or claude

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic Claude Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Dependencies

LiteLLM은 이미 `pyproject.toml`에 포함되어 있습니다:

```bash
uv sync
```

## Usage

### Basic Usage

```python
from src.app.llm import LLMClient

# OpenAI 사용
client = LLMClient(provider="openai")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Summarize this article."}
]

response = client.chat_completion(messages)
print(response)
```

### Using Claude

```python
from src.app.llm import LLMClient

# Claude 사용
client = LLMClient(provider="claude")

messages = [
    {"role": "user", "content": "Summarize this article."}
]

response = client.chat_completion(messages)
print(response)
```

### JSON Response Format

```python
from src.app.llm import LLMClient

client = LLMClient(provider="openai")

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that responds in JSON."
    },
    {
        "role": "user",
        "content": "Return JSON with keys: category, importance_score, keywords"
    }
]

response = client.chat_completion(
    messages,
    response_format="json",
    max_tokens=300
)

import json
data = json.loads(response)
```

### Generating Embeddings

```python
from src.app.llm import LLMClient

client = LLMClient(provider="openai")

text = "AI research trends in 2024"
embedding = client.generate_embedding(text)

print(f"Embedding dimension: {len(embedding)}")  # 1536 for text-embedding-3-small
```

### Async Operations

```python
import asyncio
from src.app.llm import LLMClient

async def main():
    client = LLMClient(provider="openai")

    # Async chat completion
    messages = [
        {"role": "user", "content": "What is machine learning?"}
    ]
    response = await client.achat_completion(messages)
    print(response)

    # Async embedding
    embedding = await client.agenerate_embedding("Deep learning")
    print(f"Embedding dimension: {len(embedding)}")

asyncio.run(main())
```

### Custom Parameters

```python
from src.app.llm import LLMClient

client = LLMClient(
    provider="openai",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2000
)

# Override default parameters
response = client.chat_completion(
    messages,
    temperature=0.3,  # More deterministic
    max_tokens=500
)
```

### Using Cached Client

```python
from src.app.llm import get_llm_client

# Get cached client instance (recommended for production)
client = get_llm_client(provider="openai")
response = client.chat_completion(messages)
```

## Supported Providers

### OpenAI

**Models:**
- `gpt-4o` (default)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

**Embeddings:**
- `text-embedding-3-small` (default, 1536 dimensions)
- `text-embedding-3-large` (3072 dimensions)

### Anthropic Claude

**Models:**
- `claude-3-5-sonnet-20241022` (default)
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

**Note:** Claude doesn't support native embeddings. Use OpenAI for embeddings.

## Common Use Cases

### Article Summarization

```python
from src.app.llm import LLMClient

client = LLMClient(provider="openai", temperature=0.5)

article_text = """
[Your article content here]
"""

messages = [
    {
        "role": "system",
        "content": "You are an AI research expert. Summarize articles in Korean."
    },
    {
        "role": "user",
        "content": f"다음 논문을 한국어로 3-4문장으로 요약해주세요:\n\n{article_text}"
    }
]

summary = client.chat_completion(messages, max_tokens=500)
```

### Importance Scoring

```python
from src.app.llm import LLMClient
import json

client = LLMClient(provider="openai")

messages = [
    {
        "role": "system",
        "content": "Rate article importance from 0.0 to 1.0. Respond in JSON."
    },
    {
        "role": "user",
        "content": f"Rate this article: {article_title}"
    }
]

response = client.chat_completion(messages, response_format="json")
data = json.loads(response)
importance_score = data.get("importance_score", 0.5)
```

### Category Classification

```python
from src.app.llm import LLMClient
import json

client = LLMClient(provider="openai")

messages = [
    {
        "role": "system",
        "content": "Classify content as: paper, news, or report. Respond in JSON."
    },
    {
        "role": "user",
        "content": f"Classify this: {content}"
    }
]

response = client.chat_completion(messages, response_format="json")
data = json.loads(response)
category = data.get("category", "unknown")
```

## Error Handling

```python
from src.app.llm import LLMClient

client = LLMClient(provider="openai")

try:
    response = client.chat_completion(messages)
except RuntimeError as e:
    print(f"LLM completion failed: {e}")
    # Handle error (retry, fallback, etc.)
```

## Best Practices

1. **Use Cached Client**: Use `get_llm_client()` for production to cache instances
2. **Set Appropriate Timeouts**: LiteLLM handles timeouts automatically
3. **Temperature Settings**:
   - Low (0.0-0.3): Factual, deterministic tasks
   - Medium (0.4-0.7): Balanced creativity and consistency
   - High (0.8-1.0): Creative, diverse outputs
4. **Token Limits**: Set `max_tokens` based on expected output length
5. **Async for Concurrency**: Use async methods for parallel LLM calls

## Testing

Run unit tests:
```bash
pytest tests/test_llm_client.py -v
```

Run with API integration tests:
```bash
# Requires OPENAI_API_KEY and ANTHROPIC_API_KEY in .env
pytest tests/test_llm_client.py -v
```

## Examples

Complete examples are available in:
```
examples/llm_usage_example.py
```

Run examples:
```bash
python examples/llm_usage_example.py
```

## Migration from Direct OpenAI Calls

**Before:**
```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages
)
content = response.choices[0].message.content
```

**After:**
```python
from src.app.llm import LLMClient

client = LLMClient(provider="openai")
content = client.chat_completion(messages)
```

## Troubleshooting

### API Key Not Found

```
RuntimeError: LLM completion failed
```

**Solution:** Check that the appropriate API key is set in `.env`:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Claude

### Rate Limiting

LiteLLM automatically handles rate limiting and retries. If you encounter persistent rate limit errors:

1. Add delays between calls
2. Use async operations with controlled concurrency
3. Implement exponential backoff

### Invalid JSON Response

If `response_format="json"` returns invalid JSON:

```python
import json
import re

try:
    data = json.loads(response)
except json.JSONDecodeError:
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(0))
```

## Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
