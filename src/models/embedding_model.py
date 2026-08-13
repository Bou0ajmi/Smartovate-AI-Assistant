from src.aws.bedrock_client import get_bedrock_client
from config import EMBED_MODEL_ID
from langchain_aws import BedrockEmbeddings
from functools import lru_cache

@lru_cache
def get_embedding_model():
    embedding_model=BedrockEmbeddings(
            client=get_bedrock_client(),
            model_id=EMBED_MODEL_ID
        )
    return embedding_model