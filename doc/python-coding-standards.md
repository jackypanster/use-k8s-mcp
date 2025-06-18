# K8s MCP Agent Python编码规范

## 1. 概述

本文档定义了K8s MCP Agent智能集群状态缓存系统项目的Python代码最佳实践规范，确保代码质量、可维护性和团队协作效率。

### 1.1 设计原则

- **单一职责原则**：每个模块、类、函数专注于单一功能
- **开放封闭原则**：对扩展开放，对修改封闭
- **依赖倒置原则**：依赖抽象而非具体实现
- **Fail-Fast原则**：立即抛出异常，提供详细上下文信息

### 1.2 适用范围

本规范适用于：
- 智能集群状态缓存系统的所有Python代码
- MCP工具集成模块
- Gemini 2.5 Flash LLM集成
- 测试代码和工具脚本

## 2. 代码组织规范

### 2.1 文件结构规范

#### 2.1.1 文件大小限制
```python
# ✅ 正确：单个文件不超过150行，专注单一功能
# src/cache/models.py - 数据模型定义
# src/cache/database.py - 数据库管理
# src/cache/cache_manager.py - 缓存操作

# ❌ 错误：单个文件包含多个不相关功能
# src/cache/everything.py - 包含模型、数据库、缓存管理
```

#### 2.1.2 模块导入规范
```python
# ✅ 正确：清晰的导入顺序和分组
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from sqlalchemy import create_engine
from pydantic import BaseModel

from ..fail_fast_exceptions import CacheOperationError
from .models import ClusterInfo, PodInfo

# ❌ 错误：混乱的导入顺序
from .models import ClusterInfo
import os
from sqlalchemy import create_engine
import sys
```

### 2.2 函数设计规范

#### 2.2.1 函数复杂度控制
```python
# ✅ 正确：函数不超过40行，参数不超过4个
def create_cache_record(
    table_name: str,
    data: Dict[str, Any],
    ttl_seconds: Optional[int] = None,
    validate: bool = True
) -> int:
    """创建缓存记录
    
    Args:
        table_name: 目标表名
        data: 记录数据
        ttl_seconds: TTL秒数，None使用默认值
        validate: 是否验证数据
        
    Returns:
        创建的记录ID
        
    Raises:
        CacheOperationError: 创建失败时抛出
    """
    if validate:
        _validate_record_data(table_name, data)
    
    ttl_expiry = _calculate_ttl_expiry(table_name, ttl_seconds)
    record_data = _prepare_record_data(data, ttl_expiry)
    
    return _insert_record(table_name, record_data)

# ❌ 错误：函数过长，参数过多
def create_cache_record_with_validation_and_ttl_and_metadata(
    table_name, data, ttl_seconds, validate, metadata, 
    cluster_name, namespace, labels, annotations
):
    # 80行的复杂实现...
```

#### 2.2.2 类型注解要求
```python
# ✅ 正确：完整的类型注解
from typing import Dict, List, Optional, Union, Protocol

class CacheManager:
    def __init__(self, db_path: str, max_connections: int = 10) -> None:
        self.db_path = db_path
        self.max_connections = max_connections
    
    def get_records(
        self, 
        table_name: str, 
        filters: Dict[str, Union[str, int, List[str]]]
    ) -> List[Dict[str, Any]]:
        """获取缓存记录"""
        pass

# ❌ 错误：缺少类型注解
class CacheManager:
    def __init__(self, db_path, max_connections=10):
        self.db_path = db_path
        self.max_connections = max_connections
    
    def get_records(self, table_name, filters):
        pass
```

### 2.3 类设计规范

#### 2.3.1 单一职责原则
```python
# ✅ 正确：专注单一职责的类
class DatabaseConnectionManager:
    """数据库连接管理器 - 专注连接池管理"""
    
    def __init__(self, db_path: str, max_connections: int) -> None:
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: Dict[int, sqlite3.Connection] = {}
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        pass
    
    def close_connection(self, thread_id: int) -> None:
        """关闭指定连接"""
        pass

class CacheRecordValidator:
    """缓存记录验证器 - 专注数据验证"""
    
    def validate_cluster_info(self, data: Dict[str, Any]) -> bool:
        """验证集群信息"""
        pass
    
    def validate_pod_info(self, data: Dict[str, Any]) -> bool:
        """验证Pod信息"""
        pass

# ❌ 错误：职责混乱的类
class CacheEverything:
    """包含连接管理、数据验证、记录操作等多个职责"""
    pass
```

## 3. 开发流程规范

### 3.1 文档先行原则

#### 3.1.1 功能设计文档
```python
# 编写代码前必须先完成设计文档
"""
功能模块：MCP工具预加载器
文件路径：src/mcp/tool_loader.py
设计目标：扫描和缓存可用的K8s MCP工具

核心功能：
1. 连接MCP服务器获取工具列表
2. 解析工具schema和参数要求
3. 建立工具能力映射表
4. 缓存工具信息到数据库

API设计：
- load_tools() -> List[MCPToolInfo]
- get_tool_capabilities(tool_name: str) -> ToolCapabilities
- refresh_tool_cache() -> None

异常处理：
- MCPConnectionError: MCP服务器连接失败
- ToolLoadError: 工具加载失败
- SchemaParseError: Schema解析失败
"""
```

#### 3.1.2 API文档规范
```python
# ✅ 正确：详细的API文档
def scan_cluster_resources(
    cluster_name: str,
    resource_types: List[str],
    namespaces: Optional[List[str]] = None,
    timeout: int = 120
) -> Dict[str, List[Dict[str, Any]]]:
    """扫描集群资源信息
    
    扫描指定集群的K8s资源，支持多种资源类型和命名空间过滤。
    
    Args:
        cluster_name: 目标集群名称，必须是有效的K8s集群标识
        resource_types: 要扫描的资源类型列表，支持：
            - 'pods': Pod资源
            - 'services': Service资源  
            - 'nodes': Node资源
            - 'namespaces': Namespace资源
        namespaces: 命名空间过滤列表，None表示扫描所有命名空间
        timeout: 扫描超时时间（秒），默认120秒
    
    Returns:
        资源扫描结果字典，格式：
        {
            'pods': [{'name': 'pod1', 'namespace': 'default', ...}, ...],
            'services': [{'name': 'svc1', 'type': 'ClusterIP', ...}, ...],
            ...
        }
    
    Raises:
        ClusterAccessError: 集群访问失败
        ScanTimeoutError: 扫描超时
        ResourceNotFoundError: 指定资源类型不存在
        
    Example:
        >>> scanner = ClusterScanner()
        >>> result = scanner.scan_cluster_resources(
        ...     cluster_name='prod-cluster',
        ...     resource_types=['pods', 'services'],
        ...     namespaces=['default', 'kube-system']
        ... )
        >>> print(f"Found {len(result['pods'])} pods")
    
    Note:
        - 扫描大型集群时建议设置较长的timeout
        - 返回的资源信息已过滤敏感字段（如secrets）
        - 扫描结果会自动缓存，TTL根据资源类型确定
    """
    pass
```

### 3.2 测试驱动开发（TDD）

#### 3.2.1 测试先行原则
```python
# 1. 首先编写测试用例
class TestMCPToolLoader(unittest.TestCase):
    """MCP工具加载器测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        self.loader = MCPToolLoader(
            mcp_server_url="test://localhost",
            cache_manager=MockCacheManager()
        )
    
    def test_load_tools_success(self) -> None:
        """测试成功加载工具"""
        # Given: MCP服务器返回工具列表
        mock_tools = [
            {"name": "list_pods", "schema": {...}},
            {"name": "get_cluster_info", "schema": {...}}
        ]
        
        # When: 加载工具
        result = self.loader.load_tools()
        
        # Then: 验证结果
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], MCPToolInfo)
        self.assertEqual(result[0].name, "list_pods")
    
    def test_load_tools_connection_failure(self) -> None:
        """测试MCP连接失败"""
        # Given: MCP服务器不可用
        self.loader.mcp_server_url = "invalid://url"
        
        # When & Then: 应该抛出连接异常
        with self.assertRaises(MCPConnectionError) as context:
            self.loader.load_tools()
        
        self.assertIn("MCP服务器连接失败", str(context.exception))

# 2. 然后编写实现代码
class MCPToolLoader:
    def load_tools(self) -> List[MCPToolInfo]:
        """实现工具加载逻辑"""
        pass
```

### 3.3 代码审查规范

#### 3.3.1 审查检查清单
```markdown
## 代码审查检查清单

### 功能正确性
- [ ] 功能实现符合设计文档要求
- [ ] 所有测试用例通过
- [ ] 边界条件处理正确
- [ ] 异常处理遵循fail-fast原则

### 代码质量
- [ ] 函数不超过40行，参数不超过4个
- [ ] 类方法数量不超过10个
- [ ] 单个文件不超过150行
- [ ] 类型注解完整准确

### 文档规范
- [ ] 所有公共函数包含详细docstring
- [ ] API文档包含参数、返回值、异常说明
- [ ] 复杂逻辑包含注释说明
- [ ] 示例代码可执行

### 测试覆盖
- [ ] 核心功能测试覆盖率≥90%
- [ ] 包含正常和异常场景测试
- [ ] 性能关键路径包含基准测试
- [ ] 集成测试验证端到端功能
```

## 4. 代码质量标准

### 4.1 异常处理规范

#### 4.1.1 Fail-Fast异常处理
```python
# ✅ 正确：详细的异常上下文
from ..fail_fast_exceptions import (
    create_exception_context,
    CacheOperationError
)

def update_cache_record(
    table_name: str, 
    record_id: int, 
    updates: Dict[str, Any]
) -> bool:
    """更新缓存记录"""
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not updates:
            raise ValueError("更新数据不能为空")
        
        # 执行更新操作
        result = self._execute_update(table_name, record_id, updates)
        
        # 验证更新结果
        if not result:
            raise RuntimeError("更新操作未影响任何记录")
        
        return True
        
    except Exception as e:
        # 创建详细的异常上下文
        context = create_exception_context(
            operation=f"update_cache_record_{table_name}",
            table_name=table_name,
            record_id=record_id,
            updates_keys=list(updates.keys()),
            execution_time=time.time() - start_time,
            original_error=str(e)
        )
        
        # 立即抛出异常，不进行fallback
        raise CacheOperationError(
            f"更新{table_name}记录失败: {e}", 
            context
        ) from e

# ❌ 错误：忽略异常或使用默认值
def update_cache_record(table_name, record_id, updates):
    try:
        return self._execute_update(table_name, record_id, updates)
    except Exception:
        return False  # 错误：掩盖了真实错误
```

### 4.2 环境变量配置规范

#### 4.2.1 配置管理模式
```python
# ✅ 正确：遵循十二要素应用方法论
import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class CacheConfig:
    """缓存系统配置"""
    
    # 数据库配置
    db_path: str
    db_timeout: int
    max_connections: int
    
    # TTL配置
    static_ttl: int
    dynamic_ttl: int
    tool_mapping_ttl: int
    
    # 扫描配置
    scanner_interval: int
    scanner_timeout: int
    max_concurrent_scans: int
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """从环境变量创建配置"""
        # 验证必需的环境变量
        required_vars = [
            'CACHE_DB_PATH',
            'CACHE_STATIC_TTL',
            'CACHE_DYNAMIC_TTL'
        ]
        
        missing_vars = [
            var for var in required_vars 
            if not os.getenv(var)
        ]
        
        if missing_vars:
            raise ValueError(
                f"缺少必需的环境变量: {', '.join(missing_vars)}"
            )
        
        return cls(
            db_path=os.getenv('CACHE_DB_PATH'),
            db_timeout=int(os.getenv('CACHE_DB_TIMEOUT', '30')),
            max_connections=int(os.getenv('CACHE_DB_MAX_CONNECTIONS', '10')),
            static_ttl=int(os.getenv('CACHE_STATIC_TTL')),
            dynamic_ttl=int(os.getenv('CACHE_DYNAMIC_TTL')),
            tool_mapping_ttl=int(os.getenv('CACHE_TOOL_MAPPING_TTL', '3600')),
            scanner_interval=int(os.getenv('SCANNER_INTERVAL', '300')),
            scanner_timeout=int(os.getenv('SCANNER_TIMEOUT', '120')),
            max_concurrent_scans=int(os.getenv('SCANNER_MAX_CONCURRENT', '3'))
        )

# ❌ 错误：硬编码配置值
class CacheConfig:
    DB_PATH = "/tmp/cache.db"  # 错误：硬编码路径
    STATIC_TTL = 1800  # 错误：不可配置
```

## 5. 测试覆盖要求

### 5.1 单元测试规范

#### 5.1.1 测试覆盖率要求
```python
# ✅ 正确：完整的测试覆盖
class TestCacheManager(unittest.TestCase):
    """缓存管理器测试 - 覆盖率≥90%"""

    def setUp(self) -> None:
        """测试前准备"""
        self.config = CacheConfig.from_env()
        self.cache_manager = CacheManager(self.config)

    def test_create_record_success(self) -> None:
        """测试成功创建记录"""
        # 正常场景测试
        pass

    def test_create_record_invalid_data(self) -> None:
        """测试无效数据创建记录"""
        # 异常场景测试
        pass

    def test_create_record_database_error(self) -> None:
        """测试数据库错误场景"""
        # 错误场景测试
        pass

    def test_get_record_with_ttl_expired(self) -> None:
        """测试获取过期记录"""
        # TTL边界测试
        pass

    def test_batch_operations_performance(self) -> None:
        """测试批量操作性能"""
        # 性能基准测试
        start_time = time.time()

        # 批量创建1000条记录
        records = [self._create_test_record(i) for i in range(1000)]
        self.cache_manager.batch_create_records('test_table', records)

        execution_time = time.time() - start_time
        self.assertLess(execution_time, 5.0, "批量操作应在5秒内完成")

# ❌ 错误：测试覆盖不足
class TestCacheManager(unittest.TestCase):
    def test_basic_operation(self):
        # 只测试正常场景，缺少异常和边界测试
        pass
```

#### 5.1.2 集成测试规范
```python
class TestCacheSystemIntegration(unittest.TestCase):
    """缓存系统集成测试"""

    def test_end_to_end_workflow(self) -> None:
        """测试端到端工作流程"""
        # 1. 初始化系统
        cache_system = CacheSystem.from_config()

        # 2. 加载MCP工具
        tool_loader = MCPToolLoader(cache_system.cache_manager)
        tools = tool_loader.load_tools()
        self.assertGreater(len(tools), 0)

        # 3. 扫描集群资源
        scanner = ClusterScanner(cache_system.cache_manager)
        resources = scanner.scan_cluster('test-cluster')
        self.assertIn('pods', resources)

        # 4. 验证缓存数据
        cached_pods = cache_system.cache_manager.list_records('pods')
        self.assertEqual(len(cached_pods), len(resources['pods']))

        # 5. 测试智能上下文增强
        enhancer = ContextEnhancer(cache_system.cache_manager)
        suggestions = enhancer.suggest_parameters(
            user_intent="list pods in default namespace",
            tool_name="list_pods"
        )
        self.assertIn('namespace', suggestions)
        self.assertEqual(suggestions['namespace'], 'default')

    def test_system_resilience(self) -> None:
        """测试系统弹性"""
        # 测试MCP服务器断开连接的恢复能力
        # 测试数据库连接失败的处理
        # 测试内存不足的降级处理
        pass
```

### 5.2 性能测试规范

#### 5.2.1 基准测试
```python
import time
import psutil
from typing import Dict, Any

class PerformanceBenchmark:
    """性能基准测试"""

    def benchmark_cache_operations(self) -> Dict[str, Any]:
        """缓存操作性能基准"""
        results = {}

        # 测试单记录操作性能
        start_time = time.time()
        for i in range(1000):
            self.cache_manager.create_record('test_table', self._create_test_data(i))
        results['create_1000_records'] = time.time() - start_time

        # 测试批量操作性能
        start_time = time.time()
        batch_data = [self._create_test_data(i) for i in range(1000)]
        self.cache_manager.batch_create_records('test_table', batch_data)
        results['batch_create_1000_records'] = time.time() - start_time

        # 测试查询性能
        start_time = time.time()
        for i in range(100):
            self.cache_manager.list_records('test_table', limit=100)
        results['query_100_times'] = time.time() - start_time

        # 内存使用情况
        process = psutil.Process()
        results['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024

        return results

    def assert_performance_requirements(self, results: Dict[str, Any]) -> None:
        """验证性能要求"""
        # 单记录创建：平均<1ms
        avg_create_time = results['create_1000_records'] / 1000
        self.assertLess(avg_create_time, 0.001, "单记录创建应<1ms")

        # 批量操作：比单记录快50%以上
        batch_ratio = results['batch_create_1000_records'] / results['create_1000_records']
        self.assertLess(batch_ratio, 0.5, "批量操作应比单记录快50%以上")

        # 内存使用：<100MB
        self.assertLess(results['memory_usage_mb'], 100, "内存使用应<100MB")
```

## 6. 项目特定要求

### 6.1 缓存系统规范

#### 6.1.1 数据模型设计
```python
# ✅ 正确：完整的数据模型
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

@dataclass
class CacheableModel:
    """可缓存数据模型基类"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ttl_expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，支持序列化"""
        data = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime):
                data[field_name] = field_value.isoformat()
            elif isinstance(field_value, (dict, list)):
                data[field_name] = json.dumps(field_value, ensure_ascii=False)
            else:
                data[field_name] = field_value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheableModel':
        """从字典创建实例，支持反序列化"""
        # 处理datetime字段
        datetime_fields = ['created_at', 'updated_at', 'ttl_expires_at']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])

        # 处理JSON字段（子类需要重写此方法指定具体字段）
        json_fields = cls._get_json_fields()
        for field in json_fields:
            if field in data and isinstance(data[field], str):
                data[field] = json.loads(data[field]) if data[field] else None

        return cls(**data)

    @classmethod
    def _get_json_fields(cls) -> List[str]:
        """获取需要JSON序列化的字段列表（子类重写）"""
        return []

@dataclass
class PodInfo(CacheableModel):
    """Pod信息模型"""
    cluster_name: str
    namespace: str
    name: str
    status: str
    phase: str
    node_name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    containers: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def _get_json_fields(cls) -> List[str]:
        return ['labels', 'containers']

# ❌ 错误：缺少序列化支持的模型
class PodInfo:
    def __init__(self, name, namespace):
        self.name = name
        self.namespace = namespace
        # 缺少序列化方法，无法缓存
```

### 6.2 MCP工具集成规范

#### 6.2.1 工具调用规范
```python
# ✅ 正确：完整的MCP工具调用
import asyncio
from typing import Dict, Any, Optional
from ..fail_fast_exceptions import (
    MCPConnectionError,
    ToolCallError,
    create_exception_context
)

class MCPToolCaller:
    """MCP工具调用器"""

    def __init__(
        self,
        mcp_client: MCPClient,
        max_retries: int = 3,
        timeout: int = 30
    ) -> None:
        self.mcp_client = mcp_client
        self.max_retries = max_retries
        self.timeout = timeout

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """调用MCP工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            retry_count: 当前重试次数

        Returns:
            工具执行结果

        Raises:
            ToolCallError: 工具调用失败
            MCPConnectionError: MCP连接失败
        """
        start_time = time.time()

        try:
            # 验证工具参数
            self._validate_tool_parameters(tool_name, parameters)

            # 执行工具调用（带超时）
            result = await asyncio.wait_for(
                self.mcp_client.call_tool(tool_name, parameters),
                timeout=self.timeout
            )

            # 验证返回结果
            self._validate_tool_result(tool_name, result)

            return result

        except asyncio.TimeoutError as e:
            # 超时重试
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # 指数退避
                return await self.call_tool(tool_name, parameters, retry_count + 1)

            context = create_exception_context(
                operation=f"mcp_tool_call_{tool_name}",
                tool_name=tool_name,
                parameters=parameters,
                retry_count=retry_count,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ToolCallError(f"工具{tool_name}调用超时", context) from e

        except Exception as e:
            # 连接错误重试
            if "connection" in str(e).lower() and retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.call_tool(tool_name, parameters, retry_count + 1)

            context = create_exception_context(
                operation=f"mcp_tool_call_{tool_name}",
                tool_name=tool_name,
                parameters=parameters,
                retry_count=retry_count,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )

            if "connection" in str(e).lower():
                raise MCPConnectionError(f"MCP连接失败: {e}", context) from e
            else:
                raise ToolCallError(f"工具{tool_name}调用失败: {e}", context) from e

# ❌ 错误：缺少错误处理和重试机制
async def call_tool(tool_name, parameters):
    return await mcp_client.call_tool(tool_name, parameters)
```

### 6.3 Gemini 2.5 Flash集成规范

#### 6.3.1 LLM调用规范
```python
# ✅ 正确：完整的LLM调用处理
from typing import Dict, List, Any, Optional
import tiktoken

class GeminiContextManager:
    """Gemini 2.5 Flash上下文管理器"""

    def __init__(
        self,
        max_input_tokens: int = 1048576,  # 1M+ tokens
        max_output_tokens: int = 32768,   # 32K tokens
        compression_ratio: float = 0.7    # 压缩比例
    ) -> None:
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.compression_ratio = compression_ratio
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def prepare_context(
        self,
        user_query: str,
        cached_resources: Dict[str, List[Dict[str, Any]]],
        tool_suggestions: Dict[str, Any]
    ) -> str:
        """准备LLM上下文

        Args:
            user_query: 用户查询
            cached_resources: 缓存的资源信息
            tool_suggestions: 工具建议

        Returns:
            优化后的上下文字符串
        """
        # 1. 构建基础上下文
        context_parts = [
            f"用户查询: {user_query}",
            "",
            "=== 集群资源信息 ===",
            self._format_cached_resources(cached_resources),
            "",
            "=== 工具建议 ===",
            self._format_tool_suggestions(tool_suggestions)
        ]

        full_context = "\n".join(context_parts)

        # 2. 检查token限制
        token_count = len(self.tokenizer.encode(full_context))

        if token_count > self.max_input_tokens:
            # 3. 应用上下文压缩
            compressed_context = self._compress_context(
                context_parts,
                target_tokens=int(self.max_input_tokens * self.compression_ratio)
            )
            return compressed_context

        return full_context

    def _compress_context(
        self,
        context_parts: List[str],
        target_tokens: int
    ) -> str:
        """压缩上下文以适应token限制"""
        # 优先级：用户查询 > 工具建议 > 资源信息
        essential_parts = [context_parts[0], context_parts[4], context_parts[5]]
        essential_context = "\n".join(essential_parts)
        essential_tokens = len(self.tokenizer.encode(essential_context))

        if essential_tokens > target_tokens:
            raise ValueError(f"基础上下文({essential_tokens} tokens)超过目标限制({target_tokens} tokens)")

        # 压缩资源信息
        remaining_tokens = target_tokens - essential_tokens
        compressed_resources = self._compress_resources(
            context_parts[2],
            remaining_tokens
        )

        return "\n".join([
            context_parts[0],  # 用户查询
            "",
            compressed_resources,  # 压缩的资源信息
            "",
            context_parts[4],  # 工具建议标题
            context_parts[5]   # 工具建议内容
        ])

# ❌ 错误：未考虑token限制的LLM调用
def call_gemini(user_query, all_data):
    # 直接传递所有数据，可能超过token限制
    context = f"Query: {user_query}\nData: {str(all_data)}"
    return llm.invoke(context)
```

## 7. 代码示例和反模式

### 7.1 正确的模块设计示例

```python
# ✅ 正确：清晰的模块边界和职责分离
# src/cache/ttl_manager.py
from datetime import datetime, timedelta
from typing import Dict, Optional

class TTLManager:
    """TTL管理器 - 专注TTL计算和过期处理"""

    def __init__(self, static_ttl: int, dynamic_ttl: int) -> None:
        self.static_ttl = static_ttl
        self.dynamic_ttl = dynamic_ttl

    def calculate_expiry(self, resource_type: str) -> datetime:
        """计算资源过期时间"""
        now = datetime.utcnow()
        if resource_type in ['clusters', 'namespaces', 'nodes']:
            return now + timedelta(seconds=self.static_ttl)
        else:
            return now + timedelta(seconds=self.dynamic_ttl)

    def is_expired(self, expiry_time: datetime) -> bool:
        """检查是否过期"""
        return datetime.utcnow() > expiry_time

# src/cache/record_serializer.py
import json
from typing import Any, Dict, List

class RecordSerializer:
    """记录序列化器 - 专注数据序列化/反序列化"""

    @staticmethod
    def serialize_json_fields(
        data: Dict[str, Any],
        json_fields: List[str]
    ) -> Dict[str, Any]:
        """序列化JSON字段"""
        result = data.copy()
        for field in json_fields:
            if field in result and result[field] is not None:
                result[field] = json.dumps(result[field], ensure_ascii=False)
        return result

    @staticmethod
    def deserialize_json_fields(
        data: Dict[str, Any],
        json_fields: List[str]
    ) -> Dict[str, Any]:
        """反序列化JSON字段"""
        result = data.copy()
        for field in json_fields:
            if field in result and isinstance(result[field], str):
                result[field] = json.loads(result[field]) if result[field] else None
        return result
```

### 7.2 常见反模式和解决方案

```python
# ❌ 反模式1：上帝类（God Class）
class CacheEverything:
    """包含所有功能的巨大类"""
    def __init__(self):
        pass

    def connect_database(self): pass
    def create_record(self): pass
    def serialize_data(self): pass
    def calculate_ttl(self): pass
    def compress_context(self): pass
    def call_llm(self): pass
    # ... 50个方法

# ✅ 解决方案：职责分离
class CacheManager:
    """缓存管理器 - 协调各个组件"""
    def __init__(self, db_manager, ttl_manager, serializer):
        self.db_manager = db_manager
        self.ttl_manager = ttl_manager
        self.serializer = serializer

# ❌ 反模式2：魔法数字和硬编码
def scan_cluster():
    timeout = 120  # 魔法数字
    max_retries = 3  # 魔法数字
    batch_size = 100  # 魔法数字

# ✅ 解决方案：配置化
@dataclass
class ScannerConfig:
    timeout: int = 120
    max_retries: int = 3
    batch_size: int = 100

def scan_cluster(config: ScannerConfig):
    pass

# ❌ 反模式3：异常吞噬
def risky_operation():
    try:
        dangerous_call()
    except Exception:
        pass  # 错误：忽略异常

# ✅ 解决方案：Fail-Fast
def risky_operation():
    try:
        dangerous_call()
    except Exception as e:
        context = create_exception_context(
            operation="risky_operation",
            original_error=str(e)
        )
        raise OperationError(f"操作失败: {e}", context) from e
```

## 8. 工具和自动化

### 8.1 代码格式化配置

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 8.2 预提交钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: uv run python -m pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 9. 实施计划

### 9.1 现有代码审查

1. **立即审查**：检查当前缓存系统代码是否符合规范
2. **重构计划**：识别需要重构的代码模块
3. **测试补充**：为缺少测试的模块添加测试用例
4. **文档更新**：为所有模块添加完整的API文档

### 9.2 新代码开发

1. **设计先行**：每个新功能先完成设计文档
2. **TDD开发**：测试驱动的开发流程
3. **代码审查**：所有代码变更必须通过审查
4. **持续集成**：自动化测试和代码质量检查

### 9.3 质量监控

1. **测试覆盖率**：维持≥90%的测试覆盖率
2. **性能监控**：定期执行性能基准测试
3. **代码质量**：使用静态分析工具监控代码质量
4. **文档同步**：确保代码和文档保持同步

---

## 附录：快速参考

### A.1 检查清单

- [ ] 函数不超过40行，参数不超过4个
- [ ] 类方法数量不超过10个
- [ ] 文件不超过150行
- [ ] 完整的类型注解
- [ ] 详细的docstring
- [ ] Fail-fast异常处理
- [ ] 环境变量配置
- [ ] 测试覆盖率≥90%

### A.2 常用模式

```python
# 配置类模式
@dataclass
class Config:
    @classmethod
    def from_env(cls) -> 'Config':
        pass

# 异常处理模式
try:
    operation()
except Exception as e:
    context = create_exception_context(...)
    raise CustomError(f"操作失败: {e}", context) from e

# 数据模型模式
@dataclass
class Model(CacheableModel):
    @classmethod
    def _get_json_fields(cls) -> List[str]:
        return ['field1', 'field2']
```
```
```
