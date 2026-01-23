from typing import Any

import yaml

from app.utils.path import DATA_CONFIG_PATH


def load_config(path: str) -> dict[str, Any]:
    """설정 파일을 로드한다.

    설명:
        YAML 설정 파일을 파이썬 딕셔너리로 로드한다.

    Args:
        path (str): 설정 파일 경로

    Returns:
        dict[str, Any]: 설정 딕셔너리
    """
    config = {}
    with open(path, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def load_all_configs(data_type="HPMC"):
    """
    데이터 처리/모델 학습에 필요한 설정 파일을 로드한다.

    data_type에 따라 학습 설정 경로가 달라질 수 있다.
    """

    configs = {
        "data": load_config(path=DATA_CONFIG_PATH),
    }

    return configs
