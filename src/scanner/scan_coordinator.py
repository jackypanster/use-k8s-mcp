"""
扫描协调器
协调整个扫描流程，包括扫描任务调度、错误处理、重试机制和扫描状态管理
遵循单一职责原则，专注于流程编排
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone

from .cluster_scanner import ClusterScanner
from .resource_parser import ResourceParser
from .exceptions import ScanError, ScanTimeoutError
from src.cache import CacheManager, CacheMetadata


class ScanCoordinator:
    """扫描协调器 - 专注流程编排和状态管理"""
    
    def __init__(
        self,
        cluster_scanner: ClusterScanner,
        resource_parser: ResourceParser,
        cache_manager: CacheManager,
        static_ttl: int = 1800,  # 30分钟
        dynamic_ttl: int = 300,  # 5分钟
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> None:
        """初始化扫描协调器
        
        Args:
            cluster_scanner: 集群扫描器实例
            resource_parser: 资源解析器实例
            cache_manager: 缓存管理器实例
            static_ttl: 静态资源TTL（秒）
            dynamic_ttl: 动态资源TTL（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.cluster_scanner = cluster_scanner
        self.resource_parser = resource_parser
        self.cache_manager = cache_manager
        self.static_ttl = static_ttl
        self.dynamic_ttl = dynamic_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 统计信息
        self.scan_sessions = 0
        self.successful_scans = 0
        self.failed_scans = 0
    
    async def scan_cluster_full(
        self,
        cluster_name: str,
        include_static: bool = True,
        include_dynamic: bool = True
    ) -> Dict[str, Any]:
        """执行完整的集群扫描
        
        Args:
            cluster_name: 集群名称
            include_static: 是否包含静态资源扫描
            include_dynamic: 是否包含动态资源扫描
            
        Returns:
            扫描结果统计
            
        Raises:
            ScanError: 扫描失败时抛出
        """
        start_time = time.time()
        self.scan_sessions += 1
        
        try:
            results = {
                'cluster_name': cluster_name,
                'scan_start_time': datetime.now(timezone.utc).isoformat(),
                'static_resources': {},
                'dynamic_resources': {},
                'statistics': {}
            }
            
            # 扫描静态资源
            if include_static:
                await self._update_scan_status(cluster_name, 'static', 'running')
                static_results = await self._scan_static_with_retry(cluster_name)
                results['static_resources'] = static_results
                await self._update_scan_status(cluster_name, 'static', 'completed')
            
            # 扫描动态资源
            if include_dynamic:
                await self._update_scan_status(cluster_name, 'dynamic', 'running')
                dynamic_results = await self._scan_dynamic_with_retry(cluster_name)
                results['dynamic_resources'] = dynamic_results
                await self._update_scan_status(cluster_name, 'dynamic', 'completed')
            
            # 计算统计信息
            results['statistics'] = self._calculate_scan_statistics(results)
            results['scan_duration'] = time.time() - start_time
            
            self.successful_scans += 1
            return results
            
        except Exception as e:
            self.failed_scans += 1
            await self._update_scan_status(cluster_name, 'all', 'failed', str(e))

            raise ScanError(f"集群完整扫描失败: {e}") from e
    
    async def _scan_static_with_retry(self, cluster_name: str) -> Dict[str, Any]:
        """带重试的静态资源扫描"""
        for attempt in range(self.max_retries + 1):
            try:
                # 执行静态资源扫描
                raw_data = await self.cluster_scanner.scan_static_resources(cluster_name)
                
                # 解析和存储数据
                parsed_data = await self._parse_and_store_static(raw_data, cluster_name)
                
                return {
                    'success': True,
                    'attempt': attempt + 1,
                    'data': parsed_data
                }
                
            except Exception as e:
                print(f"静态资源扫描尝试 {attempt + 1} 失败: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    print(f"静态资源扫描最终失败，已重试 {attempt + 1} 次")
                    return {
                        'success': False,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
    
    async def _scan_dynamic_with_retry(self, cluster_name: str) -> Dict[str, Any]:
        """带重试的动态资源扫描"""
        for attempt in range(self.max_retries + 1):
            try:
                # 执行动态资源扫描
                raw_data = await self.cluster_scanner.scan_dynamic_resources(cluster_name)
                
                # 解析和存储数据
                parsed_data = await self._parse_and_store_dynamic(raw_data, cluster_name)
                
                return {
                    'success': True,
                    'attempt': attempt + 1,
                    'data': parsed_data
                }
                
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    return {
                        'success': False,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
    
    async def _parse_and_store_static(
        self,
        raw_data: Dict[str, Any],
        cluster_name: str
    ) -> Dict[str, int]:
        """解析和存储静态资源数据"""
        results = {}
        
        # 解析集群信息
        if 'cluster' in raw_data:
            cluster_info = self.resource_parser.parse_cluster_info(
                raw_data['cluster'], cluster_name
            )
            self.cache_manager.create_record('clusters', cluster_info.to_dict())
            results['clusters'] = 1
        
        # 解析命名空间
        if 'namespaces' in raw_data:
            namespaces = self.resource_parser.parse_namespaces(
                raw_data['namespaces'], cluster_name
            )
            for ns in namespaces:
                self.cache_manager.create_record('namespaces', ns.to_dict())
            results['namespaces'] = len(namespaces)
        
        # 解析节点
        if 'nodes' in raw_data:
            nodes = self.resource_parser.parse_nodes(
                raw_data['nodes'], cluster_name
            )
            for node in nodes:
                self.cache_manager.create_record('nodes', node.to_dict())
            results['nodes'] = len(nodes)
        
        return results
    
    async def _parse_and_store_dynamic(
        self,
        raw_data: Dict[str, Any],
        cluster_name: str
    ) -> Dict[str, int]:
        """解析和存储动态资源数据"""
        results = {}
        
        # 解析Pod
        if 'pods' in raw_data:
            pods = self.resource_parser.parse_pods(
                raw_data['pods'], cluster_name
            )
            for pod in pods:
                self.cache_manager.create_record('pods', pod.to_dict())
            results['pods'] = len(pods)
        
        # 解析服务
        if 'services' in raw_data:
            services = self.resource_parser.parse_services(
                raw_data['services'], cluster_name
            )
            for service in services:
                self.cache_manager.create_record('services', service.to_dict())
            results['services'] = len(services)

        # 解析ConfigMap
        if 'configmaps' in raw_data:
            configmaps = self.resource_parser.parse_configmaps(
                raw_data['configmaps'], cluster_name
            )
            # ConfigMap作为配置数据，可以缓存较长时间
            for cm in configmaps:
                self.cache_manager.create_record('configmaps', cm)
            results['configmaps'] = len(configmaps)

        # 解析Secret（注意：不缓存敏感数据内容）
        if 'secrets' in raw_data:
            secrets = self.resource_parser.parse_configmaps(  # 复用configmap解析逻辑
                raw_data['secrets'], cluster_name
            )
            # Secret只缓存元数据，不缓存实际内容
            for secret in secrets:
                # 移除敏感数据
                secret_meta = {
                    'cluster_name': secret['cluster_name'],
                    'namespace': secret['namespace'],
                    'name': secret['name'],
                    'total_keys': secret['total_keys'],
                    'labels': secret['labels']
                }
                self.cache_manager.create_record('secrets', secret_meta)
            results['secrets'] = len(secrets)

        return results
    
    async def _update_scan_status(
        self,
        cluster_name: str,
        resource_type: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """更新扫描状态"""
        try:
            # 简化状态更新，只创建记录不更新
            table_name = f"{resource_type}_scan"

            metadata = CacheMetadata(
                table_name=table_name,
                cluster_name=cluster_name,
                scan_status=status,
                error_message=error_message,
                last_scan_at=datetime.now(timezone.utc) if status in ['completed', 'failed'] else None,
                next_scan_at=self._calculate_next_scan_time(resource_type)
            )

            # 直接创建记录，不检查是否存在
            self.cache_manager.create_record('cache_metadata', metadata)

        except Exception as e:
            # 状态更新失败不应该影响主流程
            print(f"警告: 扫描状态更新失败: {e}")
    
    def _calculate_next_scan_time(self, resource_type: str) -> datetime:
        """计算下次扫描时间"""
        if resource_type == 'static':
            return datetime.now(timezone.utc) + timedelta(seconds=self.static_ttl)
        elif resource_type == 'dynamic':
            return datetime.now(timezone.utc) + timedelta(seconds=self.dynamic_ttl)
        else:
            return datetime.now(timezone.utc) + timedelta(seconds=self.static_ttl)
    
    def _calculate_scan_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """计算扫描统计信息"""
        stats = {
            'total_resources': 0,
            'static_resources': 0,
            'dynamic_resources': 0,
            'resource_breakdown': {}
        }
        
        # 统计静态资源
        static_data = results.get('static_resources', {}).get('data', {})
        for resource_type, count in static_data.items():
            stats['static_resources'] += count
            stats['resource_breakdown'][resource_type] = count
        
        # 统计动态资源
        dynamic_data = results.get('dynamic_resources', {}).get('data', {})
        for resource_type, count in dynamic_data.items():
            stats['dynamic_resources'] += count
            stats['resource_breakdown'][resource_type] = count
        
        stats['total_resources'] = stats['static_resources'] + stats['dynamic_resources']
        
        return stats
    
    def get_coordinator_stats(self) -> Dict[str, Any]:
        """获取协调器统计信息"""
        return {
            'scan_sessions': self.scan_sessions,
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'success_rate': (
                self.successful_scans / max(1, self.scan_sessions)
            ) * 100,
            'scanner_stats': self.cluster_scanner.get_scan_stats(),
            'parser_stats': self.resource_parser.get_parsing_stats()
        }

    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查

        Returns:
            健康检查结果
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {},
            'issues': []
        }

        try:
            # 检查缓存管理器
            try:
                cache_stats = self.cache_manager.get_cache_stats()
                health_status['components']['cache_manager'] = {
                    'status': 'healthy',
                    'stats': cache_stats
                }
            except Exception as e:
                health_status['components']['cache_manager'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['issues'].append(f"缓存管理器异常: {e}")

            # 检查扫描器统计
            scanner_stats = self.cluster_scanner.get_scan_stats()
            if scanner_stats['success_rate'] < 50:
                health_status['issues'].append(
                    f"扫描器成功率过低: {scanner_stats['success_rate']:.1f}%"
                )

            health_status['components']['cluster_scanner'] = {
                'status': 'healthy' if scanner_stats['success_rate'] >= 50 else 'degraded',
                'stats': scanner_stats
            }

            # 检查解析器统计
            parser_stats = self.resource_parser.get_parsing_stats()
            if parser_stats['success_rate'] < 90:
                health_status['issues'].append(
                    f"解析器成功率过低: {parser_stats['success_rate']:.1f}%"
                )

            health_status['components']['resource_parser'] = {
                'status': 'healthy' if parser_stats['success_rate'] >= 90 else 'degraded',
                'stats': parser_stats
            }

            # 确定总体状态
            if health_status['issues']:
                health_status['status'] = 'degraded' if len(health_status['issues']) <= 2 else 'unhealthy'

            return health_status

        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'components': {},
                'issues': [f"健康检查失败: {e}"]
            }

    async def get_scan_history(
        self,
        cluster_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取扫描历史记录

        Args:
            cluster_name: 集群名称
            limit: 返回记录数限制

        Returns:
            扫描历史记录列表
        """
        try:
            # 从缓存元数据中获取扫描历史
            metadata_records = self.cache_manager.list_records(
                'cache_metadata',
                cluster_name=cluster_name,
                limit=limit
            )

            history = []
            for record in metadata_records:
                history.append({
                    'table_name': record.get('table_name'),
                    'scan_status': record.get('scan_status'),
                    'last_scan_at': record.get('last_scan_at'),
                    'next_scan_at': record.get('next_scan_at'),
                    'error_message': record.get('error_message')
                })

            return history

        except Exception as e:
            raise ScanError(f"获取扫描历史失败: {e}") from e

    async def cleanup_expired_cache(self) -> Dict[str, int]:
        """清理过期缓存数据

        Returns:
            清理统计信息
        """
        try:
            cleanup_stats = {
                'clusters': 0,
                'namespaces': 0,
                'nodes': 0,
                'pods': 0,
                'services': 0,
                'configmaps': 0,
                'secrets': 0,
                'total': 0
            }

            # 清理各类资源的过期缓存
            for table_name in cleanup_stats.keys():
                if table_name == 'total':
                    continue

                try:
                    cleaned = self.cache_manager.cleanup_expired_records(table_name)
                    cleanup_stats[table_name] = cleaned
                    cleanup_stats['total'] += cleaned
                except Exception as e:
                    print(f"警告: 清理{table_name}表失败: {e}")

            return cleanup_stats

        except Exception as e:
            raise ScanError(f"清理过期缓存失败: {e}") from e
