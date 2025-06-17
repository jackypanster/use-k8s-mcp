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

    # Create LLM optimized for Kubernetes cluster management
    # Configuration prioritizes precision, reliability, and deterministic outputs
    llm = ChatOpenAI(
        model="openai/gpt-3.5-turbo",  # Reliable model with good tool support
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4096,  # Sufficient for detailed K8s configurations
        temperature=0.0,  # CRITICAL: Eliminate randomness for consistent commands
        top_p=0.1,  # STRICT: Use only most probable tokens
        frequency_penalty=0.0,  # No creative variations for infrastructure
        presence_penalty=0.0,  # Avoid unexpected token choices
        max_retries=5,  # Enhanced reliability for critical operations
        request_timeout=120,  # Allow time for complex cluster analysis
        streaming=False,  # Disable streaming for complete, validated responses
        # Additional safety parameters for production environments
        stop=["```bash", "```sh", "rm -rf", "kubectl delete"],  # Prevent unsafe commands
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
