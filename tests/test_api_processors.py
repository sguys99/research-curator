"""
API Processors 통합 테스트

Step 11: API 엔드포인트 통합 테스트
- 모든 API 엔드포인트 테스트
- 에러 핸들링 테스트
- End-to-end 워크플로우 테스트
"""

import pytest
from fastapi.testclient import TestClient

from src.app.api.main import app

client = TestClient(app)

# 샘플 데이터
SAMPLE_ARTICLE = {
    "title": "Attention Is All You Need",
    "content": "We propose a new simple network architecture, the Transformer, "
    "based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
}

SAMPLE_METADATA = {"year": 2017, "citations": 50000}


class TestSummarizeEndpoint:
    """요약 생성 API 테스트"""

    def test_summarize_success(self):
        """정상적인 요약 생성"""
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
                "language": "ko",
                "length": "medium",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "language" in data
        assert "length" in data
        assert data["language"] == "ko"
        assert data["length"] == "medium"
        assert len(data["summary"]) > 0

    def test_summarize_english(self):
        """영어 요약 생성"""
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
                "language": "en",
                "length": "short",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["length"] == "short"

    def test_summarize_missing_fields(self):
        """필수 필드 누락 시 에러"""
        response = client.post(
            "/api/processors/summarize",
            json={"title": "Test"},
        )

        assert response.status_code == 422  # Validation error


class TestEvaluateEndpoint:
    """중요도 평가 API 테스트"""

    def test_evaluate_success(self):
        """정상적인 중요도 평가"""
        response = client.post(
            "/api/processors/evaluate",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
                "metadata": SAMPLE_METADATA,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 모든 점수 필드 존재 확인
        assert "innovation_score" in data
        assert "relevance_score" in data
        assert "impact_score" in data
        assert "timeliness_score" in data
        assert "final_score" in data
        assert "llm_score" in data
        assert "metadata_score" in data

        # 점수 범위 검증 (0.0 ~ 1.0)
        for key in [
            "innovation_score",
            "relevance_score",
            "impact_score",
            "timeliness_score",
            "final_score",
            "llm_score",
            "metadata_score",
        ]:
            assert 0.0 <= data[key] <= 1.0, f"{key} out of range: {data[key]}"

    def test_evaluate_without_metadata(self):
        """메타데이터 없이 평가"""
        response = client.post(
            "/api/processors/evaluate",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "final_score" in data


class TestClassifyEndpoint:
    """카테고리 분류 API 테스트"""

    def test_classify_success(self):
        """정상적인 카테고리 분류"""
        response = client.post(
            "/api/processors/classify",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
                "source_name": "arXiv",
                "url": "https://arxiv.org/abs/1706.03762",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "category" in data
        assert "confidence" in data
        assert "keywords" in data
        assert "research_field" in data

        # 카테고리 검증
        assert data["category"] in ["paper", "news", "report", "blog", "other"]
        # arXiv 소스이므로 "paper"여야 함
        assert data["category"] == "paper"

        # 신뢰도 범위 검증
        assert 0.0 <= data["confidence"] <= 1.0

        # 키워드 리스트 검증
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) > 0

    def test_classify_minimal_input(self):
        """최소 입력으로 분류"""
        response = client.post(
            "/api/processors/classify",
            json={
                "title": "Test Title",
                "content": "Test content about machine learning.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "category" in data


class TestProcessEndpoint:
    """전체 처리 파이프라인 API 테스트"""

    def test_process_success(self):
        """정상적인 전체 처리"""
        response = client.post(
            "/api/processors/process",
            json={
                "title": SAMPLE_ARTICLE["title"],
                "content": SAMPLE_ARTICLE["content"],
                "url": "https://arxiv.org/abs/1706.03762",
                "source_name": "arXiv",
                "metadata": SAMPLE_METADATA,
                "summary_language": "ko",
                "summary_length": "medium",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 원본 데이터
        assert data["title"] == SAMPLE_ARTICLE["title"]
        assert data["content"] == SAMPLE_ARTICLE["content"]
        assert data["url"] == "https://arxiv.org/abs/1706.03762"
        assert data["source_name"] == "arXiv"

        # 처리 결과
        assert "summary" in data
        assert len(data["summary"]) > 0

        assert "importance_score" in data
        assert 0.0 <= data["importance_score"] <= 1.0

        assert "category" in data
        assert data["category"] in ["paper", "news", "report", "blog", "other"]

        assert "keywords" in data
        assert isinstance(data["keywords"], list)

        assert "research_field" in data

        # 임베딩 검증
        assert "embedding" in data
        assert isinstance(data["embedding"], list)
        assert len(data["embedding"]) == 1536  # OpenAI embedding dimension

        # 상세 평가
        assert "innovation_score" in data
        assert "relevance_score" in data
        assert "impact_score" in data
        assert "timeliness_score" in data

        # 메타데이터
        assert "metadata" in data
        assert "processed_at" in data

    def test_process_minimal_input(self):
        """최소 입력으로 처리"""
        response = client.post(
            "/api/processors/process",
            json={
                "title": "Test Article",
                "content": "This is a test article about transformers.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "importance_score" in data
        assert "embedding" in data


class TestBatchProcessEndpoint:
    """배치 처리 API 테스트"""

    def test_batch_process_success(self):
        """정상적인 배치 처리"""
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {
                        "title": "Paper 1",
                        "content": "Content about transformers and attention mechanisms.",
                    },
                    {
                        "title": "Paper 2",
                        "content": "Research on deep learning and neural networks.",
                    },
                ],
                "max_concurrent": 2,
            },
            timeout=60.0,
        )

        assert response.status_code == 200
        data = response.json()

        # 배치 처리 결과 검증
        assert "total" in data
        assert "success" in data
        assert "failed" in data
        assert "results" in data
        assert "processing_time" in data

        assert data["total"] == 2
        assert data["success"] == 2
        assert data["failed"] == 0

        # 결과 리스트 검증
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 2

        # 각 결과 검증
        for result in data["results"]:
            assert "title" in result
            assert "summary" in result
            assert "importance_score" in result
            assert "category" in result
            assert "embedding" in result

    def test_batch_process_single_article(self):
        """단일 아티클 배치 처리"""
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {
                        "title": "Single Article",
                        "content": "Single article content.",
                    },
                ],
                "max_concurrent": 1,
            },
            timeout=30.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["success"] == 1

    def test_batch_process_empty_list(self):
        """빈 리스트로 배치 처리"""
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [],
                "max_concurrent": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["success"] == 0


class TestStatisticsEndpoint:
    """통계 API 테스트"""

    def test_statistics_success(self):
        """정상적인 통계 계산"""
        # 먼저 배치 처리로 데이터 생성
        batch_response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {"title": "Paper 1", "content": "AI research paper."},
                    {"title": "News 1", "content": "Tech news article."},
                ],
                "max_concurrent": 2,
            },
            timeout=60.0,
        )

        assert batch_response.status_code == 200
        articles = batch_response.json()["results"]

        # 통계 계산
        response = client.post(
            "/api/processors/statistics",
            json=articles,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "category_distribution" in data
        assert "average_score" in data
        assert "max_score" in data
        assert "min_score" in data
        assert "high_quality_count" in data

        assert data["total"] == 2
        assert isinstance(data["category_distribution"], dict)

    def test_statistics_empty_list(self):
        """빈 리스트 통계"""
        response = client.post(
            "/api/processors/statistics",
            json=[],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestEndToEndWorkflow:
    """End-to-End 워크플로우 테스트"""

    def test_full_workflow(self):
        """전체 워크플로우: 수집 → 처리 → 통계"""

        # Step 1: 단일 아티클 처리
        process_response = client.post(
            "/api/processors/process",
            json={
                "title": "GPT-4 Technical Report",
                "content": "GPT-4 is a large multimodal model capable of processing images and text.",
                "url": "https://openai.com/research/gpt-4",
                "source_name": "OpenAI",
                "metadata": {"year": 2023, "citations": 5000},
            },
        )

        assert process_response.status_code == 200
        article = process_response.json()

        # Step 2: 요약 검증
        assert len(article["summary"]) > 0
        assert article["importance_score"] > 0.5  # 중요한 논문이므로 높은 점수

        # Step 3: 분류 검증
        assert article["category"] in ["paper", "report", "news"]
        assert "GPT" in " ".join(article["keywords"]) or "model" in " ".join(article["keywords"])

        # Step 4: 임베딩 검증
        assert len(article["embedding"]) == 1536

        # Step 5: 배치 처리
        batch_response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {"title": "Article 1", "content": "Content 1"},
                    {"title": "Article 2", "content": "Content 2"},
                ],
                "max_concurrent": 2,
            },
            timeout=60.0,
        )

        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        assert batch_data["success"] == 2

        # Step 6: 통계 계산
        all_articles = [article] + batch_data["results"]
        stats_response = client.post(
            "/api/processors/statistics",
            json=all_articles,
        )

        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total"] == 3


class TestErrorHandling:
    """에러 핸들링 테스트"""

    def test_invalid_language(self):
        """잘못된 언어 코드"""
        # Pydantic이 기본값을 사용하므로 요청은 성공
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": "Test",
                "content": "Test content",
                "language": "invalid",
            },
        )
        # 요청은 성공하지만 LLM이 처리
        assert response.status_code in [200, 500]

    def test_missing_required_field(self):
        """필수 필드 누락"""
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": "Test",
                # content 누락
            },
        )

        assert response.status_code == 422

    def test_invalid_json(self):
        """잘못된 JSON"""
        response = client.post(
            "/api/processors/summarize",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_max_concurrent_validation(self):
        """max_concurrent 범위 검증"""
        # 범위 초과 (최대 10)
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [{"title": "Test", "content": "Test"}],
                "max_concurrent": 20,  # 최대 10을 초과
            },
        )

        assert response.status_code == 422

        # 0 이하
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [{"title": "Test", "content": "Test"}],
                "max_concurrent": 0,
            },
        )

        assert response.status_code == 422


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_root_endpoint(self):
        """루트 엔드포인트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint(self):
        """헬스 체크 엔드포인트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
