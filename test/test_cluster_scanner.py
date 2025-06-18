"""
集群扫描器测试
验证集群扫描功能的正确性和可靠性
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.update({
    'CACHE_DB_PATH': './test_data/test_scanner_cache.db',
    'CACHE_DB_TIMEOUT': '10',
    'CACHE_STATIC_TTL': '1800',
    'CACHE_DYNAMIC_TTL': '300'
})

from src.scanner import ClusterScanner, ResourceParser, ScanCoordinator
from src.scanner.exceptions import ScanError, ToolNotFoundError, ScanTimeoutError
from src.cache import CacheManager
from src.mcp_tools import MCPToolLoader


class TestClusterScanner(unittest.TestCase):
    """集群扫描器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的MCP客户端
        self.mock_mcp_client = Mock()
        self.mock_mcp_client.run = AsyncMock()
        
        # 创建模拟的工具加载器
        self.mock_tool_loader = Mock()
        self.mock_tool_loader.get_tool_capabilities = AsyncMock()
        
        # 创建集群扫描器
        self.scanner = ClusterScanner(
            mcp_client=self.mock_mcp_client,
            tool_loader=self.mock_tool_loader,
            timeout=30,
            max_retries=2
        )
    
    async def test_scan_static_resources_success(self):
        """测试静态资源扫描成功"""
        # 模拟工具能力检查
        self.mock_tool_loader.get_tool_capabilities.return_value = Mock()
        
        # 模拟MCP工具调用结果
        mock_cluster_info = {
            'name': 'test-cluster',
            'version': 'v1.23.15',
            'server': 'https://test-cluster:6443',
            'nodeCount': 3
        }
        
        mock_namespaces = {
            'items': [
                {
                    'metadata': {'name': 'default'},
                    'status': {'phase': 'Active'}
                },
                {
                    'metadata': {'name': 'kube-system'},
                    'status': {'phase': 'Active'}
                }
            ]
        }
        
        mock_nodes = {
            'items': [
                {
                    'metadata': {'name': 'node-1'},
                    'status': {
                        'conditions': [{'type': 'Ready', 'status': 'True'}]
                    }
                }
            ]
        }
        
        # 配置MCP客户端返回值
        self.mock_mcp_client.run.side_effect = [
            mock_cluster_info,
            mock_namespaces,
            mock_nodes
        ]
        
        # 执行扫描
        result = await self.scanner.scan_static_resources('test-cluster')
        
        # 验证结果
        self.assertIn('cluster', result)
        self.assertIn('namespaces', result)
        self.assertIn('nodes', result)
        self.assertEqual(result['cluster'], mock_cluster_info)
        self.assertEqual(len(result['namespaces']), 2)
        self.assertEqual(len(result['nodes']), 1)
        
        # 验证统计信息
        stats = self.scanner.get_scan_stats()
        self.assertEqual(stats['scan_count'], 1)
        self.assertEqual(stats['error_count'], 0)
    
    async def test_scan_dynamic_resources_success(self):
        """测试动态资源扫描成功"""
        # 模拟工具能力检查
        self.mock_tool_loader.get_tool_capabilities.return_value = Mock()
        
        # 模拟MCP工具调用结果
        mock_pods = {
            'items': [
                {
                    'metadata': {'name': 'test-pod', 'namespace': 'default'},
                    'status': {'phase': 'Running'},
                    'spec': {'nodeName': 'node-1'}
                }
            ]
        }
        
        mock_services = {
            'items': [
                {
                    'metadata': {'name': 'test-service', 'namespace': 'default'},
                    'spec': {'type': 'ClusterIP', 'clusterIP': '10.0.0.1'}
                }
            ]
        }
        
        mock_deployments = {'items': []}
        
        # 配置MCP客户端返回值
        self.mock_mcp_client.run.side_effect = [
            mock_pods,
            mock_services,
            mock_deployments
        ]
        
        # 执行扫描
        result = await self.scanner.scan_dynamic_resources('test-cluster')
        
        # 验证结果
        self.assertIn('pods', result)
        self.assertIn('services', result)
        self.assertIn('deployments', result)
        self.assertEqual(len(result['pods']), 1)
        self.assertEqual(len(result['services']), 1)
        self.assertEqual(len(result['deployments']), 0)
    
    async def test_tool_not_found_error(self):
        """测试工具不存在错误"""
        # 模拟工具不存在
        self.mock_tool_loader.get_tool_capabilities.return_value = None
        
        # 执行扫描并验证异常
        with self.assertRaises(ToolNotFoundError):
            await self.scanner.scan_static_resources('test-cluster')
    
    async def test_scan_timeout_error(self):
        """测试扫描超时错误"""
        # 模拟工具能力检查
        self.mock_tool_loader.get_tool_capabilities.return_value = Mock()
        
        # 模拟超时
        self.mock_mcp_client.run.side_effect = asyncio.TimeoutError()
        
        # 执行扫描并验证异常
        with self.assertRaises(ScanTimeoutError):
            await self.scanner.scan_static_resources('test-cluster')


class TestResourceParser(unittest.TestCase):
    """资源解析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = ResourceParser()
    
    def test_parse_cluster_info(self):
        """测试集群信息解析"""
        raw_data = {
            'name': 'test-cluster',
            'version': 'v1.23.15',
            'server': 'https://test-cluster:6443',
            'nodeCount': 3
        }
        
        cluster_info = self.parser.parse_cluster_info(raw_data, 'test-cluster')
        
        self.assertEqual(cluster_info.name, 'test-cluster')
        self.assertEqual(cluster_info.version, 'v1.23.15')
        self.assertEqual(cluster_info.api_server, 'https://test-cluster:6443')
        self.assertEqual(cluster_info.node_count, 3)
    
    def test_parse_namespaces(self):
        """测试命名空间解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'default',
                    'labels': {'name': 'default'}
                },
                'status': {'phase': 'Active'}
            },
            {
                'metadata': {
                    'name': 'kube-system',
                    'labels': {'name': 'kube-system'}
                },
                'status': {'phase': 'Active'}
            }
        ]
        
        namespaces = self.parser.parse_namespaces(raw_data, 'test-cluster')
        
        self.assertEqual(len(namespaces), 2)
        self.assertEqual(namespaces[0].name, 'default')
        self.assertEqual(namespaces[0].cluster_name, 'test-cluster')
        self.assertEqual(namespaces[0].status, 'Active')
        self.assertEqual(namespaces[1].name, 'kube-system')
    
    def test_parse_pods(self):
        """测试Pod解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'test-pod',
                    'namespace': 'default',
                    'labels': {'app': 'test'}
                },
                'status': {
                    'phase': 'Running',
                    'containerStatuses': [
                        {'name': 'test-container', 'ready': True, 'restartCount': 0}
                    ]
                },
                'spec': {
                    'nodeName': 'node-1',
                    'containers': [
                        {'name': 'test-container', 'image': 'nginx:latest'}
                    ]
                }
            }
        ]
        
        pods = self.parser.parse_pods(raw_data, 'test-cluster')
        
        self.assertEqual(len(pods), 1)
        pod = pods[0]
        self.assertEqual(pod.name, 'test-pod')
        self.assertEqual(pod.namespace, 'default')
        self.assertEqual(pod.cluster_name, 'test-cluster')
        self.assertEqual(pod.phase, 'Running')
        self.assertEqual(pod.node_name, 'node-1')
        self.assertEqual(len(pod.containers), 1)
        self.assertEqual(pod.containers[0]['name'], 'test-container')


class TestScanCoordinator(unittest.TestCase):
    """扫描协调器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟组件
        self.mock_scanner = Mock()
        self.mock_parser = Mock()
        self.mock_cache_manager = Mock()
        
        # 创建协调器
        self.coordinator = ScanCoordinator(
            cluster_scanner=self.mock_scanner,
            resource_parser=self.mock_parser,
            cache_manager=self.mock_cache_manager,
            static_ttl=1800,
            dynamic_ttl=300
        )
    
    async def test_scan_cluster_full_success(self):
        """测试完整集群扫描成功"""
        # 模拟扫描器返回值
        self.mock_scanner.scan_static_resources = AsyncMock(return_value={
            'cluster': {'name': 'test-cluster'},
            'namespaces': [{'name': 'default'}],
            'nodes': [{'name': 'node-1'}]
        })
        
        self.mock_scanner.scan_dynamic_resources = AsyncMock(return_value={
            'pods': [{'name': 'test-pod'}],
            'services': [{'name': 'test-service'}]
        })
        
        # 模拟解析器返回值
        self.mock_parser.parse_cluster_info.return_value = Mock()
        self.mock_parser.parse_namespaces.return_value = [Mock()]
        self.mock_parser.parse_nodes.return_value = [Mock()]
        self.mock_parser.parse_pods.return_value = [Mock()]
        self.mock_parser.parse_services.return_value = [Mock()]
        
        # 模拟缓存管理器
        self.mock_cache_manager.create_record = Mock()
        self.mock_cache_manager.get_record.return_value = None
        
        # 执行扫描
        result = await self.coordinator.scan_cluster_full('test-cluster')
        
        # 验证结果
        self.assertEqual(result['cluster_name'], 'test-cluster')
        self.assertIn('static_resources', result)
        self.assertIn('dynamic_resources', result)
        self.assertIn('statistics', result)
        
        # 验证统计信息
        stats = self.coordinator.get_coordinator_stats()
        self.assertEqual(stats['scan_sessions'], 1)
        self.assertEqual(stats['successful_scans'], 1)


async def run_async_tests():
    """运行异步测试"""
    # 创建测试实例并初始化
    scanner_tests = TestClusterScanner()
    scanner_tests.setUp()

    coordinator_tests = TestScanCoordinator()
    coordinator_tests.setUp()

    try:
        # 运行异步测试方法
        await scanner_tests.test_scan_static_resources_success()
        print("✅ 静态资源扫描测试通过")

        await scanner_tests.test_scan_dynamic_resources_success()
        print("✅ 动态资源扫描测试通过")

        await scanner_tests.test_tool_not_found_error()
        print("✅ 工具不存在错误测试通过")

        await scanner_tests.test_scan_timeout_error()
        print("✅ 扫描超时错误测试通过")

        await coordinator_tests.test_scan_cluster_full_success()
        print("✅ 完整集群扫描测试通过")

        print("✅ 所有异步测试通过")

    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 运行同步测试
    print("运行同步测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # 运行异步测试
    print("\n运行异步测试...")
    asyncio.run(run_async_tests())
