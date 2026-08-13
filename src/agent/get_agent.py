from src.tools.rag_tool import rag_tool 
from src.models.chat_model import get_chat_model
from src.models.summarisation_model import get_summarization_model
from src.tools.web_search_tool import web_search
from src.agent.aiAgent import Agent
import streamlit as st
from config import SYSTEM_PROMPT
from config import REGION_NAME
from config import THREAD_TABLE_NAME


@st.cache_resource
def get_agent():
    tools=[rag_tool,web_search]
    chat_model=get_chat_model()
    summarizer_model=get_summarization_model()
    agent=Agent(model=chat_model, tools=tools,table_name=THREAD_TABLE_NAME,region_name=REGION_NAME , system_prompt=SYSTEM_PROMPT,summarizer_model=summarizer_model)
    return agent