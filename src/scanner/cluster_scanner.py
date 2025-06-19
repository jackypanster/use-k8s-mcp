"""
集群扫描器
通过MCP工具调用获取K8s集群资源信息的核心功能
遵循单一职责原则，专注于资源数据获取
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from mcp_use import MCPClient, MCPAgent

from .exceptions import (
    ScanError, ClusterConnectionError, ToolNotFoundError, ScanTimeoutError
)
from src.fail_fast_exceptions import create_exception_context
from src.mcp_tools import MCPToolLoader
from src.llm_config import create_llm


class ClusterScanner:
    """集群扫描器 - 专注K8s资源数据获取"""
    
    # 静态资源扫描工具映射（修复后的正确工具名）
    STATIC_RESOURCE_TOOLS = {
        'cluster': 'GET_CLUSTER_INFO',
        'namespaces': 'LIST_NAMESPACES',
        'nodes': 'LIST_NODES'
    }

    # 动态资源扫描工具映射（使用LIST_CORE_RESOURCES）
    DYNAMIC_RESOURCE_TOOLS = {
        'pods': 'LIST_CORE_RESOURCES',
        'services': 'LIST_CORE_RESOURCES',
        'deployments': 'LIST_APPS_RESOURCES',
        'configmaps': 'LIST_CORE_RESOURCES',
        'secrets': 'LIST_CORE_RESOURCES'
    }
    
    def __init__(
        self,
        mcp_client: MCPClient,
        tool_loader: MCPToolLoader,
        timeout: int = 120,
        max_retries: int = 3
    ) -> None:
        """初始化集群扫描器

        Args:
            mcp_client: MCP客户端实例
            tool_loader: MCP工具加载器
            timeout: 扫描超时时间（秒）
            max_retries: 最大重试次数
        """
        self.mcp_client = mcp_client
        self.tool_loader = tool_loader
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建LLM和Agent（关键修复！）
        self.llm = create_llm()
        self.agent = MCPAgent(llm=self.llm, client=mcp_client, max_steps=30)

        # 统计信息
        self.scan_count = 0
        self.error_count = 0
        self.total_scan_time = 0.0
    
    async def scan_static_resources(
        self,
        cluster_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """扫描静态资源
        
        Args:
            cluster_name: 目标集群名称，None表示当前集群
            
        Returns:
            静态资源数据字典
            
        Raises:
            ScanError: 扫描失败时抛出
        """
        start_time = time.time()
        
        try:
            results = {}
            
            # 扫描集群信息
            results['cluster'] = await self._scan_cluster_info(cluster_name)
            
            # 扫描命名空间
            results['namespaces'] = await self._scan_namespaces(cluster_name)
            
            # 扫描节点
            results['nodes'] = await self._scan_nodes(cluster_name)
            
            self.scan_count += 1
            self.total_scan_time += time.time() - start_time
            
            return results
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="scan_static_resources",
                cluster_name=cluster_name,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ScanError(f"静态资源扫描失败: {e}", context) from e
    
    async def scan_dynamic_resources(
        self,
        cluster_name: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """扫描动态资源
        
        Args:
            cluster_name: 目标集群名称
            namespace: 目标命名空间，None表示所有命名空间
            
        Returns:
            动态资源数据字典
            
        Raises:
            ScanError: 扫描失败时抛出
        """
        start_time = time.time()
        
        try:
            results = {}
            
            # 扫描Pod
            results['pods'] = await self._scan_pods(cluster_name, namespace)
            
            # 扫描服务
            results['services'] = await self._scan_services(cluster_name, namespace)
            
            # 扫描部署
            results['deployments'] = await self._scan_deployments(cluster_name, namespace)

            # 扫描ConfigMap
            results['configmaps'] = await self._scan_configmaps(cluster_name, namespace)

            # 扫描Secret
            results['secrets'] = await self._scan_secrets(cluster_name, namespace)

            self.scan_count += 1
            self.total_scan_time += time.time() - start_time

            return results
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation="scan_dynamic_resources",
                cluster_name=cluster_name,
                namespace=namespace,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ScanError(f"动态资源扫描失败: {e}", context) from e
    
    async def _scan_cluster_info(self, cluster_name: Optional[str]) -> Dict[str, Any]:
        """扫描集群信息"""
        tool_name = self.STATIC_RESOURCE_TOOLS['cluster']
        params = {'cluster': cluster_name or 'default-cluster'}
        return await self._call_mcp_tool(tool_name, params)
    
    async def _scan_namespaces(self, cluster_name: Optional[str]) -> List[Dict[str, Any]]:
        """扫描命名空间"""
        tool_name = self.STATIC_RESOURCE_TOOLS['namespaces']
        params = {'cluster': cluster_name or 'default-cluster'}
        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []

    async def _scan_nodes(self, cluster_name: Optional[str]) -> List[Dict[str, Any]]:
        """扫描节点"""
        tool_name = self.STATIC_RESOURCE_TOOLS['nodes']
        params = {'cluster': cluster_name or 'default-cluster'}
        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []
    
    async def _scan_pods(
        self,
        cluster_name: Optional[str],
        namespace: Optional[str]
    ) -> List[Dict[str, Any]]:
        """扫描Pod"""
        tool_name = self.DYNAMIC_RESOURCE_TOOLS['pods']
        params = {
            'apiVersion': 'v1',
            'cluster': cluster_name or 'default-cluster',
            'kind': 'Pod'
        }
        if namespace:
            params['namespace'] = namespace

        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []
    
    async def _scan_services(
        self,
        cluster_name: Optional[str],
        namespace: Optional[str]
    ) -> List[Dict[str, Any]]:
        """扫描服务"""
        tool_name = self.DYNAMIC_RESOURCE_TOOLS['services']
        params = {
            'apiVersion': 'v1',
            'cluster': cluster_name or 'default-cluster',
            'kind': 'Service'
        }
        if namespace:
            params['namespace'] = namespace

        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []

    async def _scan_deployments(
        self,
        cluster_name: Optional[str],
        namespace: Optional[str]
    ) -> List[Dict[str, Any]]:
        """扫描部署"""
        tool_name = self.DYNAMIC_RESOURCE_TOOLS['deployments']
        params = {
            'apiVersion': 'apps/v1',
            'cluster': cluster_name or 'default-cluster',
            'kind': 'Deployment'
        }
        if namespace:
            params['namespace'] = namespace

        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []

    async def _scan_configmaps(
        self,
        cluster_name: Optional[str],
        namespace: Optional[str]
    ) -> List[Dict[str, Any]]:
        """扫描ConfigMap"""
        tool_name = self.DYNAMIC_RESOURCE_TOOLS['configmaps']
        params = {
            'apiVersion': 'v1',
            'cluster': cluster_name or 'default-cluster',
            'kind': 'ConfigMap'
        }
        if namespace:
            params['namespace'] = namespace

        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []

    async def _scan_secrets(
        self,
        cluster_name: Optional[str],
        namespace: Optional[str]
    ) -> List[Dict[str, Any]]:
        """扫描Secret"""
        tool_name = self.DYNAMIC_RESOURCE_TOOLS['secrets']
        params = {
            'apiVersion': 'v1',
            'cluster': cluster_name or 'default-cluster',
            'kind': 'Secret'
        }
        if namespace:
            params['namespace'] = namespace

        result = await self._call_mcp_tool(tool_name, params)
        return result.get('items', []) if isinstance(result, dict) else []

    async def _call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """调用MCP工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具调用结果

        Raises:
            ToolNotFoundError: 工具不存在
            ScanTimeoutError: 调用超时
            ClusterConnectionError: 集群连接失败
        """
        start_time = time.time()

        try:
            # 构建工具调用指令
            if params:
                param_str = " ".join([f"{k}={v}" for k, v in params.items()])
                instruction = f"使用 {tool_name} 工具，参数: {param_str}"
            else:
                instruction = f"使用 {tool_name} 工具获取K8s集群信息"

            # 通过Agent执行工具调用（关键修复！）
            from ..output_utils import request_log, response_log
            
            request_log("CLUSTER_SCANNER", f"执行工具调用", f"指令: {instruction}, max_steps: 30, timeout: {self.timeout}s")
            
            result = await asyncio.wait_for(
                self.agent.run(instruction, max_steps=30),
                timeout=self.timeout
            )
            
            response_log("CLUSTER_SCANNER", "工具调用完成", str(result))

            return result

        except asyncio.TimeoutError as e:
            context = create_exception_context(
                operation="call_mcp_tool",
                tool_name=tool_name,
                params=params,
                timeout=self.timeout,
                execution_time=time.time() - start_time
            )
            raise ScanTimeoutError(f"MCP工具调用超时: {tool_name}", context) from e

        except ConnectionError as e:
            context = create_exception_context(
                operation="call_mcp_tool",
                tool_name=tool_name,
                params=params,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ClusterConnectionError(f"集群连接失败: {e}", context) from e

        except Exception as e:
            context = create_exception_context(
                operation="call_mcp_tool",
                tool_name=tool_name,
                params=params,
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise ScanError(f"MCP工具调用失败: {e}", context) from e
    
    def get_scan_stats(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        avg_scan_time = (
            self.total_scan_time / max(1, self.scan_count)
        )
        
        return {
            'scan_count': self.scan_count,
            'error_count': self.error_count,
            'success_rate': (
                (self.scan_count - self.error_count) / max(1, self.scan_count)
            ) * 100,
            'avg_scan_time': avg_scan_time,
            'total_scan_time': self.total_scan_time
        }
