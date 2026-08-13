
from functools import lru_cache
from  config import REGION_NAME,PROFILE_NAME
import boto3


@lru_cache
def get_bedrock_client():
    session = boto3.Session(region_name=REGION_NAME)
    return session.client("bedrock-runtime")

