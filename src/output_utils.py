"""
K8s MCP Agent 统一输出工具
标准化所有错误、状态和信息输出，支持精简模式
"""

import os
from typing import Optional, Any
from enum import Enum
import time
from datetime import datetime


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


# 新增request/response日志功能
def request_log(component: str, action: str, request_data: str, max_length: int = 500):
    """记录请求日志"""
    truncated_data = request_data[:max_length] + "..." if len(request_data) > max_length else request_data
    print(f"🔄 [{component}] REQUEST: {action}")
    print(f"   📤 {truncated_data}")
    
def response_log(component: str, action: str, response_data: str, max_length: int = 500):
    """记录响应日志"""
    truncated_data = response_data[:max_length] + "..." if len(response_data) > max_length else response_data
    print(f"✅ [{component}] RESPONSE: {action}")
    print(f"   📥 {truncated_data}")
    
def error_log(component: str, action: str, error_msg: str):
    """记录错误日志"""
    print(f"❌ [{component}] ERROR: {action}")
    print(f"   🚨 {error_msg}")

def step_log(component: str, step_num: int, description: str):
    """记录步骤日志"""
    print(f"📍 [{component}] Step {step_num}: {description}")

# 全链路追踪日志系统
class ChainTracker:
    """调用链路追踪器"""
    def __init__(self):
        self.call_stack = []
        self.call_id = 0
        
    def start_call(self, component: str, operation: str, details: str = "") -> int:
        """开始一个调用"""
        self.call_id += 1
        call_info = {
            'id': self.call_id,
            'component': component,
            'operation': operation,
            'details': details,
            'start_time': time.time(),
            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
            'level': len(self.call_stack)
        }
        self.call_stack.append(call_info)
        
        indent = "  " * call_info['level']
        print(f"🚀 {indent}[{call_info['timestamp']}] #{call_info['id']} {component} → {operation}")
        if details:
            print(f"   {indent}📝 {details}")
        
        return self.call_id
    
    def end_call(self, call_id: int, result: str = "", error: str = ""):
        """结束一个调用"""
        if not self.call_stack:
            return
            
        call_info = None
        for i, call in enumerate(self.call_stack):
            if call['id'] == call_id:
                call_info = self.call_stack.pop(i)
                break
                
        if not call_info:
            return
            
        duration = time.time() - call_info['start_time']
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        indent = "  " * call_info['level']
        
        if error:
            print(f"❌ {indent}[{timestamp}] #{call_id} {call_info['component']} ✗ {call_info['operation']} ({duration:.3f}s)")
            print(f"   {indent}🚨 {error}")
        else:
            print(f"✅ {indent}[{timestamp}] #{call_id} {call_info['component']} ✓ {call_info['operation']} ({duration:.3f}s)")
            if result:
                truncated = result[:200] + "..." if len(result) > 200 else result
                print(f"   {indent}📤 {truncated}")

# 全局追踪器实例
_tracker = ChainTracker()

def chain_start(component: str, operation: str, details: str = "") -> int:
    """开始链路追踪"""
    return _tracker.start_call(component, operation, details)

def chain_end(call_id: int, result: str = "", error: str = ""):
    """结束链路追踪"""
    _tracker.end_call(call_id, result, error)

def llm_request(model: str, prompt: str, max_tokens: int = None):
    """LLM请求日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    truncated_prompt = prompt[:300] + "..." if len(prompt) > 300 else prompt
    print(f"🧠 [{timestamp}] LLM_REQUEST → {model}")
    if max_tokens:
        print(f"   📊 max_tokens: {max_tokens}")
    print(f"   💭 {truncated_prompt}")

def llm_response(model: str, response: str, tokens_used: int = None):
    """LLM响应日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    truncated_response = response[:300] + "..." if len(response) > 300 else response
    print(f"🧠 [{timestamp}] LLM_RESPONSE ← {model}")
    if tokens_used:
        print(f"   📊 tokens_used: {tokens_used}")
    print(f"   💬 {truncated_response}")

def mcp_tool_call(tool_name: str, params: dict):
    """MCP工具调用日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"🔧 [{timestamp}] MCP_TOOL_CALL → {tool_name}")
    print(f"   🔗 参数: {params}")

def mcp_tool_response(tool_name: str, result: str, success: bool = True):
    """MCP工具响应日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    status = "✅" if success else "❌"
    truncated_result = result[:300] + "..." if len(result) > 300 else result
    print(f"🔧 [{timestamp}] MCP_TOOL_RESPONSE {status} ← {tool_name}")
    print(f"   📋 {truncated_result}")

def agent_step(step_num: int, description: str, thinking: str = ""):
    """Agent步骤日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"🤖 [{timestamp}] AGENT_STEP_{step_num}: {description}")
    if thinking:
        truncated_thinking = thinking[:200] + "..." if len(thinking) > 200 else thinking
        print(f"   🤔 {truncated_thinking}")

def data_flow(from_component: str, to_component: str, data_type: str, size: int = None):
    """数据流转日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    size_info = f" ({size} chars)" if size else ""
    print(f"📊 [{timestamp}] DATA_FLOW: {from_component} → {to_component} | {data_type}{size_info}") 