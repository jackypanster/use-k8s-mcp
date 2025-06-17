"""
Example script demonstrating Kubernetes-optimized ChatOpenAI configuration.
Shows how to use the precision-focused LLM for cluster management tasks.
"""

import asyncio
import os
from dotenv import load_dotenv
from k8s_config import get_k8s_llm, K8sValidation
from mcp_use import MCPAgent, MCPClient

async def main():
    """
    Demonstrate Kubernetes cluster management with precision-optimized LLM.
    """
    # Load environment variables
    load_dotenv()
    
    print("🚀 Kubernetes Cluster Management Demo")
    print("=" * 50)
    
    # MCP configuration for cluster operations
    config = {
        "mcpServers": {
            "fetch": {
                "type": "sse",
                "url": "https://mcp.api-inference.modelscope.net/da81fcffd39044/sse"
            }
        }
    }
    
    # Create MCP client
    client = MCPClient.from_dict(config)
    
    # Get production-grade Kubernetes LLM
    print("🔧 Initializing production-grade Kubernetes LLM...")
    llm = get_k8s_llm("production")
    
    print(f"✅ Model: {llm.model}")
    print(f"✅ Temperature: {llm.temperature} (deterministic)")
    print(f"✅ Max retries: {llm.max_retries}")
    print(f"✅ Context length: {llm.model_kwargs.get('max_context_length'):,} tokens")
    print(f"✅ Top-p: {llm.model_kwargs.get('top_p')} (strict)")
    
    # Create agent with the precision-optimized LLM
    agent = MCPAgent(llm=llm, client=client, max_steps=10)
    
    # Example Kubernetes operations
    k8s_tasks = [
        "Analyze the current status of all pods in the kube-system namespace",
        "Generate a deployment YAML for a nginx web server with 3 replicas",
        "Explain how to troubleshoot a CrashLoopBackOff pod status",
        "Create a service manifest to expose a deployment on port 80"
    ]
    
    print("\n🎯 Kubernetes Task Examples")
    print("-" * 30)
    
    for i, task in enumerate(k8s_tasks, 1):
        print(f"\n{i}. {task}")
        
        # Validate if this involves any commands
        if "kubectl" in task.lower():
            validation = K8sValidation.validate_k8s_command(task)
            print(f"   Safety check: {'✅ Safe' if validation['is_safe'] else '⚠️ Requires review'}")
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"   Warning: {warning}")
        
        try:
            # Execute the task with the precision-optimized LLM
            result = await agent.run(task, max_steps=5)
            
            # Show truncated result for demo
            result_preview = result[:200] + "..." if len(result) > 200 else result
            print(f"   Result: {result_preview}")
            
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    print("\n🛡️ Safety Features Demonstrated:")
    print("- Zero temperature for deterministic outputs")
    print("- Strict top-p (0.1) for reliable token selection")
    print("- Enhanced retry logic (5 attempts)")
    print("- Extended timeout (120s) for complex analysis")
    print("- Safety stop sequences to prevent dangerous commands")
    print("- Command validation for Kubernetes operations")
    
    print("\n✅ Demo completed successfully!")

def demonstrate_config_differences():
    """
    Show the differences between various environment configurations.
    """
    print("\n🔍 Configuration Comparison")
    print("=" * 40)
    
    environments = ["production", "development", "analysis"]
    
    for env in environments:
        llm = get_k8s_llm(env)
        print(f"\n{env.upper()} Configuration:")
        print(f"  Model: {llm.model}")
        print(f"  Temperature: {llm.temperature}")
        print(f"  Max retries: {llm.max_retries}")
        print(f"  Timeout: {llm.request_timeout}s")
        print(f"  Top-p: {llm.model_kwargs.get('top_p')}")
        print(f"  Context: {llm.model_kwargs.get('max_context_length'):,} tokens")

def validate_sample_commands():
    """
    Demonstrate command validation for Kubernetes operations.
    """
    print("\n🔒 Command Validation Examples")
    print("=" * 35)
    
    sample_commands = [
        "kubectl get pods -n kube-system",
        "kubectl delete pod suspicious-pod",
        "kubectl apply -f deployment.yaml",
        "kubectl logs my-app-pod",
        "kubectl drain node-1 --force",
        "rm -rf /var/lib/kubelet"
    ]
    
    for cmd in sample_commands:
        validation = K8sValidation.validate_k8s_command(cmd)
        status = "✅ SAFE" if validation['is_safe'] else "⚠️ DANGEROUS"
        risk = validation['risk_level'].upper()
        
        print(f"\nCommand: {cmd}")
        print(f"Status: {status} (Risk: {risk})")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")
        
        if validation['recommendations']:
            for rec in validation['recommendations']:
                print(f"  💡 {rec}")

if __name__ == "__main__":
    print("🔧 Kubernetes LLM Configuration Demo")
    print("=" * 50)
    
    # Show configuration differences
    demonstrate_config_differences()
    
    # Show command validation
    validate_sample_commands()
    
    # Run the main async demo
    print("\n🚀 Starting async Kubernetes operations demo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("💡 Make sure your OPENROUTER_API_KEY is set in .env file")
