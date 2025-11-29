"""Example script demonstrating LLM client usage."""

import asyncio

from src.app.llm import LLMClient


def example_openai_basic():
    """Basic OpenAI usage example."""
    print("=== OpenAI Basic Example ===")
    client = LLMClient(provider="openai", model="gpt-4o")

    messages = [
        {"role": "system", "content": "You are a helpful AI research assistant."},
        {
            "role": "user",
            "content": "Summarize the key trends in AI research in 2024 in 3 bullet points.",
        },
    ]

    response = client.chat_completion(messages, temperature=0.7, max_tokens=500)
    print(response)
    print()


def example_claude_basic():
    """Basic Claude usage example."""
    print("=== Claude Basic Example ===")
    client = LLMClient(provider="claude", model="claude-3-5-sonnet-20241022")

    messages = [
        {
            "role": "user",
            "content": "Summarize the key trends in AI research in 2024 in 3 bullet points.",
        },
    ]

    response = client.chat_completion(messages, temperature=0.7, max_tokens=500)
    print(response)
    print()


def example_json_output():
    """Example of JSON-formatted output."""
    print("=== JSON Output Example ===")
    client = LLMClient(provider="openai")

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that responds in JSON format.",
        },
        {
            "role": "user",
            "content": """
            Analyze this article title and return a JSON object with:
            - category: one of (paper, news, report)
            - importance_score: 0.0 to 1.0
            - keywords: list of 3-5 relevant keywords

            Title: "GPT-5 Achieves Human-Level Performance on Complex Reasoning Tasks"
            """,
        },
    ]

    response = client.chat_completion(messages, response_format="json", max_tokens=300)
    print(response)
    print()


def example_embedding():
    """Example of generating embeddings."""
    print("=== Embedding Generation Example ===")
    client = LLMClient(provider="openai")

    texts = [
        "Transformer architecture in deep learning",
        "Reinforcement learning for robotics",
        "Computer vision using CNNs",
    ]

    for text in texts:
        embedding = client.generate_embedding(text)
        print(f"Text: {text}")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        print()


async def example_async_operations():
    """Example of async operations."""
    print("=== Async Operations Example ===")
    client = LLMClient(provider="openai")

    # Async chat completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"},
    ]

    response = await client.achat_completion(messages, max_tokens=200)
    print("Async chat response:", response[:100], "...")
    print()

    # Async embedding
    embedding = await client.agenerate_embedding("Deep learning for NLP")
    print(f"Async embedding dimension: {len(embedding)}")
    print()


def example_comparing_providers():
    """Example comparing OpenAI and Claude responses."""
    print("=== Comparing Providers ===")

    prompt = "Explain neural networks in one sentence."
    messages = [{"role": "user", "content": prompt}]

    # OpenAI response
    openai_client = LLMClient(provider="openai")
    openai_response = openai_client.chat_completion(messages, max_tokens=100)
    print(f"OpenAI: {openai_response}")
    print()

    # Claude response
    claude_client = LLMClient(provider="claude")
    claude_response = claude_client.chat_completion(messages, max_tokens=100)
    print(f"Claude: {claude_response}")
    print()


def example_article_summarization():
    """Example of article summarization (common use case)."""
    print("=== Article Summarization Example ===")
    client = LLMClient(provider="openai", temperature=0.5)

    article_text = """
    Researchers at MIT have developed a new neural network architecture
    that combines the benefits of transformers with the efficiency of
    convolutional neural networks. The hybrid model, dubbed TransConv,
    achieves state-of-the-art results on image classification tasks while
    requiring 40% less computational resources than traditional transformer
    models. The key innovation lies in the selective attention mechanism
    that adaptively chooses between local and global feature processing
    based on the input characteristics.
    """

    messages = [
        {
            "role": "system",
            "content": "You are an AI research expert. Summarize articles in Korean.",
        },
        {
            "role": "user",
            "content": f"다음 논문 내용을 한국어로 3-4문장으로 요약해주세요:\n\n{article_text}",
        },
    ]

    summary = client.chat_completion(messages, max_tokens=500)
    print(summary)
    print()


if __name__ == "__main__":
    # Run synchronous examples
    try:
        example_openai_basic()
    except Exception as e:
        print(f"OpenAI example failed: {e}\n")

    try:
        example_claude_basic()
    except Exception as e:
        print(f"Claude example failed: {e}\n")

    try:
        example_json_output()
    except Exception as e:
        print(f"JSON output example failed: {e}\n")

    try:
        example_embedding()
    except Exception as e:
        print(f"Embedding example failed: {e}\n")

    try:
        example_comparing_providers()
    except Exception as e:
        print(f"Comparing providers example failed: {e}\n")

    try:
        example_article_summarization()
    except Exception as e:
        print(f"Article summarization example failed: {e}\n")

    # Run async example
    try:
        asyncio.run(example_async_operations())
    except Exception as e:
        print(f"Async example failed: {e}\n")

    print("=== Examples Complete ===")
