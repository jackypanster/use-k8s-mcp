"""
MCP工具预加载系统数据模型
定义工具schema、能力和选择相关的数据结构
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ToolSchema:
    """工具Schema数据模型"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    required_params: Optional[List[str]] = None
    optional_params: Optional[List[str]] = None
    
    def __post_init__(self) -> None:
        """初始化后处理，提取参数信息"""
        if self.required_params is None or self.optional_params is None:
            self._extract_parameters()
    
    def _extract_parameters(self) -> None:
        """从input_schema中提取参数信息"""
        if not isinstance(self.input_schema, dict):
            self.required_params = []
            self.optional_params = []
            return
        
        properties = self.input_schema.get('properties', {})
        required = self.input_schema.get('required', [])
        
        self.required_params = [param for param in required if param in properties]
        self.optional_params = [
            param for param in properties.keys() 
            if param not in required
        ]
    
    def get_parameter_info(self, param_name: str) -> Optional[Dict[str, Any]]:
        """获取参数详细信息
        
        Args:
            param_name: 参数名称
            
        Returns:
            参数信息字典，未找到时返回None
        """
        properties = self.input_schema.get('properties', {})
        return properties.get(param_name)
    
    def is_required_param(self, param_name: str) -> bool:
        """检查参数是否为必需参数"""
        return param_name in (self.required_params or [])


@dataclass
class ToolCapabilities:
    """工具能力数据模型"""
    tool_name: str
    resource_types: List[str]  # 支持的K8s资源类型
    operation_types: List[str]  # 支持的操作类型
    scope: str  # cluster, namespace, node, pod
    cache_friendly: bool  # 是否适合缓存
    complexity_score: int  # 复杂度评分 (1-10)
    confidence_score: float = 1.0  # 分析置信度 (0.0-1.0)
    
    def __post_init__(self) -> None:
        """验证数据有效性"""
        if not 1 <= self.complexity_score <= 10:
            raise ValueError(f"复杂度评分必须在1-10之间，当前值: {self.complexity_score}")
        
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"置信度必须在0.0-1.0之间，当前值: {self.confidence_score}")
        
        valid_scopes = {'cluster', 'namespace', 'node', 'pod', 'resource'}
        if self.scope not in valid_scopes:
            raise ValueError(f"无效的作用域: {self.scope}，有效值: {valid_scopes}")
    
    def supports_resource(self, resource_type: str) -> bool:
        """检查是否支持指定的资源类型"""
        return resource_type.lower() in [rt.lower() for rt in self.resource_types]
    
    def supports_operation(self, operation_type: str) -> bool:
        """检查是否支持指定的操作类型"""
        return operation_type.lower() in [ot.lower() for ot in self.operation_types]
    
    def is_compatible_with(
        self, 
        resource_type: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> bool:
        """检查工具是否与指定需求兼容"""
        if resource_type and not self.supports_resource(resource_type):
            return False
        
        if operation_type and not self.supports_operation(operation_type):
            return False
        
        return True


@dataclass
class ToolSelectionCriteria:
    """工具选择条件"""
    resource_type: Optional[str] = None
    operation_type: Optional[str] = None
    scope: Optional[str] = None
    cache_friendly: Optional[bool] = None
    max_complexity: Optional[int] = None
    min_confidence: Optional[float] = None
    
    def matches(self, capabilities: ToolCapabilities) -> bool:
        """检查工具能力是否匹配选择条件"""
        if self.resource_type and not capabilities.supports_resource(self.resource_type):
            return False
        
        if self.operation_type and not capabilities.supports_operation(self.operation_type):
            return False
        
        if self.scope and capabilities.scope != self.scope:
            return False
        
        if self.cache_friendly is not None and capabilities.cache_friendly != self.cache_friendly:
            return False
        
        if self.max_complexity and capabilities.complexity_score > self.max_complexity:
            return False
        
        if self.min_confidence and capabilities.confidence_score < self.min_confidence:
            return False
        
        return True


@dataclass
class ToolRanking:
    """工具排序结果"""
    tool_name: str
    relevance_score: float  # 相关性评分 (0.0-1.0)
    capabilities: ToolCapabilities
    match_reasons: List[str]  # 匹配原因列表
    
    def __post_init__(self) -> None:
        """验证评分有效性"""
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError(f"相关性评分必须在0.0-1.0之间，当前值: {self.relevance_score}")


# 常量定义
K8S_RESOURCE_TYPES = [
    'pod', 'service', 'deployment', 'replicaset', 'daemonset', 'statefulset',
    'job', 'cronjob', 'configmap', 'secret', 'persistentvolume', 'persistentvolumeclaim',
    'node', 'namespace', 'ingress', 'networkpolicy', 'serviceaccount',
    'role', 'rolebinding', 'clusterrole', 'clusterrolebinding',
    'horizontalpodautoscaler', 'verticalpodautoscaler', 'poddisruptionbudget'
]

K8S_OPERATION_TYPES = [
    'list', 'get', 'describe', 'create', 'apply', 'update', 'patch',
    'delete', 'scale', 'rollout', 'logs', 'exec', 'port-forward',
    'top', 'events', 'drain', 'cordon', 'uncordon'
]

SCOPE_HIERARCHY = {
    'cluster': 4,
    'namespace': 3,
    'node': 2,
    'pod': 1,
    'resource': 1
}
