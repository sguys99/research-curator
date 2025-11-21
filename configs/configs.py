import os

import streamlit as st
from boto3 import session
from botocore.exceptions import ClientError  # type: ignore
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    profiles: str = "dev"
    ai_operation_host: str
    upstage_api_key: str

    class Config:
        app_profile = os.getenv("APP_PROFILE")
        if app_profile and "dev" in app_profile:
            env_file = [".env", ".env.dev"]
        else:
            env_file = ".env"


@st.cache_resource
def load_configs() -> Config:
    print("Loading configs...")
    secrets: dict[str, str] = __get_secret(
        region_name="ap-northeast-2", secret_name="v2/marvel/dev/ai-streamlit"
    )
    return Config(**secrets)


def __get_secret(region_name: str, secret_name: str) -> dict[str, str]:
    boto3_session = session.Session()
    client = boto3_session.client(service_name="secretsmanager", region_name=region_name)  # type: ignore
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)  # type: ignore
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = eval(get_secret_value_response["SecretString"])  # type: ignore
    return dict(secret)
