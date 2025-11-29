"""LLM API endpoints."""

import json

from fastapi import APIRouter, HTTPException

from src.app.api.schemas import (
    ArticleAnalysisRequest,
    ArticleAnalysisResponse,
    ArticleSummaryRequest,
    ArticleSummaryResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from src.app.llm import LLMClient

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    Generate chat completion using specified LLM provider.

    Supports both OpenAI and Claude with a unified interface.
    """
    try:
        # Create LLM client
        client = LLMClient(
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Convert messages to dict format
        messages = [msg.model_dump() for msg in request.messages]

        # Generate completion
        content = await client.achat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
        )

        return ChatCompletionResponse(content=content, provider=request.provider, model=client.model)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM completion failed: {str(e)}",
        ) from e


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """
    Generate embedding vector for given text.

    Uses OpenAI's embedding models by default.
    """
    try:
        # Create LLM client (always use OpenAI for embeddings)
        client = LLMClient(provider="openai")

        # Generate embedding
        embedding = await client.agenerate_embedding(text=request.text, model=request.model)

        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
            model=request.model or client.model,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}",
        ) from e


@router.post("/summarize", response_model=ArticleSummaryResponse)
async def summarize_article(
    request: ArticleSummaryRequest,
) -> ArticleSummaryResponse:
    """
    Summarize article in specified language.

    Default language is Korean (ko).
    """
    try:
        # Create LLM client
        client = LLMClient(provider=request.provider, temperature=0.5)

        # Prepare prompt based on language
        if request.language == "ko":
            system_content = "You are an AI research expert. Summarize articles in Korean."
            user_content = f"""다음 논문을 한국어로 {request.max_sentences}문장 이내로 요약해주세요:

Title: {request.title}

Content:
{request.content}
"""
        else:
            system_content = "You are an AI research expert. Summarize articles concisely."
            user_content = (
                f"Summarize the following article in {request.max_sentences} "
                f"sentences or less:\n\nTitle: {request.title}\n\nContent:\n{request.content}"
            )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

        # Generate summary
        summary = await client.achat_completion(messages=messages, max_tokens=1000)

        return ArticleSummaryResponse(
            summary=summary,
            original_length=len(request.content),
            summary_length=len(summary),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}",
        ) from e


@router.post("/analyze", response_model=ArticleAnalysisResponse)
async def analyze_article(request: ArticleAnalysisRequest) -> ArticleAnalysisResponse:
    """
    Analyze research article and extract metadata.

    Returns category, importance score, keywords, field, and Korean summary.
    """
    try:
        # Create LLM client
        client = LLMClient(provider=request.provider, temperature=0.3)

        # Analysis prompt
        analysis_messages = [
            {
                "role": "system",
                "content": "You are an AI research expert. Analyze articles and respond in JSON.",
            },
            {
                "role": "user",
                "content": f"""
Analyze this research article and return JSON with:
- category: one of (paper, news, report)
- importance_score: 0.0 to 1.0
- keywords: list of 5 relevant keywords
- field: research field (e.g., "Computer Vision", "NLP", "Robotics")

Title: {request.title}
Content: {request.content}
""",
            },
        ]

        # Korean summary prompt
        summary_messages = [
            {
                "role": "system",
                "content": "You are an AI research expert. Summarize in Korean.",
            },
            {
                "role": "user",
                "content": f"""다음 논문을 한국어로 3-4문장으로 요약해주세요:

Title: {request.title}
Content: {request.content}
""",
            },
        ]

        # Run both tasks concurrently
        import asyncio

        analysis_task = client.achat_completion(
            analysis_messages,
            response_format="json",
            max_tokens=300,
        )
        summary_task = client.achat_completion(summary_messages, max_tokens=500)

        analysis_response, summary = await asyncio.gather(analysis_task, summary_task)

        # Parse JSON response
        try:
            analysis = json.loads(analysis_response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", analysis_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                raise ValueError("Failed to parse JSON response") from None

        return ArticleAnalysisResponse(
            category=analysis.get("category", "paper"),
            importance_score=analysis.get("importance_score", 0.5),
            keywords=analysis.get("keywords", []),
            field=analysis.get("field", "Unknown"),
            summary_korean=summary,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        ) from e
