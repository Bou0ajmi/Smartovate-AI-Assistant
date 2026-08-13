from src.aws.bedrock_client import get_bedrock_client
from langchain_aws import ChatBedrockConverse
from config import SUMM_MODEL_ID
from functools import lru_cache

@lru_cache
def get_summarization_model():
    summ_model=ChatBedrockConverse(
            client=get_bedrock_client(),
            model_id=SUMM_MODEL_ID
        )
    return summ_model