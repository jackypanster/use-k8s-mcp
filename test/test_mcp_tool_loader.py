"""
MCP工具预加载机制测试
验证工具发现、解析、分析和缓存的完整流程
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.update({
    'CACHE_DB_PATH': './test_data/test_mcp_cache.db',
    'CACHE_DB_TIMEOUT': '10',
    'CACHE_STATIC_TTL': '1800',
    'CACHE_DYNAMIC_TTL': '300',
    'MCP_TOOL_LOAD_TIMEOUT': '30'
})

from src.mcp import (
    MCPToolLoader, SchemaParser, CapabilityAnalyzer, ToolSelector,
    ToolSchema, ToolCapabilities, MCPConnectionError, ToolLoadError
)
from src.cache import CacheManager


class TestSchemaParser(unittest.TestCase):
    """Schema解析器测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        self.parser = SchemaParser()
    
    def test_parse_valid_tool_schema(self) -> None:
        """测试解析有效的工具schema"""
        tool_data = {
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
        }
        
        schema = self.parser.parse_tool_schema(tool_data)
        
        self.assertEqual(schema.name, 'k8s_list_pods')
        self.assertEqual(schema.description, 'List pods in a namespace')
        self.assertEqual(schema.required_params, ['namespace'])
        self.assertEqual(schema.optional_params, ['label_selector'])
        
        print("✅ Schema解析测试通过")
    
    def test_parse_tool_without_schema(self) -> None:
        """测试解析没有schema的工具"""
        tool_data = {
            'name': 'simple_tool',
            'description': 'A simple tool'
        }
        
        schema = self.parser.parse_tool_schema(tool_data)
        
        self.assertEqual(schema.name, 'simple_tool')
        self.assertEqual(schema.required_params, [])
        self.assertEqual(schema.optional_params, [])
        
        print("✅ 无schema工具解析测试通过")
    
    def test_extract_parameters(self) -> None:
        """测试参数提取"""
        schema = {
            'type': 'object',
            'properties': {
                'required_param': {'type': 'string'},
                'optional_param': {'type': 'string'}
            },
            'required': ['required_param']
        }
        
        required, optional = self.parser.extract_parameters(schema)
        
        self.assertEqual(required, ['required_param'])
        self.assertEqual(optional, ['optional_param'])
        
        print("✅ 参数提取测试通过")


class TestCapabilityAnalyzer(unittest.TestCase):
    """能力分析器测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        self.analyzer = CapabilityAnalyzer()
    
    def test_analyze_pod_tool_capabilities(self) -> None:
        """测试分析Pod工具能力"""
        tool_schema = ToolSchema(
            name='k8s_list_pods',
            description='List pods in a namespace',
            input_schema={
                'type': 'object',
                'properties': {
                    'namespace': {'type': 'string'}
                },
                'required': ['namespace']
            }
        )
        
        capabilities = self.analyzer.analyze_tool_capabilities(tool_schema)
        
        self.assertEqual(capabilities.tool_name, 'k8s_list_pods')
        self.assertIn('pod', capabilities.resource_types)
        self.assertIn('list', capabilities.operation_types)
        self.assertTrue(capabilities.cache_friendly)
        
        print("✅ Pod工具能力分析测试通过")
    
    def test_infer_resource_types(self) -> None:
        """测试资源类型推断"""
        resource_types = self.analyzer.infer_resource_types(
            'k8s_describe_service',
            'Describe a Kubernetes service'
        )
        
        self.assertIn('service', resource_types)
        
        print("✅ 资源类型推断测试通过")
    
    def test_infer_operation_types(self) -> None:
        """测试操作类型推断"""
        operation_types = self.analyzer.infer_operation_types(
            'k8s_create_deployment',
            {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'image': {'type': 'string'}
                }
            }
        )
        
        self.assertIn('create', operation_types)
        
        print("✅ 操作类型推断测试通过")


class TestToolSelector(unittest.TestCase):
    """工具选择器测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        # 创建测试数据目录
        test_data_dir = Path('./test_data')
        test_data_dir.mkdir(exist_ok=True)
        
        # 删除已存在的测试数据库
        test_db_path = Path('./test_data/test_mcp_cache.db')
        if test_db_path.exists():
            test_db_path.unlink()
        
        self.cache_manager = CacheManager()
        self.selector = ToolSelector(self.cache_manager)
        
        # 准备测试数据
        self._prepare_test_tools()
    
    def _prepare_test_tools(self) -> None:
        """准备测试工具数据"""
        from src.cache import MCPToolInfo
        
        test_tools = [
            MCPToolInfo(
                name='k8s_list_pods',
                description='List pods in a namespace',
                resource_types=['pod'],
                operation_types=['list'],
                required_params=['namespace']
            ),
            MCPToolInfo(
                name='k8s_describe_service',
                description='Describe a service',
                resource_types=['service'],
                operation_types=['describe'],
                required_params=['namespace', 'name']
            )
        ]
        
        self.cache_manager.batch_create_records('mcp_tools', test_tools)
    
    def test_get_compatible_tools(self) -> None:
        """测试获取兼容工具"""
        compatible_tools = self.selector.get_compatible_tools(
            resource_type='pod',
            operation_type='list'
        )
        
        self.assertIn('k8s_list_pods', compatible_tools)
        self.assertNotIn('k8s_describe_service', compatible_tools)
        
        print("✅ 兼容工具获取测试通过")
    
    def test_select_best_tool(self) -> None:
        """测试选择最佳工具"""
        best_tool = self.selector.select_best_tool(
            intent="list all pods in default namespace",
            resource_type="pod",
            operation_type="list"
        )

        self.assertEqual(best_tool, 'k8s_list_pods')

        print("✅ 最佳工具选择测试通过")


class TestMCPToolLoader(unittest.TestCase):
    """MCP工具加载器测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        # 创建测试数据目录
        test_data_dir = Path('./test_data')
        test_data_dir.mkdir(exist_ok=True)
        
        # 删除已存在的测试数据库
        test_db_path = Path('./test_data/test_mcp_cache.db')
        if test_db_path.exists():
            test_db_path.unlink()
        
        self.cache_manager = CacheManager()
        self.loader = MCPToolLoader(self.cache_manager, timeout=10)
    
    def test_load_tools_success(self) -> None:
        """测试成功加载工具"""
        # 运行异步加载
        tools = asyncio.run(self.loader.load_tools())
        
        self.assertGreater(len(tools), 0)
        self.assertEqual(tools[0].name, 'k8s_list_pods')
        
        # 验证工具已缓存
        cached_tools = self.cache_manager.list_records('mcp_tools')
        self.assertEqual(len(cached_tools), len(tools))
        
        print("✅ 工具加载测试通过")
    
    def test_get_tool_capabilities(self) -> None:
        """测试获取工具能力"""
        # 先加载工具
        asyncio.run(self.loader.load_tools())
        
        # 获取工具能力
        capabilities = asyncio.run(
            self.loader.get_tool_capabilities('k8s_list_pods')
        )
        
        self.assertIsNotNone(capabilities)
        self.assertEqual(capabilities.tool_name, 'k8s_list_pods')
        self.assertIn('pod', capabilities.resource_types)
        
        print("✅ 工具能力获取测试通过")
    
    def test_get_loading_stats(self) -> None:
        """测试获取加载统计"""
        # 加载工具
        asyncio.run(self.loader.load_tools())
        
        stats = self.loader.get_loading_stats()
        
        self.assertIn('loaded_count', stats)
        self.assertIn('error_count', stats)
        self.assertIn('schema_parser_stats', stats)
        self.assertIn('capability_analyzer_stats', stats)
        
        self.assertGreater(stats['loaded_count'], 0)
        
        print("✅ 加载统计测试通过")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self) -> None:
        """测试前准备"""
        # 创建测试数据目录
        test_data_dir = Path('./test_data')
        test_data_dir.mkdir(exist_ok=True)
        
        # 删除已存在的测试数据库
        test_db_path = Path('./test_data/test_mcp_cache.db')
        if test_db_path.exists():
            test_db_path.unlink()
        
        self.cache_manager = CacheManager()
    
    def test_end_to_end_workflow(self) -> None:
        """测试端到端工作流程"""
        # 1. 初始化工具加载器
        loader = MCPToolLoader(self.cache_manager)
        
        # 2. 加载工具
        tools = asyncio.run(loader.load_tools())
        self.assertGreater(len(tools), 0)
        
        # 3. 初始化工具选择器
        selector = ToolSelector(self.cache_manager)
        
        # 4. 选择工具
        best_tool = selector.select_best_tool(
            intent="show me all pods",
            resource_type="pod"
        )
        self.assertIsNotNone(best_tool)
        
        # 5. 获取工具能力
        capabilities = asyncio.run(loader.get_tool_capabilities(best_tool))
        self.assertIsNotNone(capabilities)
        
        print("✅ 端到端工作流程测试通过")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
