"""
프롬프트 관리 유틸리티

configs/prompts.yaml 파일에서 LLM 프롬프트를 로드하고 관리합니다.
"""

import logging
from functools import lru_cache
from pathlib import Path
from string import Template
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class PromptManager:
    """프롬프트 로드 및 관리 클래스"""

    def __init__(self, prompts_path: Path | None = None):
        """
        Args:
            prompts_path: prompts.yaml 파일 경로 (None일 경우 기본 경로 사용)
        """
        if prompts_path is None:
            # 기본 경로: configs/prompts.yaml
            project_root = Path(__file__).parent.parent.parent.parent
            prompts_path = project_root / "configs" / "prompts.yaml"

        self.prompts_path = prompts_path
        self._prompts: dict[str, Any] | None = None

    @property
    def prompts(self) -> dict[str, Any]:
        """프롬프트 데이터 (lazy loading)"""
        if self._prompts is None:
            self._prompts = self._load_prompts()
        return self._prompts

    def _load_prompts(self) -> dict[str, Any]:
        """YAML 파일에서 프롬프트 로드"""
        try:
            with open(self.prompts_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"Prompts loaded from {self.prompts_path}")
                return data
        except FileNotFoundError:
            logger.error(f"Prompts file not found: {self.prompts_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise

    def reload(self) -> None:
        """프롬프트 파일 재로드"""
        self._prompts = None
        logger.info("Prompts reloaded")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        프롬프트 가져오기

        Args:
            key_path: 점(.)으로 구분된 키 경로 (예: "summarize.korean.medium")
            default: 키가 없을 때 반환할 기본값

        Returns:
            프롬프트 데이터

        Examples:
            >>> manager = PromptManager()
            >>> system_prompt = manager.get("summarize.korean.medium.system")
        """
        keys = key_path.split(".")
        value = self.prompts

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_system_prompt(self, category: str, subcategory: str | None = None) -> str | None:
        """
        시스템 프롬프트 가져오기

        Args:
            category: 프롬프트 카테고리 (예: "summarize", "evaluate_importance")
            subcategory: 하위 카테고리 (예: "korean.medium")

        Returns:
            시스템 프롬프트 문자열

        Examples:
            >>> manager.get_system_prompt("summarize", "korean.medium")
            >>> manager.get_system_prompt("evaluate_importance")
        """
        if subcategory:
            return self.get(f"{category}.{subcategory}.system")
        return self.get(f"{category}.system")

    def get_user_template(self, category: str, subcategory: str | None = None) -> str | None:
        """
        유저 프롬프트 템플릿 가져오기

        Args:
            category: 프롬프트 카테고리
            subcategory: 하위 카테고리

        Returns:
            유저 프롬프트 템플릿 문자열
        """
        if subcategory:
            return self.get(f"{category}.{subcategory}.user_template")
        return self.get(f"{category}.user_template")

    def format_prompt(self, template: str, **kwargs) -> str:
        """
        프롬프트 템플릿에 변수 치환

        Args:
            template: 프롬프트 템플릿 문자열
            **kwargs: 치환할 변수들

        Returns:
            변수가 치환된 프롬프트 문자열

        Examples:
            >>> template = "제목: {title}\\n내용: {content}"
            >>> manager.format_prompt(template, title="Test", content="Content")
            "제목: Test\\n내용: Content"
        """
        try:
            # Python string.Template 사용 (안전한 치환)
            # {key} 형식을 $key로 변경
            safe_template = template.replace("{", "${")
            t = Template(safe_template)
            return t.safe_substitute(**kwargs)
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return template

    def build_messages(
        self,
        category: str,
        subcategory: str | None = None,
        **template_vars,
    ) -> list[dict[str, str]]:
        """
        LLM API용 메시지 리스트 생성

        Args:
            category: 프롬프트 카테고리
            subcategory: 하위 카테고리
            **template_vars: 유저 프롬프트 템플릿에 치환할 변수들

        Returns:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Examples:
            >>> messages = manager.build_messages(
            ...     "summarize",
            ...     "korean.medium",
            ...     title="GPT-4",
            ...     content="..."
            ... )
        """
        system_prompt = self.get_system_prompt(category, subcategory)
        user_template = self.get_user_template(category, subcategory)

        if not system_prompt or not user_template:
            raise ValueError(
                f"Prompts not found for {category}" + (f".{subcategory}" if subcategory else ""),
            )

        # 유저 프롬프트에 변수 치환
        user_prompt = self.format_prompt(user_template, **template_vars)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def get_categories(self) -> list[str]:
        """사용 가능한 카테고리 목록 반환"""
        return list(self.prompts.keys())

    def get_summary_lengths(self) -> list[str]:
        """요약 길이 옵션 반환"""
        korean_prompts = self.get("summarize.korean", {})
        return list(korean_prompts.keys())

    def get_classification_categories(self) -> list[str]:
        """분류 카테고리 목록 반환"""
        return self.get("classify_category.categories", [])

    def get_research_fields(self) -> list[str]:
        """연구 분야 목록 반환"""
        return self.get("classify_category.research_fields", [])

    def get_evaluation_criteria(self) -> list[str]:
        """평가 기준 목록 반환"""
        return self.get("evaluate_importance.criteria", [])

    def get_evaluation_weights(self) -> dict[str, float]:
        """평가 기준별 가중치 반환"""
        return self.get("evaluate_importance.weights", {})


@lru_cache(maxsize=1)
def get_prompt_manager() -> PromptManager:
    """
    PromptManager 싱글톤 인스턴스 반환

    Returns:
        PromptManager 인스턴스

    Examples:
        >>> manager = get_prompt_manager()
        >>> messages = manager.build_messages("summarize", "korean.medium", ...)
    """
    return PromptManager()


# 편의 함수들
def get_prompt(key_path: str, default: Any = None) -> Any:
    """프롬프트 가져오기 (편의 함수)"""
    return get_prompt_manager().get(key_path, default)


def build_messages(
    category: str,
    subcategory: str | None = None,
    **template_vars,
) -> list[dict[str, str]]:
    """메시지 빌드 (편의 함수)"""
    return get_prompt_manager().build_messages(category, subcategory, **template_vars)


def format_prompt(template: str, **kwargs) -> str:
    """프롬프트 포맷 (편의 함수)"""
    return get_prompt_manager().format_prompt(template, **kwargs)


# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # PromptManager 인스턴스 생성
    manager = get_prompt_manager()

    # 1. 카테고리 목록 확인
    print("Available categories:", manager.get_categories())
    print("Summary lengths:", manager.get_summary_lengths())
    print("Classification categories:", manager.get_classification_categories())

    # 2. 특정 프롬프트 가져오기
    system_prompt = manager.get("summarize.korean.medium.system")
    print("\n[System Prompt]")
    print(system_prompt[:100], "...")

    # 3. 메시지 빌드
    messages = manager.build_messages(
        "summarize",
        "korean.medium",
        title="Attention Is All You Need",
        content="Transformer 모델을 소개하는 논문...",
    )
    print("\n[Built Messages]")
    for msg in messages:
        print(f"{msg['role']}: {msg['content'][:80]}...")

    # 4. 평가 기준 및 가중치
    criteria = manager.get_evaluation_criteria()
    weights = manager.get_evaluation_weights()
    print("\n[Evaluation]")
    print("Criteria:", criteria)
    print("Weights:", weights)

    # 5. 프롬프트 포맷팅
    template = "제목: {title}, 저자: {author}"
    formatted = manager.format_prompt(template, title="GPT-4", author="OpenAI")
    print("\n[Formatted]")
    print(formatted)
