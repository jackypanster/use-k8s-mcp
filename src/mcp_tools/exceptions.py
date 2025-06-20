"""
MCP工具预加载系统异常定义
遵循fail-fast原则和详细异常上下文
"""


class MCPConnectionError(Exception):
    """MCP服务器连接失败异常
    
    当无法连接到MCP服务器或连接中断时抛出
    遵循fail-fast原则，立即终止操作
    """
    pass


class ToolLoadError(Exception):
    """工具加载失败异常

    当工具发现或加载过程中出现错误时抛出
    包含详细的工具信息和错误上下文
    """
    pass


class SchemaParseError(Exception):
    """Schema解析失败异常

    当工具schema解析失败时抛出
    包含schema内容和解析错误详情
    """
    pass


class ToolValidationError(Exception):
    """工具验证失败异常

    当工具信息验证失败时抛出
    包含验证规则和失败原因
    """
    pass


class CapabilityAnalysisError(Exception):
    """能力分析失败异常

    当工具能力分析过程中出现错误时抛出
    包含分析上下文和错误详情
    """
    pass
