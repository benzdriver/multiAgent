from dotenv import load_dotenv
load_dotenv()
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    agent = AssistantAgent("assistant", model_client=model_client)
    ask = "中国人为什么又叫黄皮肤"
    result = await agent.run(messages=[{"role": "user", "content": ask}])
    print(result)
    await model_client.close()

asyncio.run(main())