"""
MCP工具加载器
协调工具发现、解析、分析和缓存的完整流程
遵循单一职责原则，作为各组件的协调器
"""

import os
import time
import asyncio
from typing import List, Optional, Dict, Any

from .schema_parser import SchemaParser
from .capability_analyzer import CapabilityAnalyzer
from .models import ToolSchema, ToolCapabilities
from .exceptions import MCPConnectionError, ToolLoadError
from src.cache import CacheManager, MCPToolInfo
from src.fail_fast_exceptions import create_exception_context


class MCPToolLoader:
    """MCP工具加载器 - 协调工具发现、解析和缓存"""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        timeout: int = 30,
        max_parallel_load: int = 5
    ) -> None:
        """初始化工具加载器
        
        Args:
            cache_manager: 缓存管理器实例
            timeout: 操作超时时间（秒）
            max_parallel_load: 最大并行加载数量
        """
        self.cache_manager = cache_manager
        self.timeout = timeout
        self.max_parallel_load = max_parallel_load
        
        # 初始化组件
        self.schema_parser = SchemaParser()
        self.capability_analyzer = CapabilityAnalyzer()
        
        # 统计信息
        self.loaded_count = 0
        self.error_count = 0
    
    async def load_tools(self) -> List[MCPToolInfo]:
        """加载所有MCP工具
        
        Returns:
            加载的工具信息列表
            
        Raises:
            MCPConnectionError: MCP连接失败
            ToolLoadError: 工具加载失败
        """
        start_time = time.time()
        
        try:
            # 1. 发现可用工具
            raw_tools = await self._discover_tools()
            
            if not raw_tools:
                return []
            
            # 2. 并行处理工具
            tool_infos = await self._process_tools_parallel(raw_tools)
            
            # 3. 批量缓存工具信息
            await self._cache_tools(tool_infos)
            
            self.loaded_count = len(tool_infos)
            return tool_infos
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="load_tools",
                execution_time=time.time() - start_time,
                timeout=self.timeout,
                original_error=str(e)
            )
            
            if "connection" in str(e).lower():
                raise MCPConnectionError(f"MCP工具加载失败: {e}", context) from e
            else:
                raise ToolLoadError(f"工具加载失败: {e}", context) from e
    
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
        try:
            # 从缓存获取工具信息
            tool_info = self.cache_manager.get_record('mcp_tools', name=tool_name)
            
            if not tool_info:
                return None
            
            # 构建ToolCapabilities对象
            capabilities = ToolCapabilities(
                tool_name=tool_info.name,
                resource_types=tool_info.resource_types or [],
                operation_types=tool_info.operation_types or [],
                scope='resource',  # 默认值，可以从工具信息中获取
                cache_friendly=True,  # 默认值
                complexity_score=5  # 默认值
            )
            
            return capabilities
            
        except Exception as e:
            context = create_exception_context(
                operation="get_tool_capabilities",
                tool_name=tool_name,
                original_error=str(e)
            )
            raise ToolLoadError(f"获取工具能力失败: {e}", context) from e
    
    def refresh_tool_cache(self) -> None:
        """刷新工具缓存"""
        try:
            # 清理现有工具缓存
            self.cache_manager.delete_record('mcp_tools')
            
            # 重新加载工具（同步调用异步方法）
            asyncio.run(self.load_tools())
            
        except Exception as e:
            context = create_exception_context(
                operation="refresh_tool_cache",
                original_error=str(e)
            )
            raise ToolLoadError(f"刷新工具缓存失败: {e}", context) from e
    
    async def _discover_tools(self) -> List[Dict[str, Any]]:
        """发现可用的MCP工具"""
        # 模拟工具发现过程
        # 在实际实现中，这里会连接真实的MCP服务器
        mock_tools = [
            {
                'name': 'k8s_list_pods',
                'description': 'List pods in a namespace',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'namespace': {'type': 'string'},
                        'label_selector': {'type': 'string'}
                    },
                    'required': ['namespace']
                }
            },
            {
                'name': 'k8s_get_cluster_info',
                'description': 'Get cluster information',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'k8s_describe_service',
                'description': 'Describe a service in detail',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'namespace': {'type': 'string'},
                        'name': {'type': 'string'}
                    },
                    'required': ['namespace', 'name']
                }
            }
        ]
        
        return mock_tools
    
    async def _process_tools_parallel(
        self,
        raw_tools: List[Dict[str, Any]]
    ) -> List[MCPToolInfo]:
        """并行处理工具列表"""
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_parallel_load)
        
        # 创建处理任务
        tasks = [
            self._process_single_tool(semaphore, tool_data)
            for tool_data in raw_tools
        ]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        tool_infos = []
        for result in results:
            if isinstance(result, MCPToolInfo):
                tool_infos.append(result)
            elif isinstance(result, Exception):
                # 记录错误但继续处理其他工具
                print(f"工具处理失败: {result}")
        
        return tool_infos
    
    async def _process_single_tool(
        self,
        semaphore: asyncio.Semaphore,
        tool_data: Dict[str, Any]
    ) -> MCPToolInfo:
        """处理单个工具"""
        async with semaphore:
            try:
                # 解析schema
                tool_schema = self.schema_parser.parse_tool_schema(tool_data)
                
                # 分析能力
                capabilities = self.capability_analyzer.analyze_tool_capabilities(tool_schema)
                
                # 创建MCPToolInfo对象
                tool_info = MCPToolInfo(
                    name=tool_schema.name,
                    description=tool_schema.description,
                    input_schema=tool_schema.input_schema,
                    output_schema=tool_schema.output_schema,
                    resource_types=capabilities.resource_types,
                    operation_types=capabilities.operation_types,
                    required_params=tool_schema.required_params,
                    optional_params=tool_schema.optional_params
                )
                
                return tool_info
                
            except Exception as e:
                raise ToolLoadError(f"处理工具{tool_data.get('name', 'unknown')}失败: {e}") from e
    
    async def _cache_tools(self, tool_infos: List[MCPToolInfo]) -> None:
        """批量缓存工具信息"""
        try:
            # 使用批量创建提高性能
            self.cache_manager.batch_create_records('mcp_tools', tool_infos)
            
        except Exception as e:
            context = create_exception_context(
                operation="cache_tools",
                tool_count=len(tool_infos),
                original_error=str(e)
            )
            raise ToolLoadError(f"缓存工具信息失败: {e}", context) from e
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        return {
            'loaded_count': self.loaded_count,
            'error_count': self.error_count,
            'schema_parser_stats': self.schema_parser.get_parsing_stats(),
            'capability_analyzer_stats': self.capability_analyzer.get_analysis_stats()
        }
