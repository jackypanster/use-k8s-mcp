"""
缓存系统基础功能测试
验证SQLite数据库、数据模型和缓存管理器的核心功能
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.update({
    'CACHE_DB_PATH': './test_data/test_k8s_cache.db',
    'CACHE_DB_TIMEOUT': '10',
    'CACHE_DB_MAX_CONNECTIONS': '5',
    'CACHE_STATIC_TTL': '1800',
    'CACHE_DYNAMIC_TTL': '300',
    'CACHE_TOOL_MAPPING_TTL': '3600'
})

from src.cache import CacheManager, ClusterInfo, NamespaceInfo, PodInfo, MCPToolInfo


class TestCacheSystem(unittest.TestCase):
    """缓存系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据目录
        test_data_dir = Path('./test_data')
        test_data_dir.mkdir(exist_ok=True)
        
        # 删除已存在的测试数据库
        test_db_path = Path('./test_data/test_k8s_cache.db')
        if test_db_path.exists():
            test_db_path.unlink()
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager()
    
    def tearDown(self):
        """测试后清理"""
        self.cache_manager.close()
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        # 验证数据库文件创建
        db_path = Path('./test_data/test_k8s_cache.db')
        self.assertTrue(db_path.exists(), "数据库文件应该被创建")
        
        # 验证数据库统计
        stats = self.cache_manager.get_cache_stats()
        self.assertIn('clusters', stats, "应该包含clusters表统计")
        self.assertIn('namespaces', stats, "应该包含namespaces表统计")
        self.assertIn('pods', stats, "应该包含pods表统计")
        self.assertIn('mcp_tools', stats, "应该包含mcp_tools表统计")
        
        print("✅ 数据库初始化测试通过")
    
    def test_cluster_info_crud(self):
        """测试集群信息CRUD操作"""
        # 创建集群信息
        cluster = ClusterInfo(
            name="test-cluster",
            version="v1.28.0",
            api_server="https://test-cluster.example.com:6443",
            node_count=3
        )
        
        # 测试创建
        cluster_id = self.cache_manager.create_record('clusters', cluster)
        self.assertIsInstance(cluster_id, int, "应该返回记录ID")
        self.assertGreater(cluster_id, 0, "记录ID应该大于0")
        
        # 测试获取
        retrieved_cluster = self.cache_manager.get_record('clusters', name="test-cluster")
        self.assertIsNotNone(retrieved_cluster, "应该能够获取到集群记录")
        self.assertEqual(retrieved_cluster.name, "test-cluster", "集群名称应该匹配")
        self.assertEqual(retrieved_cluster.version, "v1.28.0", "集群版本应该匹配")
        
        # 测试更新
        updated = self.cache_manager.update_record('clusters', cluster_id, {
            'node_count': 5,
            'version': 'v1.28.1'
        })
        self.assertTrue(updated, "更新操作应该成功")
        
        # 验证更新结果
        updated_cluster = self.cache_manager.get_record('clusters', name="test-cluster")
        self.assertEqual(updated_cluster.node_count, 5, "节点数量应该被更新")
        self.assertEqual(updated_cluster.version, "v1.28.1", "版本应该被更新")
        
        # 测试删除
        deleted_count = self.cache_manager.delete_record('clusters', name="test-cluster")
        self.assertEqual(deleted_count, 1, "应该删除1条记录")
        
        # 验证删除结果
        deleted_cluster = self.cache_manager.get_record('clusters', name="test-cluster")
        self.assertIsNone(deleted_cluster, "删除后应该无法获取到记录")
        
        print("✅ 集群信息CRUD测试通过")
    
    def test_namespace_info_with_json_fields(self):
        """测试命名空间信息（包含JSON字段）"""
        # 创建命名空间信息
        namespace = NamespaceInfo(
            cluster_name="test-cluster",
            name="test-namespace",
            status="Active",
            labels={"env": "test", "team": "platform"},
            annotations={"description": "测试命名空间", "owner": "platform-team"}
        )
        
        # 测试创建
        ns_id = self.cache_manager.create_record('namespaces', namespace)
        self.assertGreater(ns_id, 0, "应该成功创建命名空间记录")
        
        # 测试获取（验证JSON字段序列化/反序列化）
        retrieved_ns = self.cache_manager.get_record('namespaces', 
                                                   cluster_name="test-cluster", 
                                                   name="test-namespace")
        self.assertIsNotNone(retrieved_ns, "应该能够获取到命名空间记录")
        self.assertEqual(retrieved_ns.labels["env"], "test", "标签应该正确反序列化")
        self.assertEqual(retrieved_ns.annotations["description"], "测试命名空间", "注解应该正确反序列化")
        
        print("✅ 命名空间JSON字段测试通过")
    
    def test_batch_operations(self):
        """测试批量操作"""
        # 准备批量数据
        pods = [
            PodInfo(
                cluster_name="test-cluster",
                namespace="default",
                name=f"test-pod-{i}",
                status="Running",
                phase="Running",
                node_name=f"node-{i % 3}",
                labels={"app": "test", "instance": str(i)}
            )
            for i in range(5)
        ]
        
        # 测试批量创建
        pod_ids = self.cache_manager.batch_create_records('pods', pods)
        self.assertEqual(len(pod_ids), 5, "应该创建5个Pod记录")
        self.assertTrue(all(pid > 0 for pid in pod_ids), "所有记录ID应该有效")
        
        # 测试批量查询
        retrieved_pods = self.cache_manager.list_records('pods', 
                                                       cluster_name="test-cluster",
                                                       namespace="default")
        self.assertEqual(len(retrieved_pods), 5, "应该获取到5个Pod记录")
        
        # 验证数据完整性
        pod_names = {pod.name for pod in retrieved_pods}
        expected_names = {f"test-pod-{i}" for i in range(5)}
        self.assertEqual(pod_names, expected_names, "Pod名称应该完全匹配")
        
        print("✅ 批量操作测试通过")
    
    def test_mcp_tool_mapping(self):
        """测试MCP工具映射"""
        # 创建工具信息
        tool = MCPToolInfo(
            name="list_pods",
            description="列出指定命名空间的所有Pod",
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "label_selector": {"type": "string"}
                },
                "required": ["namespace"]
            },
            output_schema={
                "type": "array",
                "items": {"type": "object"}
            },
            resource_types=["pod"],
            operation_types=["list", "read"],
            required_params=["namespace"],
            optional_params=["label_selector", "field_selector"]
        )
        
        # 测试创建
        tool_id = self.cache_manager.create_record('mcp_tools', tool)
        self.assertGreater(tool_id, 0, "应该成功创建工具记录")
        
        # 测试获取
        retrieved_tool = self.cache_manager.get_record('mcp_tools', name="list_pods")
        self.assertIsNotNone(retrieved_tool, "应该能够获取到工具记录")
        self.assertEqual(retrieved_tool.name, "list_pods", "工具名称应该匹配")
        self.assertIn("namespace", retrieved_tool.required_params, "必需参数应该包含namespace")
        self.assertEqual(retrieved_tool.input_schema["type"], "object", "输入schema应该正确反序列化")
        
        print("✅ MCP工具映射测试通过")
    
    def test_ttl_functionality(self):
        """测试TTL功能"""
        # 创建一个集群记录
        cluster = ClusterInfo(
            name="ttl-test-cluster",
            version="v1.28.0",
            api_server="https://ttl-test.example.com:6443",
            node_count=1
        )
        
        cluster_id = self.cache_manager.create_record('clusters', cluster)
        
        # 验证记录存在
        retrieved = self.cache_manager.get_record('clusters', name="ttl-test-cluster")
        self.assertIsNotNone(retrieved, "新创建的记录应该存在")
        
        # 手动设置过期时间为过去
        past_time = datetime.utcnow() - timedelta(hours=1)
        self.cache_manager.update_record('clusters', cluster_id, {
            'ttl_expires_at': past_time
        })
        
        # 验证过期记录不会被查询到
        expired_record = self.cache_manager.get_record('clusters', name="ttl-test-cluster")
        self.assertIsNone(expired_record, "过期记录不应该被查询到")
        
        # 测试清理过期记录
        cleanup_stats = self.cache_manager.cleanup_expired_cache()
        self.assertIn('clusters', cleanup_stats, "清理统计应该包含clusters表")
        self.assertGreaterEqual(cleanup_stats['clusters'], 1, "应该清理至少1条过期记录")
        
        print("✅ TTL功能测试通过")
    
    def test_cache_statistics(self):
        """测试缓存统计功能"""
        # 创建一些测试数据
        cluster = ClusterInfo(
            name="stats-test-cluster",
            version="v1.28.0",
            api_server="https://stats-test.example.com:6443",
            node_count=2
        )
        self.cache_manager.create_record('clusters', cluster)
        
        # 获取统计信息
        stats = self.cache_manager.get_cache_stats()
        
        # 验证统计信息结构
        self.assertIn('clusters', stats, "统计应该包含clusters表")
        self.assertIn('ttl_stats', stats, "统计应该包含TTL信息")
        self.assertIn('db_size_bytes', stats, "统计应该包含数据库大小")
        self.assertIn('active_connections', stats, "统计应该包含连接池信息")
        
        # 验证TTL统计
        ttl_stats = stats['ttl_stats']
        self.assertIn('clusters', ttl_stats, "TTL统计应该包含clusters表")
        
        cluster_ttl = ttl_stats['clusters']
        self.assertIn('valid_records', cluster_ttl, "应该包含有效记录数")
        self.assertIn('expired_records', cluster_ttl, "应该包含过期记录数")
        self.assertIn('total_records', cluster_ttl, "应该包含总记录数")
        
        self.assertGreaterEqual(cluster_ttl['valid_records'], 1, "应该至少有1条有效记录")
        
        print("✅ 缓存统计测试通过")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
