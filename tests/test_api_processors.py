"""Unit tests for processors API endpoints."""

import pytest


@pytest.mark.unit
class TestSummarizeEndpoint:
    def test_summarize_success(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
                "language": "ko",
                "length": "medium",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "ko"
        assert data["length"] == "medium"
        assert data["summary"]

    def test_summarize_english(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
                "language": "en",
                "length": "short",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["length"] == "short"

    def test_summarize_missing_fields(self, client):
        response = client.post(
            "/api/processors/summarize",
            json={"title": "Test"},
        )

        assert response.status_code == 422


@pytest.mark.unit
class TestEvaluateEndpoint:
    def test_evaluate_success(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/evaluate",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
                "metadata": sample_article["metadata"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert 0.0 <= data["innovation_score"] <= 1.0
        assert 0.0 <= data["relevance_score"] <= 1.0
        assert 0.0 <= data["impact_score"] <= 1.0
        assert 0.0 <= data["timeliness_score"] <= 1.0
        assert 0.0 <= data["final_score"] <= 1.0

    def test_evaluate_without_metadata(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/evaluate",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "final_score" in data


@pytest.mark.unit
class TestClassifyEndpoint:
    def test_classify_success(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/classify",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
                "source_name": sample_article["source_name"],
                "url": sample_article["url"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] in ["paper", "news", "report", "blog", "other"]
        assert data["category"] == "paper"
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["keywords"], list)

    def test_classify_minimal_input(self, client, llm_mock):
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


@pytest.mark.unit
class TestProcessEndpoint:
    def test_process_success(self, client, sample_article, llm_mock):
        response = client.post(
            "/api/processors/process",
            json={
                "title": sample_article["title"],
                "content": sample_article["content"],
                "url": sample_article["url"],
                "source_name": sample_article["source_name"],
                "metadata": sample_article["metadata"],
                "summary_language": "ko",
                "summary_length": "medium",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == sample_article["title"]
        assert data["content"] == sample_article["content"]
        assert data["url"] == sample_article["url"]
        assert data["source_name"] == sample_article["source_name"]

        assert data["summary"]
        assert 0.0 <= data["importance_score"] <= 1.0
        assert data["category"] in ["paper", "news", "report", "blog", "other"]
        assert isinstance(data["keywords"], list)
        assert isinstance(data["embedding"], list)

    def test_process_minimal_input(self, client, llm_mock):
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


@pytest.mark.unit
class TestBatchProcessEndpoint:
    def test_batch_process_success(self, client, llm_mock):
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
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert data["success"] == 2
        assert data["failed"] == 0

        assert isinstance(data["results"], list)
        assert len(data["results"]) == 2

        for result in data["results"]:
            assert "title" in result
            assert "summary" in result
            assert "importance_score" in result
            assert "category" in result
            assert "embedding" in result

    def test_batch_process_single_article(self, client, llm_mock):
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
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["success"] == 1

    def test_batch_process_empty_list(self, client, llm_mock):
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


@pytest.mark.unit
class TestStatisticsEndpoint:
    def test_statistics_success(self, client, llm_mock):
        batch_response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {"title": "Paper 1", "content": "AI research paper."},
                    {"title": "News 1", "content": "Tech news article."},
                ],
                "max_concurrent": 2,
            },
        )

        assert batch_response.status_code == 200
        articles = batch_response.json()["results"]

        response = client.post(
            "/api/processors/statistics",
            json=articles,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert isinstance(data["category_distribution"], dict)

    def test_statistics_empty_list(self, client, llm_mock):
        response = client.post(
            "/api/processors/statistics",
            json=[],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


@pytest.mark.unit
class TestEndToEndWorkflow:
    def test_full_workflow(self, client, llm_mock):
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

        assert article["summary"]
        assert 0.0 <= article["importance_score"] <= 1.0
        assert article["category"] in ["paper", "report", "news", "blog", "other"]
        assert len(article["embedding"]) == 1536

        batch_response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [
                    {"title": "Article 1", "content": "Content 1"},
                    {"title": "Article 2", "content": "Content 2"},
                ],
                "max_concurrent": 2,
            },
        )

        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        assert batch_data["success"] == 2

        all_articles = [article] + batch_data["results"]
        stats_response = client.post(
            "/api/processors/statistics",
            json=all_articles,
        )

        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total"] == 3


@pytest.mark.unit
class TestErrorHandling:
    def test_invalid_language(self, client, llm_mock):
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": "Test",
                "content": "Test content",
                "language": "invalid",
            },
        )

        assert response.status_code == 200

    def test_missing_required_field(self, client):
        response = client.post(
            "/api/processors/summarize",
            json={
                "title": "Test",
            },
        )

        assert response.status_code == 422

    def test_invalid_json(self, client):
        response = client.post(
            "/api/processors/summarize",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_max_concurrent_validation(self, client):
        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [{"title": "Test", "content": "Test"}],
                "max_concurrent": 20,
            },
        )

        assert response.status_code == 422

        response = client.post(
            "/api/processors/batch-process",
            json={
                "articles": [{"title": "Test", "content": "Test"}],
                "max_concurrent": 0,
            },
        )

        assert response.status_code == 422


@pytest.mark.unit
class TestHealthCheck:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
