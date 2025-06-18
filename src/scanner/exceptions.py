"""
扫描模块异常定义
遵循fail-fast原则和详细异常上下文
"""

from src.fail_fast_exceptions import K8sAgentException


class ScanError(K8sAgentException):
    """扫描操作失败异常
    
    当集群扫描过程中出现错误时抛出
    遵循fail-fast原则，立即终止操作
    """
    pass


class ResourceParseError(K8sAgentException):
    """资源解析失败异常
    
    当MCP工具返回的数据解析失败时抛出
    包含详细的解析错误信息和原始数据
    """
    pass


class ScanTimeoutError(K8sAgentException):
    """扫描超时异常
    
    当扫描操作超过预设时间限制时抛出
    包含超时时间和已完成的扫描进度
    """
    pass


class ClusterConnectionError(K8sAgentException):
    """集群连接失败异常
    
    当无法连接到目标K8s集群时抛出
    包含集群信息和连接错误详情
    """
    pass


class ToolNotFoundError(K8sAgentException):
    """工具未找到异常
    
    当所需的MCP工具不可用时抛出
    包含工具名称和可用工具列表
    """
    pass


class ScanValidationError(K8sAgentException):
    """扫描验证失败异常

    当扫描结果验证失败时抛出
    包含验证规则和失败原因
    """
    pass


class ToolDiscoveryError(K8sAgentException):
    """工具发现失败异常

    当MCP工具发现过程中出现错误时抛出
    包含发现错误详情和已发现的工具信息
    """
    pass
