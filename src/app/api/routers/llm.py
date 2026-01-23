"""LLM API 엔드포인트."""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    ArticleAnalysisRequest,
    ArticleAnalysisResponse,
    ArticleSummaryRequest,
    ArticleSummaryResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.llm import LLMClient

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse | StreamingResponse:
    """
    지정한 LLM 제공자를 사용해 채팅 응답을 생성한다.

    OpenAI와 Claude를 동일한 인터페이스로 지원한다.
    stream=True일 때 스트리밍 모드를 지원한다.
    """
    try:
        # LLM 클라이언트 생성
        client = LLMClient(
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # 메시지를 dict 형식으로 변환
        messages = [msg.model_dump() for msg in request.messages]

        # 스트리밍 모드
        if request.stream:

            async def stream_generator() -> AsyncIterator[str]:
                """LLM 응답으로 SSE 스트림을 생성한다."""
                try:
                    response_stream = await client.achat_completion(
                        messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        response_format=request.response_format,
                        stream=True,
                    )

                    async for chunk in response_stream:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            # SSE 형식: "data: {json}\n\n"
                            yield f"data: {json.dumps({'content': content})}\n\n"

                    # 완료 신호 전송
                    yield f"data: {json.dumps({'done': True})}\n\n"

                except Exception as e:
                    # SSE 형식으로 에러 전송
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        # 비스트리밍 모드
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
    주어진 텍스트의 임베딩 벡터를 생성한다.

    기본으로 OpenAI 임베딩 모델을 사용한다.
    """
    try:
        # LLM 클라이언트 생성(임베딩은 OpenAI 고정)
        client = LLMClient(provider="openai")

        # 임베딩 생성
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
    지정한 언어로 아티클을 요약한다.

    기본 언어는 한국어(ko)다.
    """
    try:
        # LLM 클라이언트 생성
        client = LLMClient(provider=request.provider, temperature=0.5)

        # 언어에 따른 프롬프트 준비
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

        # 요약 생성
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
    연구 아티클을 분석해 메타데이터를 추출한다.

    category, importance_score, keywords, field, summary_korean을 반환한다.
    """
    try:
        # LLM 클라이언트 생성
        client = LLMClient(provider=request.provider, temperature=0.3)

        # 분석 프롬프트
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

        # 한국어 요약 프롬프트
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

        # 두 작업 동시 실행
        import asyncio

        analysis_task = client.achat_completion(
            analysis_messages,
            response_format="json",
            max_tokens=300,
        )
        summary_task = client.achat_completion(summary_messages, max_tokens=500)

        analysis_response, summary = await asyncio.gather(analysis_task, summary_task)

        # JSON 응답 파싱
        try:
            analysis = json.loads(analysis_response)
        except json.JSONDecodeError:
            # 응답에서 JSON 추출 시도
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
