from src.aws.bedrock_client import get_bedrock_client
from langchain_aws import ChatBedrockConverse
from config import MODEL_ID
from functools import lru_cache

@lru_cache
def get_chat_model():
    chat_model=ChatBedrockConverse(
            client=get_bedrock_client(),
            model_id=MODEL_ID
        )
    return chat_model