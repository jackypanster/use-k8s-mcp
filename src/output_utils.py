"""
K8s MCP Agent 统一输出工具
标准化所有错误、状态和信息输出，支持精简模式
"""

import os
from typing import Optional, Any
from enum import Enum


class OutputLevel(Enum):
    """输出详细度级别"""
    SILENT = 0     # 静默模式，只输出关键错误
    MINIMAL = 1    # 最小模式，只输出核心状态
    NORMAL = 2     # 正常模式，输出必要信息
    VERBOSE = 3    # 详细模式，输出调试信息


class OutputFormatter:
    """统一输出格式化器"""
    
    def __init__(self, level: OutputLevel = OutputLevel.NORMAL):
        self.level = level
        # 从环境变量读取输出级别
        env_level = os.getenv('K8S_MCP_OUTPUT_LEVEL', 'normal').upper()
        if hasattr(OutputLevel, env_level):
            self.level = getattr(OutputLevel, env_level)
    
    def should_output(self, required_level: OutputLevel) -> bool:
        """判断是否应该输出"""
        return self.level.value >= required_level.value
    
    def success(self, message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.MINIMAL):
        """成功状态输出"""
        if not self.should_output(level):
            return
        
        if detail and self.level.value >= OutputLevel.NORMAL.value:
            print(f"✅ {message} | {detail}")
        else:
            print(f"✅ {message}")
    
    def error(self, message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.MINIMAL):
        """错误状态输出"""
        if not self.should_output(level):
            return
        
        if detail:
            print(f"❌ {message} - {detail}")
        else:
            print(f"❌ {message}")
    
    def warning(self, message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.NORMAL):
        """警告状态输出"""
        if not self.should_output(level):
            return
        
        if detail and self.level.value >= OutputLevel.VERBOSE.value:
            print(f"⚠️ {message} - {detail}")
        else:
            print(f"⚠️ {message}")
    
    def info(self, message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.NORMAL):
        """信息状态输出"""
        if not self.should_output(level):
            return
        
        if detail and self.level.value >= OutputLevel.VERBOSE.value:
            print(f"ℹ️ {message} - {detail}")
        else:
            print(f"ℹ️ {message}")
    
    def debug(self, message: str, detail: Optional[str] = None):
        """调试信息输出"""
        if not self.should_output(OutputLevel.VERBOSE):
            return
        
        if detail:
            print(f"🔧 [DEBUG] {message} - {detail}")
        else:
            print(f"🔧 [DEBUG] {message}")
    
    def fatal(self, operation: str, error: str, guide: Optional[str] = None):
        """致命错误输出（始终显示）"""
        print(f"❌ 致命错误: {operation}失败 - {error}")
        if guide and self.level.value >= OutputLevel.NORMAL.value:
            print(f"💡 {guide}")


# 全局输出器实例
_global_formatter = OutputFormatter()


def set_output_level(level: OutputLevel):
    """设置全局输出级别"""
    global _global_formatter
    _global_formatter.level = level


def success(message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.MINIMAL):
    """全局成功输出函数"""
    _global_formatter.success(message, detail, level)


def error(message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.MINIMAL):
    """全局错误输出函数"""
    _global_formatter.error(message, detail, level)


def warning(message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.NORMAL):
    """全局警告输出函数"""
    _global_formatter.warning(message, detail, level)


def info(message: str, detail: Optional[str] = None, level: OutputLevel = OutputLevel.NORMAL):
    """全局信息输出函数"""
    _global_formatter.info(message, detail, level)


def debug(message: str, detail: Optional[str] = None):
    """全局调试输出函数"""
    _global_formatter.debug(message, detail)


def fatal(operation: str, error: str, guide: Optional[str] = None):
    """全局致命错误输出函数"""
    _global_formatter.fatal(operation, error, guide)


# 标准化的错误类型和指导信息
class StandardErrors:
    """标准错误类型和指导信息"""
    
    MCP_CONNECTION = {
        "operation": "MCP服务器连接",
        "guide": "请确保MCP服务器运行正常且网络连接畅通"
    }
    
    CONFIG_VALIDATION = {
        "operation": "环境配置验证",
        "guide": "请检查 .env 文件中的配置变量"
    }
    
    LLM_INITIALIZATION = {
        "operation": "LLM初始化",
        "guide": "请检查 LLM 配置和API密钥"
    }
    
    CLUSTER_SCAN = {
        "operation": "集群扫描",
        "guide": "请检查集群连接和权限配置"
    }
    
    TOOL_DISCOVERY = {
        "operation": "工具发现",
        "guide": "请确保MCP工具服务正常运行"
    }
    
    DATA_VALIDATION = {
        "operation": "数据验证", 
        "guide": "请检查输入数据的完整性和格式"
    }


def standard_fatal_error(error_type: dict, error_detail: str):
    """标准化致命错误输出"""
    fatal(error_type["operation"], error_detail, error_type["guide"]) 