import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient


async def main():
    """Run the example using a configuration file."""
    # Load environment variables
    load_dotenv()

    config = {
        "mcpServers": {
            "fetch": {
                "type": "sse",
                "url": "https://mcp.api-inference.modelscope.net/da81fcffd39044/sse"
            }
        }
    }

    # Create MCPClient from config file
    client = MCPClient.from_dict(config)

    # Create LLM with OpenRouter configuration
    llm = ChatOpenAI(
        model="qwen/qwen3-32b",  # Use GPT-3.5 which supports tool use
        api_key=os.getenv("OPENROUTER_API_KEY"),  # Your OpenRouter API key
        base_url="https://openrouter.ai/api/v1",  # OpenRouter base URL
    )

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run(
        "fetch page https://www.ruanyifeng.com/blog/",
        max_steps=30,
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    # Run the appropriate example
    asyncio.run(main())
