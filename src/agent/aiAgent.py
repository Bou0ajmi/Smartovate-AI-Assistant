from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph_checkpoint_aws import DynamoDBSaver

class Agent:
    def __init__(self, model, table_name, region_name, tools=None,
                system_prompt="You are a helpful assistant.",
                summarizer_model=None, max_tokens_before_summary=3000,
                messages_to_keep=8):

        tools = tools or []
        summarizer_model = summarizer_model or model

        self.checkpointer = DynamoDBSaver(
            table_name=table_name,
            region_name=region_name,
        )

        summarization = SummarizationMiddleware(
            model=summarizer_model,
            max_tokens_before_summary=max_tokens_before_summary,
            messages_to_keep=messages_to_keep
        )
        self.agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            middleware=[summarization],
            checkpointer=self.checkpointer
        )

    def invoke(self, user_input: str, thread_id: str) -> str:
        config = {"configurable": {"thread_id": thread_id}}
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )

        last_message = result["messages"][-1]
        content = last_message.content

        # Case 1: plain string content (typical final answer)
        if isinstance(content, str):
            return content

        # Case 2: list of content blocks (e.g. mixed text/tool_use/thinking)
        if isinstance(content, list):
            return "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )

        return ""

    def stream(self, user_input: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        for chunk, metadata in self.agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode="messages"
        ):
            # Only look at chunks coming from the "model" node
            if metadata.get("langgraph_node") != "model":
                continue

            content = chunk.content
            if not content:
                continue

            # content is a list of blocks; only keep 'text' type blocks
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        yield text