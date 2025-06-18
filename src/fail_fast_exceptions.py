"""
K8s MCP Agent Fail Fast异常处理模块
实现数据真实性铁律中的Fail Fast原则
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExceptionContext:
    """标准化的异常上下文信息"""
    operation: str
    timestamp: str
    mcp_tool: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    cluster_name: Optional[str] = None
    resource_info: Optional[Dict[str, Any]] = None
    user_input: Optional[str] = None
    agent_step: Optional[int] = None
    system_state: Optional[Dict[str, Any]] = None
    original_error: Optional[str] = None


class K8sAgentException(Exception):
    """K8s MCP Agent基础异常类"""
    
    def __init__(self, message: str, context: ExceptionContext):
        super().__init__(message)
        self.context = context
        self.creation_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录"""
        return {
            "message": str(self),
            "context": self.context.__dict__,
            "creation_time": self.creation_time,
            "exception_type": self.__class__.__name__
        }


class MCPConnectionError(K8sAgentException):
    """MCP连接失败 - 必须立即终止程序"""
    pass


class ToolCallError(K8sAgentException):
    """MCP工具调用失败 - 立即终止当前操作"""
    pass


class DataValidationError(K8sAgentException):
    """数据验证失败 - 立即终止并报告"""
    pass


class ClusterPermissionError(K8sAgentException):
    """集群访问权限不足 - 立即终止并要求检查权限"""
    pass


class ClusterAccessError(K8sAgentException):
    """集群访问失败 - 立即终止并检查连接"""
    pass


class ToolUnavailableError(K8sAgentException):
    """关键工具不可用 - 立即终止操作"""
    pass


class FailFastValidator:
    """Fail Fast原则验证器"""
    
    @staticmethod
    def validate_exception_timing(start_time: float, max_delay: float = 0.1) -> None:
        """验证异常抛出的及时性"""
        elapsed = time.time() - start_time
        if elapsed > max_delay:
            raise RuntimeError(
                f"异常抛出延迟过长: {elapsed:.3f}s > {max_delay}s，违反Fail Fast原则"
            )
    
    @staticmethod
    def validate_exception_context(context: ExceptionContext) -> None:
        """验证异常上下文的完整性"""
        required_fields = ['operation', 'timestamp']
        missing_fields = [field for field in required_fields if not getattr(context, field)]
        
        if missing_fields:
            raise ValueError(f"异常上下文缺少必要字段: {missing_fields}")
    
    @staticmethod
    def detect_fallback_pattern(code_location: str, behavior: str) -> None:
        """检测fallback模式违规"""
        forbidden_patterns = [
            "default_value",
            "fallback_response", 
            "graceful_degradation",
            "retry_with_default",
            "ignore_error"
        ]
        
        if any(pattern in behavior.lower() for pattern in forbidden_patterns):
            raise RuntimeError(
                f"检测到禁止的fallback模式在 {code_location}: {behavior}"
            )


def create_exception_context(operation: str, **kwargs) -> ExceptionContext:
    """创建标准化的异常上下文"""
    return ExceptionContext(
        operation=operation,
        timestamp=datetime.utcnow().isoformat(),
        mcp_tool=kwargs.get('mcp_tool'),
        tool_params=kwargs.get('tool_params'),
        cluster_name=kwargs.get('cluster_name'),
        resource_info=kwargs.get('resource_info'),
        user_input=kwargs.get('user_input'),
        agent_step=kwargs.get('agent_step'),
        system_state=kwargs.get('system_state'),
        original_error=kwargs.get('original_error')
    )


def fail_fast_mcp_call(tool_name: str, params: Dict[str, Any], **context_kwargs):
    """
    执行MCP工具调用，严格遵循Fail Fast原则
    
    Args:
        tool_name: MCP工具名称
        params: 工具调用参数
        **context_kwargs: 异常上下文信息
    
    Raises:
        ToolCallError: 工具调用失败时立即抛出
    """
    start_time = time.time()
    
    try:
        # 这里应该是实际的MCP工具调用逻辑
        # result = actual_mcp_call(tool_name, params)
        
        # 模拟工具调用（实际实现时替换）
        if not params:
            raise Exception("参数不能为空")
        
        # 验证异常抛出及时性
        FailFastValidator.validate_exception_timing(start_time)
        
        return {"success": True, "data": "模拟数据"}
        
    except Exception as e:
        # 创建详细的异常上下文
        context = create_exception_context(
            operation=f"mcp_tool_call_{tool_name}",
            mcp_tool=tool_name,
            tool_params=params,
            original_error=str(e),
            **context_kwargs
        )
        
        # 验证上下文完整性
        FailFastValidator.validate_exception_context(context)
        
        # 立即抛出异常，不进行任何fallback
        raise ToolCallError(f"MCP工具 {tool_name} 调用失败: {e}", context) from e


def fail_fast_data_validation(data: Any, validation_rules: Dict[str, Any], **context_kwargs):
    """
    执行数据验证，严格遵循Fail Fast原则
    
    Args:
        data: 待验证的数据
        validation_rules: 验证规则
        **context_kwargs: 异常上下文信息
    
    Raises:
        DataValidationError: 数据验证失败时立即抛出
    """
    start_time = time.time()
    
    try:
        # 执行数据验证逻辑
        if not data:
            raise ValueError("数据不能为空")
        
        if 'required_fields' in validation_rules:
            missing_fields = []
            for field in validation_rules['required_fields']:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValueError(f"缺少必要字段: {missing_fields}")
        
        # 验证异常抛出及时性
        FailFastValidator.validate_exception_timing(start_time)
        
        return True
        
    except Exception as e:
        # 创建详细的异常上下文
        context = create_exception_context(
            operation="data_validation",
            original_error=str(e),
            **context_kwargs
        )
        
        # 立即抛出异常，不进行任何修复或默认值处理
        raise DataValidationError(f"数据验证失败: {e}", context) from e


def fail_fast_cluster_access(cluster_name: str, operation: str, **context_kwargs):
    """
    执行集群访问，严格遵循Fail Fast原则
    
    Args:
        cluster_name: 集群名称
        operation: 操作类型
        **context_kwargs: 异常上下文信息
    
    Raises:
        ClusterAccessError: 集群访问失败时立即抛出
        ClusterPermissionError: 权限不足时立即抛出
    """
    start_time = time.time()
    
    try:
        # 模拟集群访问检查
        if not cluster_name:
            raise ValueError("集群名称不能为空")
        
        # 模拟权限检查
        if cluster_name == "restricted_cluster":
            raise PermissionError("权限不足")
        
        # 验证异常抛出及时性
        FailFastValidator.validate_exception_timing(start_time)
        
        return {"cluster": cluster_name, "accessible": True}
        
    except PermissionError as e:
        context = create_exception_context(
            operation=f"cluster_access_{operation}",
            cluster_name=cluster_name,
            original_error=str(e),
            **context_kwargs
        )
        raise ClusterPermissionError(f"集群 {cluster_name} 权限不足: {e}", context) from e
        
    except Exception as e:
        context = create_exception_context(
            operation=f"cluster_access_{operation}",
            cluster_name=cluster_name,
            original_error=str(e),
            **context_kwargs
        )
        raise ClusterAccessError(f"集群 {cluster_name} 访问失败: {e}", context) from e


# 使用示例和测试
if __name__ == "__main__":
    # 测试Fail Fast原则的实施
    try:
        # 测试工具调用失败
        fail_fast_mcp_call("GET_CLUSTER_INFO", {}, cluster_name="test-cluster")
    except ToolCallError as e:
        print(f"✅ 正确捕获工具调用异常: {e}")
        print(f"   上下文: {e.context}")
    
    try:
        # 测试数据验证失败
        fail_fast_data_validation({}, {"required_fields": ["name", "version"]})
    except DataValidationError as e:
        print(f"✅ 正确捕获数据验证异常: {e}")
    
    try:
        # 测试集群访问失败
        fail_fast_cluster_access("restricted_cluster", "get_pods")
    except ClusterPermissionError as e:
        print(f"✅ 正确捕获权限异常: {e}")
