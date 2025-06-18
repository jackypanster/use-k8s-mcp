"""
集群扫描器基础功能测试
验证核心组件的基本功能
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scanner.resource_parser import ResourceParser
from src.cache.models import ClusterInfo, NamespaceInfo, NodeInfo, PodInfo, ServiceInfo


class TestResourceParserBasic(unittest.TestCase):
    """资源解析器基础测试"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = ResourceParser()
    
    def test_parse_cluster_info_basic(self):
        """测试基础集群信息解析"""
        raw_data = {
            'name': 'test-cluster',
            'version': 'v1.23.15',
            'server': 'https://test-cluster:6443',
            'nodeCount': 3
        }
        
        cluster_info = self.parser.parse_cluster_info(raw_data, 'test-cluster')
        
        self.assertIsInstance(cluster_info, ClusterInfo)
        self.assertEqual(cluster_info.name, 'test-cluster')
        self.assertEqual(cluster_info.version, 'v1.23.15')
        self.assertEqual(cluster_info.api_server, 'https://test-cluster:6443')
        self.assertEqual(cluster_info.node_count, 3)
        
        print("✅ 集群信息解析测试通过")
    
    def test_parse_namespaces_basic(self):
        """测试基础命名空间解析"""
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
        self.assertIsInstance(namespaces[0], NamespaceInfo)
        self.assertEqual(namespaces[0].name, 'default')
        self.assertEqual(namespaces[0].cluster_name, 'test-cluster')
        self.assertEqual(namespaces[0].status, 'Active')
        self.assertEqual(namespaces[1].name, 'kube-system')
        
        print("✅ 命名空间解析测试通过")
    
    def test_parse_nodes_basic(self):
        """测试基础节点解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'master-node',
                    'labels': {
                        'node-role.kubernetes.io/master': '',
                        'kubernetes.io/hostname': 'master-node'
                    }
                },
                'status': {
                    'conditions': [
                        {'type': 'Ready', 'status': 'True'}
                    ],
                    'capacity': {
                        'cpu': '4',
                        'memory': '8Gi'
                    },
                    'allocatable': {
                        'cpu': '3800m',
                        'memory': '7.5Gi'
                    }
                },
                'spec': {
                    'taints': [
                        {
                            'key': 'node-role.kubernetes.io/master',
                            'effect': 'NoSchedule'
                        }
                    ]
                }
            }
        ]
        
        nodes = self.parser.parse_nodes(raw_data, 'test-cluster')
        
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertIsInstance(node, NodeInfo)
        self.assertEqual(node.name, 'master-node')
        self.assertEqual(node.cluster_name, 'test-cluster')
        self.assertEqual(node.status, 'Ready')
        self.assertIn('master', node.roles)
        self.assertEqual(node.capacity['cpu'], '4')
        self.assertEqual(len(node.taints), 1)
        
        print("✅ 节点解析测试通过")
    
    def test_parse_pods_basic(self):
        """测试基础Pod解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'test-pod',
                    'namespace': 'default',
                    'labels': {'app': 'test', 'version': 'v1'}
                },
                'status': {
                    'phase': 'Running',
                    'containerStatuses': [
                        {
                            'name': 'test-container',
                            'ready': True,
                            'restartCount': 0
                        }
                    ]
                },
                'spec': {
                    'nodeName': 'worker-node-1',
                    'containers': [
                        {
                            'name': 'test-container',
                            'image': 'nginx:1.20'
                        }
                    ]
                }
            }
        ]
        
        pods = self.parser.parse_pods(raw_data, 'test-cluster')
        
        self.assertEqual(len(pods), 1)
        pod = pods[0]
        self.assertIsInstance(pod, PodInfo)
        self.assertEqual(pod.name, 'test-pod')
        self.assertEqual(pod.namespace, 'default')
        self.assertEqual(pod.cluster_name, 'test-cluster')
        self.assertEqual(pod.phase, 'Running')
        self.assertEqual(pod.node_name, 'worker-node-1')
        self.assertEqual(len(pod.containers), 1)
        self.assertEqual(pod.containers[0]['name'], 'test-container')
        self.assertEqual(pod.containers[0]['image'], 'nginx:1.20')
        self.assertTrue(pod.containers[0]['ready'])
        
        print("✅ Pod解析测试通过")
    
    def test_parse_services_basic(self):
        """测试基础服务解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'test-service',
                    'namespace': 'default'
                },
                'spec': {
                    'type': 'ClusterIP',
                    'clusterIP': '10.96.0.1',
                    'selector': {'app': 'test'},
                    'ports': [
                        {
                            'name': 'http',
                            'port': 80,
                            'targetPort': 8080,
                            'protocol': 'TCP'
                        }
                    ]
                }
            },
            {
                'metadata': {
                    'name': 'lb-service',
                    'namespace': 'default'
                },
                'spec': {
                    'type': 'LoadBalancer',
                    'clusterIP': '10.96.0.2',
                    'selector': {'app': 'web'},
                    'ports': [
                        {
                            'name': 'https',
                            'port': 443,
                            'targetPort': 8443,
                            'protocol': 'TCP'
                        }
                    ]
                },
                'status': {
                    'loadBalancer': {
                        'ingress': [
                            {'ip': '203.0.113.1'}
                        ]
                    }
                }
            }
        ]
        
        services = self.parser.parse_services(raw_data, 'test-cluster')
        
        self.assertEqual(len(services), 2)
        
        # 测试ClusterIP服务
        cluster_service = services[0]
        self.assertIsInstance(cluster_service, ServiceInfo)
        self.assertEqual(cluster_service.name, 'test-service')
        self.assertEqual(cluster_service.namespace, 'default')
        self.assertEqual(cluster_service.cluster_name, 'test-cluster')
        self.assertEqual(cluster_service.type, 'ClusterIP')
        self.assertEqual(cluster_service.cluster_ip, '10.96.0.1')
        self.assertIsNone(cluster_service.external_ip)
        self.assertEqual(len(cluster_service.ports), 1)
        self.assertEqual(cluster_service.ports[0]['port'], 80)
        
        # 测试LoadBalancer服务
        lb_service = services[1]
        self.assertEqual(lb_service.name, 'lb-service')
        self.assertEqual(lb_service.type, 'LoadBalancer')
        self.assertEqual(lb_service.external_ip, '203.0.113.1')
        
        print("✅ 服务解析测试通过")
    
    def test_parsing_stats(self):
        """测试解析统计功能"""
        # 执行一些解析操作
        cluster_data = {'name': 'test', 'version': 'v1.23', 'server': 'https://test:6443', 'nodeCount': 1}
        self.parser.parse_cluster_info(cluster_data, 'test')
        
        namespace_data = [{'metadata': {'name': 'default'}, 'status': {'phase': 'Active'}}]
        self.parser.parse_namespaces(namespace_data, 'test')
        
        # 获取统计信息
        stats = self.parser.get_parsing_stats()
        
        self.assertIn('parsed_count', stats)
        self.assertIn('error_count', stats)
        self.assertIn('success_rate', stats)
        self.assertGreater(stats['parsed_count'], 0)
        self.assertEqual(stats['error_count'], 0)
        self.assertEqual(stats['success_rate'], 100.0)
        
        print("✅ 解析统计测试通过")

    def test_parse_deployments_basic(self):
        """测试基础部署解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'web-deployment',
                    'namespace': 'production',
                    'labels': {'app': 'web', 'tier': 'frontend'}
                },
                'spec': {
                    'replicas': 3,
                    'selector': {'matchLabels': {'app': 'web'}}
                },
                'status': {
                    'readyReplicas': 3,
                    'availableReplicas': 3,
                    'replicas': 3
                }
            }
        ]

        deployments = self.parser.parse_deployments(raw_data, 'test-cluster')

        self.assertEqual(len(deployments), 1)
        deploy = deployments[0]
        self.assertEqual(deploy['name'], 'web-deployment')
        self.assertEqual(deploy['namespace'], 'production')
        self.assertEqual(deploy['cluster_name'], 'test-cluster')
        self.assertEqual(deploy['replicas'], 3)
        self.assertEqual(deploy['ready_replicas'], 3)
        self.assertEqual(deploy['available_replicas'], 3)

        print("✅ 部署解析测试通过")

    def test_parse_configmaps_basic(self):
        """测试基础ConfigMap解析"""
        raw_data = [
            {
                'metadata': {
                    'name': 'app-config',
                    'namespace': 'production',
                    'labels': {'app': 'web'}
                },
                'data': {
                    'database.url': 'postgres://localhost:5432/app',
                    'redis.url': 'redis://localhost:6379',
                    'log.level': 'INFO'
                },
                'binaryData': {
                    'cert.pem': 'LS0tLS1CRUdJTi...'
                }
            }
        ]

        configmaps = self.parser.parse_configmaps(raw_data, 'test-cluster')

        self.assertEqual(len(configmaps), 1)
        cm = configmaps[0]
        self.assertEqual(cm['name'], 'app-config')
        self.assertEqual(cm['namespace'], 'production')
        self.assertEqual(cm['cluster_name'], 'test-cluster')
        self.assertEqual(len(cm['data_keys']), 3)
        self.assertEqual(len(cm['binary_data_keys']), 1)
        self.assertEqual(cm['total_keys'], 4)
        self.assertIn('database.url', cm['data_keys'])
        self.assertIn('cert.pem', cm['binary_data_keys'])

        print("✅ ConfigMap解析测试通过")

    def test_validate_parsed_data(self):
        """测试数据验证功能"""
        # 测试集群数据验证
        cluster_data = {
            'name': 'test-cluster',
            'version': 'v1.23.15',
            'api_server': 'https://test:6443',
            'node_count': 3
        }

        result = self.parser.validate_parsed_data(
            cluster_data,
            'cluster',
            ['name', 'version', 'api_server', 'node_count']
        )
        self.assertTrue(result)

        # 测试Pod数据验证
        pod_data = {
            'name': 'test-pod',
            'namespace': 'default',
            'cluster_name': 'test-cluster',
            'phase': 'Running',
            'status': 'Running'
        }

        result = self.parser.validate_parsed_data(
            pod_data,
            'pod',
            ['name', 'namespace', 'cluster_name', 'phase']
        )
        self.assertTrue(result)

        # 测试服务数据验证
        service_data = {
            'name': 'test-service',
            'namespace': 'default',
            'cluster_name': 'test-cluster',
            'type': 'ClusterIP'
        }

        result = self.parser.validate_parsed_data(
            service_data,
            'service',
            ['name', 'namespace', 'cluster_name', 'type']
        )
        self.assertTrue(result)

        print("✅ 数据验证测试通过")


class TestDataModels(unittest.TestCase):
    """数据模型测试"""
    
    def test_cluster_info_model(self):
        """测试集群信息模型"""
        cluster = ClusterInfo(
            name='test-cluster',
            version='v1.23.15',
            api_server='https://test:6443',
            node_count=3
        )
        
        # 测试基本属性
        self.assertEqual(cluster.name, 'test-cluster')
        self.assertEqual(cluster.version, 'v1.23.15')
        self.assertEqual(cluster.node_count, 3)
        
        # 测试序列化
        data_dict = cluster.to_dict()
        self.assertIn('name', data_dict)
        self.assertIn('version', data_dict)
        self.assertIn('node_count', data_dict)
        
        # 测试反序列化
        cluster2 = ClusterInfo.from_dict(data_dict)
        self.assertEqual(cluster2.name, cluster.name)
        self.assertEqual(cluster2.version, cluster.version)
        
        print("✅ 集群信息模型测试通过")
    
    def test_namespace_info_model(self):
        """测试命名空间信息模型"""
        namespace = NamespaceInfo(
            cluster_name='test-cluster',
            name='default',
            status='Active',
            labels={'name': 'default'},
            annotations={'created-by': 'system'}
        )
        
        self.assertEqual(namespace.cluster_name, 'test-cluster')
        self.assertEqual(namespace.name, 'default')
        self.assertEqual(namespace.status, 'Active')
        self.assertEqual(namespace.labels['name'], 'default')
        
        print("✅ 命名空间信息模型测试通过")


if __name__ == '__main__':
    print("运行集群扫描器基础功能测试...")
    unittest.main(verbosity=2)
