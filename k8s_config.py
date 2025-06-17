"""
Kubernetes-optimized ChatOpenAI configurations for maximum precision and reliability.
Designed for production infrastructure operations with strict deterministic outputs.
"""

import os
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List

class K8sLLMConfig:
    """
    Kubernetes-specific LLM configurations prioritizing safety and precision.
    """
    
    # Safety stop sequences to prevent dangerous command execution
    SAFETY_STOP_SEQUENCES = [
        "```bash",
        "```sh", 
        "```shell",
        "rm -rf",
        "kubectl delete",
        "docker rmi",
        "sudo rm"
    ]
    
    # Models ranked by infrastructure task performance
    INFRASTRUCTURE_MODELS = {
        "claude-3-5-sonnet": {
            "model": "anthropic/claude-3-5-sonnet",
            "context_length": 200000,
            "strengths": ["code analysis", "yaml parsing", "complex reasoning"],
            "cost": "medium"
        },
        "gpt-4-turbo": {
            "model": "openai/gpt-4-turbo",
            "context_length": 128000,
            "strengths": ["precise instructions", "error analysis"],
            "cost": "high"
        },
        "qwen-coder": {
            "model": "qwen/qwen2.5-coder-32b-instruct",
            "context_length": 131072,
            "strengths": ["code generation", "debugging"],
            "cost": "low"
        }
    }

    @staticmethod
    def create_production_k8s_llm(model_choice: str = "claude-3-5-sonnet") -> ChatOpenAI:
        """
        Create a production-ready LLM for Kubernetes operations.
        
        Args:
            model_choice: Model to use for K8s operations
            
        Returns:
            Configured ChatOpenAI instance optimized for infrastructure tasks
        """
        model_config = K8sLLMConfig.INFRASTRUCTURE_MODELS.get(model_choice)
        if not model_config:
            raise ValueError(f"Unknown model choice: {model_choice}")
        
        return ChatOpenAI(
            model=model_config["model"],
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",

            # Output configuration for detailed K8s responses
            max_tokens=4096,  # Sufficient for complex manifests and explanations

            # CRITICAL: Zero randomness for infrastructure operations
            temperature=0.0,  # Completely deterministic outputs

            # STRICT sampling parameters (moved from model_kwargs)
            top_p=0.1,  # Use only the most probable tokens

            # Eliminate creative variations (moved from model_kwargs)
            frequency_penalty=0.0,  # No repetition avoidance
            presence_penalty=0.0,   # No topic diversity

            # Safety and consistency
            streaming=False,  # Complete responses for validation
            stop=K8sLLMConfig.SAFETY_STOP_SEQUENCES,  # Prevent dangerous commands

            # Reliability configuration
            max_retries=5,  # Multiple retries for critical operations
            request_timeout=120,  # Extended timeout for complex analysis

            # Model-specific parameters (only supported ones)
            model_kwargs={
                # Additional deterministic parameters
                "seed": 42,  # Fixed seed for reproducible outputs (if supported)
                "top_k": 10,   # Limit token choices further (if supported)
            }
        )

    @staticmethod
    def create_development_k8s_llm() -> ChatOpenAI:
        """
        Create a development/testing LLM with slightly relaxed parameters.
        Still prioritizes accuracy but allows minimal creativity for explanations.
        """
        return ChatOpenAI(
            model="qwen/qwen2.5-coder-32b-instruct",  # Cost-effective for dev
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            max_tokens=3072,
            temperature=0.1,  # Minimal randomness for dev environment
            top_p=0.2,  # Slightly more flexible for explanations
            frequency_penalty=0.0,
            presence_penalty=0.0,
            streaming=False,
            stop=K8sLLMConfig.SAFETY_STOP_SEQUENCES,
            max_retries=3,
            request_timeout=90,
            model_kwargs={
                "seed": 42,
            }
        )

    @staticmethod
    def create_analysis_k8s_llm() -> ChatOpenAI:
        """
        Create an LLM optimized for cluster analysis and troubleshooting.
        Maximum context length for analyzing large log files and manifests.
        """
        return ChatOpenAI(
            model="anthropic/claude-3-5-sonnet",  # Best for analysis tasks
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            max_tokens=8192,  # Longer outputs for detailed analysis
            temperature=0.0,  # Strict determinism
            top_p=0.05,  # Even stricter token selection
            frequency_penalty=0.0,
            presence_penalty=0.0,
            streaming=False,
            stop=K8sLLMConfig.SAFETY_STOP_SEQUENCES,
            max_retries=5,
            request_timeout=180,  # Extended for large file analysis
            model_kwargs={
                "seed": 42,
            }
        )

# Validation functions for K8s operations
class K8sValidation:
    """
    Validation utilities for Kubernetes operations.
    """
    
    DANGEROUS_COMMANDS = [
        "kubectl delete",
        "kubectl apply --force",
        "rm -rf",
        "docker system prune",
        "kubectl drain --force",
        "kubectl cordon",
    ]
    
    SAFE_COMMANDS = [
        "kubectl get",
        "kubectl describe",
        "kubectl logs",
        "kubectl explain",
        "kubectl version",
        "kubectl cluster-info",
    ]
    
    @staticmethod
    def validate_k8s_command(command: str) -> Dict[str, Any]:
        """
        Validate a Kubernetes command for safety.
        
        Args:
            command: The kubectl command to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "is_safe": True,
            "risk_level": "low",
            "warnings": [],
            "recommendations": []
        }
        
        command_lower = command.lower().strip()
        
        # Check for dangerous commands
        for dangerous in K8sValidation.DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                result["is_safe"] = False
                result["risk_level"] = "high"
                result["warnings"].append(f"Contains dangerous command: {dangerous}")
        
        # Check for missing namespace specification
        if "kubectl" in command_lower and "-n " not in command_lower and "--namespace" not in command_lower:
            result["warnings"].append("No namespace specified - will use default namespace")
            result["recommendations"].append("Consider specifying namespace with -n or --namespace")
        
        # Check for missing dry-run on apply commands
        if "kubectl apply" in command_lower and "--dry-run" not in command_lower:
            result["risk_level"] = "medium"
            result["recommendations"].append("Consider using --dry-run=client first")
        
        return result

# Configuration presets for different environments
K8S_ENVIRONMENT_CONFIGS = {
    "production": {
        "llm_factory": K8sLLMConfig.create_production_k8s_llm,
        "validation_required": True,
        "auto_approve": False,
        "backup_required": True
    },
    "staging": {
        "llm_factory": K8sLLMConfig.create_production_k8s_llm,
        "validation_required": True,
        "auto_approve": False,
        "backup_required": False
    },
    "development": {
        "llm_factory": K8sLLMConfig.create_development_k8s_llm,
        "validation_required": False,
        "auto_approve": True,
        "backup_required": False
    },
    "analysis": {
        "llm_factory": K8sLLMConfig.create_analysis_k8s_llm,
        "validation_required": False,
        "auto_approve": False,
        "backup_required": False
    }
}

def get_k8s_llm(environment: str = "production") -> ChatOpenAI:
    """
    Get a Kubernetes-optimized LLM for the specified environment.
    
    Args:
        environment: Target environment (production, staging, development, analysis)
        
    Returns:
        Configured ChatOpenAI instance
    """
    config = K8S_ENVIRONMENT_CONFIGS.get(environment)
    if not config:
        raise ValueError(f"Unknown environment: {environment}")
    
    return config["llm_factory"]()

if __name__ == "__main__":
    # Example usage
    print("🔧 Kubernetes LLM Configuration Examples")
    print("=" * 50)
    
    # Production configuration
    prod_llm = get_k8s_llm("production")
    print(f"Production LLM: {prod_llm.model}")
    print(f"Temperature: {prod_llm.temperature}")
    print(f"Max retries: {prod_llm.max_retries}")
    print(f"Context length: {prod_llm.model_kwargs.get('max_context_length')}")
    
    # Validate a sample command
    sample_command = "kubectl get pods -n kube-system"
    validation = K8sValidation.validate_k8s_command(sample_command)
    print(f"\nCommand validation for: {sample_command}")
    print(f"Safe: {validation['is_safe']}")
    print(f"Risk level: {validation['risk_level']}")
