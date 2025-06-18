# MCP工具预加载器设计文档

## 1. 功能概述

### 1.1 设计目标
MCP工具预加载器负责在系统启动时扫描和缓存所有可用的K8s MCP工具，建立工具能力映射表，为后续的智能工具选择和参数建议提供基础数据。

### 1.2 核心功能
1. **工具发现**：连接MCP服务器，获取所有可用工具列表
2. **Schema解析**：解析每个工具的输入/输出schema和参数要求
3. **能力分析**：分析工具支持的K8s资源类型和操作类型
4. **数据缓存**：将工具信息存储到SQLite数据库中
5. **查询接口**：提供工具能力查询和智能选择功能

### 1.3 技术约束
- 遵循fail-fast原则：MCP连接失败时立即抛出异常
- 使用现有的缓存系统：复用已实现的CacheManager
- 支持异步操作：工具发现和schema解析使用异步模式
- 完整的错误处理：详细的异常上下文和重试机制

## 2. 架构设计

### 2.1 组件结构
```
src/mcp/
├── __init__.py              # 模块初始化
├── tool_loader.py           # 工具加载器主类
├── schema_parser.py         # Schema解析器
├── capability_analyzer.py   # 能力分析器
└── tool_selector.py         # 工具选择器
```

### 2.2 类设计

#### 2.2.1 MCPToolLoader
**职责**：协调工具发现、解析和缓存过程
**方法**：
- `load_tools() -> List[MCPToolInfo]`：加载所有工具
- `refresh_tool_cache() -> None`：刷新工具缓存
- `get_tool_count() -> int`：获取工具数量

#### 2.2.2 SchemaParser
**职责**：解析MCP工具的schema定义
**方法**：
- `parse_tool_schema(tool_data: Dict) -> ToolSchema`：解析工具schema
- `extract_parameters(schema: Dict) -> Tuple[List[str], List[str]]`：提取必需和可选参数
- `validate_schema(schema: Dict) -> bool`：验证schema有效性

#### 2.2.3 CapabilityAnalyzer
**职责**：分析工具的K8s操作能力
**方法**：
- `analyze_tool_capabilities(tool_info: Dict) -> ToolCapabilities`：分析工具能力
- `infer_resource_types(tool_name: str, description: str) -> List[str]`：推断支持的资源类型
- `infer_operation_types(tool_name: str, schema: Dict) -> List[str]`：推断操作类型

#### 2.2.4 ToolSelector
**职责**：基于用户需求智能选择合适的工具
**方法**：
- `select_best_tool(intent: str, resource_type: str) -> Optional[str]`：选择最佳工具
- `get_compatible_tools(resource_type: str, operation: str) -> List[str]`：获取兼容工具
- `rank_tools_by_relevance(tools: List[str], context: Dict) -> List[str]`：按相关性排序

## 3. 数据模型

### 3.1 ToolSchema
```python
@dataclass
class ToolSchema:
    """工具Schema数据模型"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    required_params: List[str]
    optional_params: List[str]
```

### 3.2 ToolCapabilities
```python
@dataclass
class ToolCapabilities:
    """工具能力数据模型"""
    tool_name: str
    resource_types: List[str]  # 支持的K8s资源类型
    operation_types: List[str]  # 支持的操作类型
    scope: str  # cluster, namespace, node
    cache_friendly: bool  # 是否适合缓存
    complexity_score: int  # 复杂度评分 (1-10)
```

## 4. API设计

### 4.1 MCPToolLoader API

```python
class MCPToolLoader:
    def __init__(
        self, 
        mcp_client: MCPClient,
        cache_manager: CacheManager,
        timeout: int = 30
    ) -> None:
        """初始化工具加载器"""
        
    async def load_tools(self) -> List[MCPToolInfo]:
        """加载所有MCP工具
        
        Returns:
            工具信息列表
            
        Raises:
            MCPConnectionError: MCP连接失败
            ToolLoadError: 工具加载失败
        """
        
    async def get_tool_capabilities(
        self, 
        tool_name: str
    ) -> Optional[ToolCapabilities]:
        """获取工具能力信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具能力信息，未找到时返回None
        """
        
    def refresh_tool_cache(self) -> None:
        """刷新工具缓存"""
```

### 4.2 ToolSelector API

```python
class ToolSelector:
    def select_tools_for_intent(
        self,
        user_intent: str,
        resource_type: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> List[str]:
        """根据用户意图选择工具
        
        Args:
            user_intent: 用户意图描述
            resource_type: 目标资源类型
            operation_type: 操作类型
            
        Returns:
            推荐的工具名称列表（按相关性排序）
        """
```

## 5. 工具能力映射规则

### 5.1 资源类型推断
```python
RESOURCE_TYPE_PATTERNS = {
    'pod': ['pod', 'container', 'workload'],
    'service': ['service', 'svc', 'endpoint'],
    'deployment': ['deployment', 'deploy', 'app'],
    'node': ['node', 'worker', 'machine'],
    'namespace': ['namespace', 'ns', 'project'],
    'cluster': ['cluster', 'master', 'control-plane']
}
```

### 5.2 操作类型推断
```python
OPERATION_TYPE_PATTERNS = {
    'list': ['list', 'get', 'show', 'describe'],
    'create': ['create', 'add', 'new', 'deploy'],
    'update': ['update', 'edit', 'modify', 'patch'],
    'delete': ['delete', 'remove', 'destroy'],
    'scale': ['scale', 'resize', 'replicas'],
    'logs': ['logs', 'log', 'tail']
}
```

## 6. 异常处理

### 6.1 异常类型定义
```python
class MCPConnectionError(K8sAgentException):
    """MCP服务器连接失败异常"""
    pass

class ToolLoadError(K8sAgentException):
    """工具加载失败异常"""
    pass

class SchemaParseError(K8sAgentException):
    """Schema解析失败异常"""
    pass
```

### 6.2 错误处理策略
1. **连接失败**：立即抛出异常，不进行重试
2. **部分工具加载失败**：记录错误，继续加载其他工具
3. **Schema解析失败**：跳过该工具，记录警告
4. **缓存写入失败**：抛出异常，确保数据一致性

## 7. 性能要求

### 7.1 性能指标
- **工具发现时间**：< 10秒（100个工具以内）
- **缓存写入时间**：< 5秒
- **工具查询响应时间**：< 100ms
- **内存使用**：< 50MB（工具元数据）

### 7.2 优化策略
- **并发加载**：并行处理多个工具的schema解析
- **增量更新**：只更新变化的工具信息
- **缓存预热**：系统启动时预加载常用工具
- **懒加载**：按需加载详细的schema信息

## 8. 测试策略

### 8.1 单元测试
- 每个组件的独立功能测试
- Mock MCP客户端进行离线测试
- 异常场景的完整覆盖

### 8.2 集成测试
- 与真实MCP服务器的连接测试
- 端到端的工具加载流程测试
- 缓存系统集成测试

### 8.3 性能测试
- 大量工具的加载性能测试
- 并发查询的响应时间测试
- 内存使用情况监控

## 9. 配置管理

### 9.1 环境变量
```bash
# MCP工具加载配置
MCP_TOOL_LOAD_TIMEOUT=30          # 工具加载超时时间
MCP_TOOL_CACHE_TTL=3600           # 工具缓存TTL（1小时）
MCP_TOOL_PARALLEL_LOAD=5          # 并行加载数量
MCP_TOOL_RETRY_COUNT=3            # 重试次数
```

### 9.2 工具过滤配置
```bash
# 工具过滤规则
MCP_TOOL_INCLUDE_PATTERNS=k8s_*,kubectl_*  # 包含模式
MCP_TOOL_EXCLUDE_PATTERNS=test_*,debug_*   # 排除模式
MCP_TOOL_MIN_COMPLEXITY=1                  # 最小复杂度
MCP_TOOL_MAX_COMPLEXITY=8                  # 最大复杂度
```

## 10. 实施计划

### 10.1 开发阶段
1. **阶段1**：实现基础的工具发现和缓存功能
2. **阶段2**：添加schema解析和能力分析
3. **阶段3**：实现智能工具选择算法
4. **阶段4**：性能优化和错误处理完善

### 10.2 验收标准
- [ ] 成功连接MCP服务器并获取工具列表
- [ ] 正确解析所有工具的schema信息
- [ ] 准确分析工具的K8s操作能力
- [ ] 工具信息成功缓存到数据库
- [ ] 提供快速的工具查询和选择功能
- [ ] 完整的异常处理和错误恢复
- [ ] 性能指标满足要求
- [ ] 测试覆盖率达到90%以上
