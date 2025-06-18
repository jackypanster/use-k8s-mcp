"""
MCP工具能力分析器
专注于分析工具的K8s操作能力和资源类型支持
遵循单一职责原则，文件大小控制在150行以内
"""

import re
import time
from typing import Dict, Any, List, Set

from .models import ToolCapabilities, ToolSchema, K8S_RESOURCE_TYPES, K8S_OPERATION_TYPES
from .exceptions import CapabilityAnalysisError
from ..fail_fast_exceptions import create_exception_context


class CapabilityAnalyzer:
    """工具能力分析器 - 专注K8s能力分析和推断"""
    
    # 资源类型匹配模式
    RESOURCE_PATTERNS = {
        'pod': ['pod', 'container', 'workload'],
        'service': ['service', 'svc', 'endpoint'],
        'deployment': ['deployment', 'deploy', 'app'],
        'node': ['node', 'worker', 'machine'],
        'namespace': ['namespace', 'ns', 'project'],
        'cluster': ['cluster', 'master', 'control-plane'],
        'configmap': ['configmap', 'config', 'cm'],
        'secret': ['secret', 'credential'],
        'ingress': ['ingress', 'route', 'gateway'],
        'persistentvolume': ['pv', 'volume', 'storage'],
        'job': ['job', 'task', 'batch'],
        'cronjob': ['cronjob', 'cron', 'schedule']
    }
    
    # 操作类型匹配模式
    OPERATION_PATTERNS = {
        'list': ['list', 'get', 'show', 'describe', 'find'],
        'create': ['create', 'add', 'new', 'deploy', 'apply'],
        'update': ['update', 'edit', 'modify', 'patch', 'set'],
        'delete': ['delete', 'remove', 'destroy', 'rm'],
        'scale': ['scale', 'resize', 'replicas'],
        'logs': ['logs', 'log', 'tail', 'output'],
        'exec': ['exec', 'run', 'execute', 'shell'],
        'rollout': ['rollout', 'restart', 'undo'],
        'top': ['top', 'metrics', 'usage', 'stats']
    }
    
    def __init__(self) -> None:
        """初始化能力分析器"""
        self.analyzed_count = 0
        self.error_count = 0
    
    def analyze_tool_capabilities(
        self,
        tool_schema: ToolSchema
    ) -> ToolCapabilities:
        """分析工具能力

        Args:
            tool_schema: 工具schema对象

        Returns:
            工具能力分析结果

        Raises:
            CapabilityAnalysisError: 能力分析失败时抛出
        """
        start_time = time.time()

        try:
            # 执行核心分析
            analysis_result = self._perform_core_analysis(tool_schema)

            # 创建能力对象
            capabilities = ToolCapabilities(**analysis_result)

            self.analyzed_count += 1
            return capabilities

        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation=f"analyze_tool_capabilities_{tool_schema.name}",
                tool_name=tool_schema.name,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise CapabilityAnalysisError(f"工具能力分析失败: {e}", context) from e

    def _perform_core_analysis(self, tool_schema: ToolSchema) -> Dict[str, Any]:
        """执行核心分析逻辑"""
        # 推断资源类型
        resource_types = self.infer_resource_types(
            tool_schema.name,
            tool_schema.description
        )

        # 推断操作类型
        operation_types = self.infer_operation_types(
            tool_schema.name,
            tool_schema.input_schema
        )

        # 推断作用域
        scope = self._infer_scope(tool_schema.name, resource_types)

        # 评估缓存友好性
        cache_friendly = self._evaluate_cache_friendliness(operation_types)

        # 计算复杂度评分
        complexity_score = self._calculate_complexity_score(tool_schema)

        # 计算置信度
        confidence_score = self._calculate_confidence_score(
            tool_schema.name,
            tool_schema.description,
            resource_types,
            operation_types
        )

        return {
            'tool_name': tool_schema.name,
            'resource_types': resource_types,
            'operation_types': operation_types,
            'scope': scope,
            'cache_friendly': cache_friendly,
            'complexity_score': complexity_score,
            'confidence_score': confidence_score
        }
    
    def infer_resource_types(self, tool_name: str, description: str) -> List[str]:
        """推断支持的资源类型"""
        resource_types: Set[str] = set()
        text = f"{tool_name} {description}".lower()
        
        for resource, patterns in self.RESOURCE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    resource_types.add(resource)
        
        # 如果没有匹配到具体资源，尝试通用匹配
        if not resource_types:
            for k8s_resource in K8S_RESOURCE_TYPES:
                if k8s_resource in text:
                    resource_types.add(k8s_resource)
        
        return list(resource_types)
    
    def infer_operation_types(
        self, 
        tool_name: str, 
        input_schema: Dict[str, Any]
    ) -> List[str]:
        """推断操作类型"""
        operation_types: Set[str] = set()
        text = tool_name.lower()
        
        # 从工具名称推断
        for operation, patterns in self.OPERATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    operation_types.add(operation)
        
        # 从参数名称推断
        properties = input_schema.get('properties', {})
        for param_name in properties.keys():
            param_lower = param_name.lower()
            for operation, patterns in self.OPERATION_PATTERNS.items():
                for pattern in patterns:
                    if pattern in param_lower:
                        operation_types.add(operation)
        
        # 如果没有匹配到，默认为查询操作
        if not operation_types:
            operation_types.add('list')
        
        return list(operation_types)
    
    def _infer_scope(self, tool_name: str, resource_types: List[str]) -> str:
        """推断工具作用域"""
        name_lower = tool_name.lower()
        
        # 从工具名称推断
        if any(keyword in name_lower for keyword in ['cluster', 'master', 'control']):
            return 'cluster'
        
        if any(keyword in name_lower for keyword in ['namespace', 'ns', 'project']):
            return 'namespace'
        
        if any(keyword in name_lower for keyword in ['node', 'worker', 'machine']):
            return 'node'
        
        if any(keyword in name_lower for keyword in ['pod', 'container']):
            return 'pod'
        
        # 从资源类型推断
        if 'cluster' in resource_types:
            return 'cluster'
        elif 'namespace' in resource_types:
            return 'namespace'
        elif 'node' in resource_types:
            return 'node'
        elif 'pod' in resource_types:
            return 'pod'
        
        # 默认为资源级别
        return 'resource'
    
    def _evaluate_cache_friendliness(self, operation_types: List[str]) -> bool:
        """评估是否适合缓存"""
        # 只读操作适合缓存
        read_operations = {'list', 'get', 'describe', 'show', 'top', 'logs'}
        
        # 如果所有操作都是只读的，则适合缓存
        return all(op in read_operations for op in operation_types)
    
    def _calculate_complexity_score(self, tool_schema: ToolSchema) -> int:
        """计算复杂度评分 (1-10)"""
        score = 1
        
        # 基于参数数量
        total_params = len(tool_schema.required_params or []) + len(tool_schema.optional_params or [])
        if total_params > 10:
            score += 3
        elif total_params > 5:
            score += 2
        elif total_params > 2:
            score += 1
        
        # 基于必需参数数量
        required_count = len(tool_schema.required_params or [])
        if required_count > 5:
            score += 2
        elif required_count > 3:
            score += 1
        
        # 基于schema复杂度
        if self._has_nested_objects(tool_schema.input_schema):
            score += 2
        
        return min(score, 10)
    
    def _calculate_confidence_score(
        self,
        tool_name: str,
        description: str,
        resource_types: List[str],
        operation_types: List[str]
    ) -> float:
        """计算分析置信度 (0.0-1.0)"""
        confidence = 0.5  # 基础置信度
        
        # 如果有明确的资源类型匹配，增加置信度
        if resource_types:
            confidence += 0.2
        
        # 如果有明确的操作类型匹配，增加置信度
        if operation_types and 'list' not in operation_types:  # 排除默认的list操作
            confidence += 0.2
        
        # 如果工具名称包含K8s相关关键词，增加置信度
        k8s_keywords = ['k8s', 'kubectl', 'kubernetes', 'kube']
        if any(keyword in tool_name.lower() for keyword in k8s_keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _has_nested_objects(self, schema: Dict[str, Any]) -> bool:
        """检查schema是否包含嵌套对象"""
        properties = schema.get('properties', {})
        
        for prop_schema in properties.values():
            if isinstance(prop_schema, dict):
                if prop_schema.get('type') == 'object':
                    return True
                if prop_schema.get('type') == 'array':
                    items = prop_schema.get('items', {})
                    if isinstance(items, dict) and items.get('type') == 'object':
                        return True
        
        return False
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        return {
            'analyzed_count': self.analyzed_count,
            'error_count': self.error_count,
            'success_rate': (
                self.analyzed_count / max(1, self.analyzed_count + self.error_count)
            ) * 100
        }
