"""
MCP工具选择器
专注于基于用户需求智能选择合适的工具
遵循单一职责原则，文件大小控制在150行以内
"""

import re
import time
from typing import Dict, List, Optional, Any

from .models import (
    ToolCapabilities, ToolSelectionCriteria, ToolRanking,
    K8S_RESOURCE_TYPES, K8S_OPERATION_TYPES
)
from src.cache import CacheManager


class ToolSelectionError(Exception):
    """工具选择失败异常"""
    pass


class ToolSelector:
    """工具选择器 - 专注智能工具选择和排序"""
    
    def __init__(self, cache_manager: CacheManager) -> None:
        """初始化工具选择器
        
        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache_manager = cache_manager
        self.selection_count = 0
    
    def select_best_tool(
        self,
        intent: str,
        resource_type: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> Optional[str]:
        """选择最佳工具

        Args:
            intent: 用户意图描述
            resource_type: 目标资源类型
            operation_type: 操作类型

        Returns:
            最佳工具名称，未找到时返回None

        Raises:
            ToolSelectionError: 工具选择失败时抛出
        """
        start_time = time.time()

        try:
            # 执行工具选择流程
            best_tool = self._execute_selection_process(
                intent, resource_type, operation_type
            )

            self.selection_count += 1
            return best_tool

        except Exception as e:
            raise ToolSelectionError(f"工具选择失败: {e}") from e

    def _execute_selection_process(
        self,
        intent: str,
        resource_type: Optional[str],
        operation_type: Optional[str]
    ) -> Optional[str]:
        """执行工具选择流程"""
        # 解析用户意图
        parsed_intent = self._parse_user_intent(intent)

        # 合并显式参数和解析的意图
        final_resource_type = resource_type or parsed_intent.get('resource_type')
        final_operation_type = operation_type or parsed_intent.get('operation_type')

        # 获取兼容工具
        compatible_tools = self.get_compatible_tools(
            final_resource_type,
            final_operation_type
        )

        if not compatible_tools:
            return None

        # 排序工具
        ranked_tools = self.rank_tools_by_relevance(
            compatible_tools,
            {
                'intent': intent,
                'resource_type': final_resource_type,
                'operation_type': final_operation_type
            }
        )

        return ranked_tools[0].tool_name if ranked_tools else None
    
    def get_compatible_tools(
        self,
        resource_type: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> List[str]:
        """获取兼容工具列表
        
        Args:
            resource_type: 资源类型
            operation_type: 操作类型
            
        Returns:
            兼容的工具名称列表
        """
        try:
            # 从缓存获取所有工具
            tools = self.cache_manager.list_records('mcp_tools')
            
            compatible_tools = []
            
            for tool in tools:
                # 检查资源类型兼容性
                if resource_type:
                    tool_resources = tool.resource_types or []
                    if not any(resource_type.lower() in res.lower() for res in tool_resources):
                        continue
                
                # 检查操作类型兼容性
                if operation_type:
                    tool_operations = tool.operation_types or []
                    if not any(operation_type.lower() in op.lower() for op in tool_operations):
                        continue
                
                compatible_tools.append(tool.name)
            
            return compatible_tools
            
        except Exception as e:
            raise ToolSelectionError(f"获取兼容工具失败: {e}") from e
    
    def rank_tools_by_relevance(
        self,
        tool_names: List[str],
        context: Dict[str, Any]
    ) -> List[ToolRanking]:
        """按相关性排序工具
        
        Args:
            tool_names: 工具名称列表
            context: 上下文信息
            
        Returns:
            排序后的工具排名列表
        """
        rankings = []
        
        for tool_name in tool_names:
            # 获取工具信息
            tool = self.cache_manager.get_record('mcp_tools', name=tool_name)
            if not tool:
                continue
            
            # 计算相关性评分
            relevance_score = self._calculate_relevance_score(tool, context)
            
            # 生成匹配原因
            match_reasons = self._generate_match_reasons(tool, context)
            
            # 创建工具能力对象
            capabilities = ToolCapabilities(
                tool_name=tool.name,
                resource_types=tool.resource_types or [],
                operation_types=tool.operation_types or [],
                scope='resource',  # 默认值，实际应从工具信息中获取
                cache_friendly=True,  # 默认值
                complexity_score=5  # 默认值
            )
            
            ranking = ToolRanking(
                tool_name=tool_name,
                relevance_score=relevance_score,
                capabilities=capabilities,
                match_reasons=match_reasons
            )
            
            rankings.append(ranking)
        
        # 按相关性评分降序排序
        rankings.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return rankings
    
    def _parse_user_intent(self, intent: str) -> Dict[str, Optional[str]]:
        """解析用户意图"""
        intent_lower = intent.lower()
        
        # 推断资源类型
        resource_type = None
        for resource in K8S_RESOURCE_TYPES:
            if resource in intent_lower:
                resource_type = resource
                break
        
        # 推断操作类型
        operation_type = None
        for operation in K8S_OPERATION_TYPES:
            if operation in intent_lower:
                operation_type = operation
                break
        
        return {
            'resource_type': resource_type,
            'operation_type': operation_type
        }
    
    def _calculate_relevance_score(
        self,
        tool: Any,
        context: Dict[str, Any]
    ) -> float:
        """计算工具相关性评分"""
        score = 0.0
        
        # 基础评分
        score += 0.1
        
        # 资源类型匹配
        resource_type = context.get('resource_type')
        if resource_type and tool.resource_types:
            if any(resource_type.lower() in res.lower() for res in tool.resource_types):
                score += 0.4
        
        # 操作类型匹配
        operation_type = context.get('operation_type')
        if operation_type and tool.operation_types:
            if any(operation_type.lower() in op.lower() for op in tool.operation_types):
                score += 0.3
        
        # 工具名称相关性
        intent = context.get('intent', '')
        if intent:
            # 简单的关键词匹配
            intent_words = set(intent.lower().split())
            tool_words = set(tool.name.lower().split('_'))
            
            common_words = intent_words.intersection(tool_words)
            if common_words:
                score += 0.2 * len(common_words) / len(intent_words)
        
        return min(score, 1.0)
    
    def _generate_match_reasons(
        self,
        tool: Any,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成匹配原因列表"""
        reasons = []
        
        resource_type = context.get('resource_type')
        if resource_type and tool.resource_types:
            if any(resource_type.lower() in res.lower() for res in tool.resource_types):
                reasons.append(f"支持{resource_type}资源类型")
        
        operation_type = context.get('operation_type')
        if operation_type and tool.operation_types:
            if any(operation_type.lower() in op.lower() for op in tool.operation_types):
                reasons.append(f"支持{operation_type}操作")
        
        if not reasons:
            reasons.append("通用工具匹配")
        
        return reasons
    
    def get_selection_stats(self) -> Dict[str, int]:
        """获取选择统计信息"""
        return {
            'selection_count': self.selection_count
        }
