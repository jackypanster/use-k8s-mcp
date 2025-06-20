"""
资源解析器
将MCP工具返回的原始数据解析为标准化的数据模型
遵循单一职责原则，专注于数据转换和验证
"""

import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .exceptions import ResourceParseError, ScanValidationError
from src.cache.models import (
    ClusterInfo, NamespaceInfo, NodeInfo, PodInfo, ServiceInfo
)


class ResourceParser:
    """资源解析器 - 专注数据转换和验证"""
    
    def __init__(self) -> None:
        """初始化资源解析器"""
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_cluster_info(
        self,
        raw_data: Dict[str, Any],
        cluster_name: Optional[str] = None
    ) -> ClusterInfo:
        """解析集群信息
        
        Args:
            raw_data: MCP工具返回的原始集群数据
            cluster_name: 集群名称（可选）
            
        Returns:
            解析后的集群信息对象
            
        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()
        
        try:
            # 提取必需字段
            name = cluster_name or raw_data.get('name', 'unknown')
            version = raw_data.get('version', raw_data.get('serverVersion', 'unknown'))
            api_server = raw_data.get('server', raw_data.get('apiServer', 'unknown'))
            
            # 计算节点数量
            node_count = 0
            if 'nodes' in raw_data:
                node_count = len(raw_data['nodes'])
            elif 'nodeCount' in raw_data:
                node_count = raw_data['nodeCount']
            
            # 创建集群信息对象
            cluster_info = ClusterInfo(
                name=name,
                version=version,
                api_server=api_server,
                node_count=node_count
            )
            
            self.parsed_count += 1
            return cluster_info
            
        except Exception as e:
            self.error_count += 1
            raise ResourceParseError(f"集群信息解析失败: {e}") from e
    
    def parse_namespaces(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[NamespaceInfo]:
        """解析命名空间列表
        
        Args:
            raw_data: MCP工具返回的原始命名空间数据列表
            cluster_name: 集群名称
            
        Returns:
            解析后的命名空间信息列表
            
        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()
        
        try:
            namespaces = []
            
            for ns_data in raw_data:
                # 提取基础信息
                name = ns_data.get('metadata', {}).get('name', ns_data.get('name'))
                if not name:
                    continue
                
                status = ns_data.get('status', {}).get('phase', 'Unknown')
                labels = ns_data.get('metadata', {}).get('labels', {})
                annotations = ns_data.get('metadata', {}).get('annotations', {})
                
                # 创建命名空间对象
                namespace_info = NamespaceInfo(
                    cluster_name=cluster_name,
                    name=name,
                    status=status,
                    labels=labels,
                    annotations=annotations
                )
                
                namespaces.append(namespace_info)
            
            self.parsed_count += len(namespaces)
            return namespaces
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_namespaces",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"命名空间解析失败: {e}", context) from e
    
    def parse_nodes(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[NodeInfo]:
        """解析节点列表
        
        Args:
            raw_data: MCP工具返回的原始节点数据列表
            cluster_name: 集群名称
            
        Returns:
            解析后的节点信息列表
            
        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()
        
        try:
            nodes = []
            
            for node_data in raw_data:
                # 提取基础信息
                name = node_data.get('metadata', {}).get('name', node_data.get('name'))
                if not name:
                    continue
                
                # 解析节点状态
                status = self._extract_node_status(node_data)
                
                # 解析节点角色
                roles = self._extract_node_roles(node_data)
                
                # 解析资源信息
                capacity = node_data.get('status', {}).get('capacity', {})
                allocatable = node_data.get('status', {}).get('allocatable', {})
                
                # 解析标签和污点
                labels = node_data.get('metadata', {}).get('labels', {})
                taints = node_data.get('spec', {}).get('taints', [])
                
                # 创建节点对象
                node_info = NodeInfo(
                    cluster_name=cluster_name,
                    name=name,
                    status=status,
                    roles=roles,
                    capacity=capacity,
                    allocatable=allocatable,
                    labels=labels,
                    taints=taints
                )
                
                nodes.append(node_info)
            
            self.parsed_count += len(nodes)
            return nodes
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_nodes",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"节点解析失败: {e}", context) from e
    
    def parse_pods(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[PodInfo]:
        """解析Pod列表
        
        Args:
            raw_data: MCP工具返回的原始Pod数据列表
            cluster_name: 集群名称
            
        Returns:
            解析后的Pod信息列表
            
        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()
        
        try:
            pods = []
            
            for pod_data in raw_data:
                # 提取基础信息
                metadata = pod_data.get('metadata', {})
                name = metadata.get('name')
                namespace = metadata.get('namespace', 'default')
                
                if not name:
                    continue
                
                # 解析Pod状态
                status_info = pod_data.get('status', {})
                phase = status_info.get('phase', 'Unknown')
                status = self._extract_pod_status(pod_data)
                
                # 解析节点信息
                node_name = pod_data.get('spec', {}).get('nodeName')
                
                # 解析标签和容器
                labels = metadata.get('labels', {})
                containers = self._extract_container_info(pod_data)
                
                # 创建Pod对象
                pod_info = PodInfo(
                    cluster_name=cluster_name,
                    namespace=namespace,
                    name=name,
                    status=status,
                    phase=phase,
                    node_name=node_name,
                    labels=labels,
                    containers=containers
                )
                
                pods.append(pod_info)
            
            self.parsed_count += len(pods)
            return pods
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_pods",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"Pod解析失败: {e}", context) from e
    
    def parse_services(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[ServiceInfo]:
        """解析服务列表
        
        Args:
            raw_data: MCP工具返回的原始服务数据列表
            cluster_name: 集群名称
            
        Returns:
            解析后的服务信息列表
            
        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()
        
        try:
            services = []
            
            for svc_data in raw_data:
                # 提取基础信息
                metadata = svc_data.get('metadata', {})
                name = metadata.get('name')
                namespace = metadata.get('namespace', 'default')
                
                if not name:
                    continue
                
                # 解析服务规格
                spec = svc_data.get('spec', {})
                service_type = spec.get('type', 'ClusterIP')
                cluster_ip = spec.get('clusterIP')
                selector = spec.get('selector', {})
                ports = spec.get('ports', [])
                
                # 解析外部IP
                external_ip = None
                if service_type == 'LoadBalancer':
                    status = svc_data.get('status', {})
                    ingress = status.get('loadBalancer', {}).get('ingress', [])
                    if ingress:
                        external_ip = ingress[0].get('ip')
                
                # 创建服务对象
                service_info = ServiceInfo(
                    cluster_name=cluster_name,
                    namespace=namespace,
                    name=name,
                    type=service_type,
                    cluster_ip=cluster_ip,
                    external_ip=external_ip,
                    ports=ports,
                    selector=selector
                )
                
                services.append(service_info)
            
            self.parsed_count += len(services)
            return services
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_services",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"服务解析失败: {e}", context) from e
    
    def _extract_node_status(self, node_data: Dict[str, Any]) -> str:
        """提取节点状态"""
        conditions = node_data.get('status', {}).get('conditions', [])
        for condition in conditions:
            if condition.get('type') == 'Ready':
                return 'Ready' if condition.get('status') == 'True' else 'NotReady'
        return 'Unknown'
    
    def _extract_node_roles(self, node_data: Dict[str, Any]) -> List[str]:
        """提取节点角色"""
        labels = node_data.get('metadata', {}).get('labels', {})
        roles = []
        
        # 检查常见的角色标签
        role_labels = [
            'node-role.kubernetes.io/master',
            'node-role.kubernetes.io/control-plane',
            'node-role.kubernetes.io/worker'
        ]
        
        for label in role_labels:
            if label in labels:
                role = label.split('/')[-1]
                roles.append(role)
        
        return roles if roles else ['worker']
    
    def _extract_pod_status(self, pod_data: Dict[str, Any]) -> str:
        """提取Pod状态"""
        status_info = pod_data.get('status', {})
        phase = status_info.get('phase', 'Unknown')
        
        # 检查容器状态
        container_statuses = status_info.get('containerStatuses', [])
        if container_statuses:
            all_ready = all(cs.get('ready', False) for cs in container_statuses)
            if phase == 'Running' and all_ready:
                return 'Running'
            elif phase == 'Running' and not all_ready:
                return 'NotReady'
        
        return phase
    
    def _extract_container_info(self, pod_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取容器信息"""
        containers = []
        
        # 从spec获取容器定义
        spec_containers = pod_data.get('spec', {}).get('containers', [])
        status_containers = pod_data.get('status', {}).get('containerStatuses', [])
        
        # 创建容器状态映射
        status_map = {cs.get('name'): cs for cs in status_containers}
        
        for container in spec_containers:
            name = container.get('name')
            image = container.get('image')
            
            # 获取容器状态
            container_status = status_map.get(name, {})
            ready = container_status.get('ready', False)
            restart_count = container_status.get('restartCount', 0)
            
            containers.append({
                'name': name,
                'image': image,
                'ready': ready,
                'restartCount': restart_count
            })
        
        return containers
    
    def parse_deployments(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[Dict[str, Any]]:
        """解析部署列表

        Args:
            raw_data: MCP工具返回的原始部署数据列表
            cluster_name: 集群名称

        Returns:
            解析后的部署信息列表（简化格式）

        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()

        try:
            deployments = []

            for deploy_data in raw_data:
                # 提取基础信息
                metadata = deploy_data.get('metadata', {})
                name = metadata.get('name')
                namespace = metadata.get('namespace', 'default')

                if not name:
                    continue

                # 解析部署规格
                spec = deploy_data.get('spec', {})
                replicas = spec.get('replicas', 1)
                selector = spec.get('selector', {})

                # 解析部署状态
                status = deploy_data.get('status', {})
                ready_replicas = status.get('readyReplicas', 0)
                available_replicas = status.get('availableReplicas', 0)

                # 创建部署信息对象（简化格式）
                deployment_info = {
                    'cluster_name': cluster_name,
                    'namespace': namespace,
                    'name': name,
                    'replicas': replicas,
                    'ready_replicas': ready_replicas,
                    'available_replicas': available_replicas,
                    'selector': selector,
                    'labels': metadata.get('labels', {})
                }

                deployments.append(deployment_info)

            self.parsed_count += len(deployments)
            return deployments

        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_deployments",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"部署解析失败: {e}", context) from e

    def parse_configmaps(
        self,
        raw_data: List[Dict[str, Any]],
        cluster_name: str
    ) -> List[Dict[str, Any]]:
        """解析ConfigMap列表

        Args:
            raw_data: MCP工具返回的原始ConfigMap数据列表
            cluster_name: 集群名称

        Returns:
            解析后的ConfigMap信息列表

        Raises:
            ResourceParseError: 解析失败时抛出
        """
        start_time = time.time()

        try:
            configmaps = []

            for cm_data in raw_data:
                # 提取基础信息
                metadata = cm_data.get('metadata', {})
                name = metadata.get('name')
                namespace = metadata.get('namespace', 'default')

                if not name:
                    continue

                # 解析数据
                data = cm_data.get('data', {})
                binary_data = cm_data.get('binaryData', {})

                # 创建ConfigMap信息对象
                configmap_info = {
                    'cluster_name': cluster_name,
                    'namespace': namespace,
                    'name': name,
                    'data_keys': list(data.keys()),
                    'binary_data_keys': list(binary_data.keys()),
                    'total_keys': len(data) + len(binary_data),
                    'labels': metadata.get('labels', {}),
                    'annotations': metadata.get('annotations', {})
                }

                configmaps.append(configmap_info)

            self.parsed_count += len(configmaps)
            return configmaps

        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="parse_configmaps",
                cluster_name=cluster_name,
                raw_data_count=len(raw_data) if isinstance(raw_data, list) else 0,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ResourceParseError(f"ConfigMap解析失败: {e}", context) from e

    def validate_parsed_data(
        self,
        data: Any,
        resource_type: str,
        required_fields: List[str]
    ) -> bool:
        """验证解析后的数据

        Args:
            data: 解析后的数据
            resource_type: 资源类型
            required_fields: 必需字段列表

        Returns:
            验证是否通过

        Raises:
            ScanValidationError: 验证失败时抛出
        """
        try:
            if not data:
                raise ValueError("数据不能为空")

            # 检查必需字段
            if isinstance(data, dict):
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)

                if missing_fields:
                    raise ValueError(f"缺少必需字段: {missing_fields}")

            # 检查数据类型特定的验证
            if resource_type == 'cluster':
                if not isinstance(data.get('node_count'), int) or data['node_count'] < 0:
                    raise ValueError("节点数量必须是非负整数")

            elif resource_type == 'pod':
                valid_phases = ['Pending', 'Running', 'Succeeded', 'Failed', 'Unknown']
                if data.get('phase') not in valid_phases:
                    raise ValueError(f"无效的Pod阶段: {data.get('phase')}")

            elif resource_type == 'service':
                valid_types = ['ClusterIP', 'NodePort', 'LoadBalancer', 'ExternalName']
                if data.get('type') not in valid_types:
                    raise ValueError(f"无效的服务类型: {data.get('type')}")

            return True

        except Exception as e:
            context = create_exception_context(
                operation="validate_parsed_data",
                resource_type=resource_type,
                required_fields=required_fields,
                original_error=str(e)
            )
            raise ScanValidationError(f"数据验证失败: {e}", context) from e

    def get_parsing_stats(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            'parsed_count': self.parsed_count,
            'error_count': self.error_count,
            'success_rate': (
                (self.parsed_count - self.error_count) / max(1, self.parsed_count)
            ) * 100
        }
