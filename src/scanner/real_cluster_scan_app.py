"""
真实K8s集群扫描应用程序
集成Gemini 2.5 Flash大模型，处理真实的集群数据
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.llm_config import create_llm
from src.cache.cache_manager import CacheManager
from src.cache.models import ClusterInfo, NamespaceInfo, NodeInfo, PodInfo, ServiceInfo
from src.scanner.exceptions import ScanError, ToolNotFoundError
from mcp_use import MCPClient, MCPAgent


class RealClusterScanApp:
    """真实K8s集群扫描应用程序 - 集成Gemini 2.5 Flash"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.agent: Optional[MCPAgent] = None
        self.available_tools: Dict[str, Any] = {}
        self.scan_stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'last_scan_time': None,
            'total_resources_scanned': 0,
            'clusters_discovered': 0
        }
    
    async def initialize(self) -> None:
        """初始化扫描应用"""
        try:
            print("🔧 初始化真实K8s集群扫描应用...")
            print("🤖 集成Gemini 2.5 Flash大模型...")
            
            # 验证环境配置
            self._validate_environment()
            
            # 初始化MCP Agent (使用Gemini 2.5 Flash)
            await self._initialize_agent()
            
            # 加载可用工具
            await self._load_available_tools()
            
            print("✅ 真实扫描应用初始化完成")
            
        except Exception as e:
            raise ScanError(f"真实扫描应用初始化失败: {e}") from e
    
    def _validate_environment(self) -> None:
        """验证环境配置"""
        required_vars = ["MCP_SERVER_URL", "MCP_SERVER_TYPE", "MCP_SERVER_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ScanError(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        
        # 验证LLM配置
        llm_vars = ["OPENROUTER_API_KEY", "LLM_MODEL_NAME"]
        missing_llm_vars = [var for var in llm_vars if not os.getenv(var)]
        
        if missing_llm_vars:
            raise ScanError(f"缺少LLM配置环境变量: {', '.join(missing_llm_vars)}")
    
    async def _initialize_agent(self) -> None:
        """初始化MCP Agent (使用Gemini 2.5 Flash)"""
        try:
            config = {
                "mcpServers": {
                    os.getenv("MCP_SERVER_NAME"): {
                        "type": os.getenv("MCP_SERVER_TYPE"),
                        "url": os.getenv("MCP_SERVER_URL")
                    }
                }
            }
            
            mcp_client = MCPClient.from_dict(config)
            
            # 使用Gemini 2.5 Flash
            llm = create_llm()
            print(f"🤖 使用模型: {os.getenv('LLM_MODEL_NAME', 'google/gemini-2.5-flash')}")
            
            self.agent = MCPAgent(
                llm=llm,
                client=mcp_client,
                max_steps=15  # 增加步数以处理复杂的真实数据
            )
            
        except Exception as e:
            raise ScanError(f"MCP Agent初始化失败: {e}") from e
    
    async def _load_available_tools(self) -> None:
        """从数据库加载可用工具"""
        try:
            tools = self.cache_manager.list_records('mcp_tools')
            self.available_tools = {tool.name: tool for tool in tools}
            print(f"📋 加载了 {len(self.available_tools)} 个可用工具")
            
        except Exception as e:
            raise ScanError(f"工具加载失败: {e}") from e
    
    async def discover_all_clusters(self) -> List[Dict[str, Any]]:
        """发现所有可用的集群"""
        if 'GET_CLUSTER_INFO' not in self.available_tools:
            raise ToolNotFoundError("GET_CLUSTER_INFO工具不可用")
        
        try:
            print("🔍 发现所有可用集群...")
            
            result = await self.agent.run(
                "使用 GET_CLUSTER_INFO 工具获取所有可用的Kubernetes集群信息，"
                "包括集群名称、描述、端点、版本和状态。请返回详细的集群列表。",
                max_steps=5
            )
            
            # 解析集群列表
            clusters = self._parse_cluster_list(result)
            
            print(f"✅ 发现 {len(clusters)} 个集群")
            for cluster in clusters:
                status_icon = "✅" if cluster.get('status') == 'Available' else "❌"
                print(f"   {status_icon} {cluster['name']}: {cluster.get('description', 'N/A')}")
            
            self.scan_stats['clusters_discovered'] = len(clusters)
            return clusters
            
        except Exception as e:
            print(f"❌ 集群发现失败: {e}")
            return []
    
    def _parse_cluster_list(self, result: str) -> List[Dict[str, Any]]:
        """解析集群列表信息"""
        clusters = []

        try:
            # 尝试从结果中提取集群信息
            lines = result.split('\n')
            current_cluster = {}

            for line in lines:
                line = line.strip()
                if not line:  # 跳过空行
                    continue

                # 匹配集群名称 (通常以**开头)
                cluster_name_match = re.search(r'\*\*([^*]+)\*\*', line)
                if cluster_name_match:
                    # 保存前一个集群
                    if current_cluster and 'name' in current_cluster:
                        clusters.append(current_cluster)
                    current_cluster = {'name': cluster_name_match.group(1).strip()}
                    continue

                # 只有在有当前集群的情况下才解析属性
                if not current_cluster:
                    continue

                # 匹配描述
                if 'Description:' in line:
                    desc_match = re.search(r'Description:\s*(.+)', line)
                    if desc_match:
                        current_cluster['description'] = desc_match.group(1).strip()

                # 匹配端点
                elif 'Endpoint:' in line:
                    endpoint_match = re.search(r'Endpoint:\s*(.+)', line)
                    if endpoint_match:
                        current_cluster['endpoint'] = endpoint_match.group(1).strip()

                # 匹配版本
                elif 'Version:' in line:
                    version_match = re.search(r'Version:\s*(.+)', line)
                    if version_match:
                        current_cluster['version'] = version_match.group(1).strip()

                # 匹配状态
                elif 'Status:' in line:
                    status_match = re.search(r'Status:\s*(.+)', line)
                    if status_match:
                        current_cluster['status'] = status_match.group(1).strip()

            # 添加最后一个集群
            if current_cluster and 'name' in current_cluster:
                clusters.append(current_cluster)

            # 过滤掉无效的集群
            valid_clusters = []
            for cluster in clusters:
                if cluster.get('name') and len(cluster.get('name', '')) > 1:
                    valid_clusters.append(cluster)

            return valid_clusters

        except Exception as e:
            print(f"⚠️ 集群列表解析失败: {e}")
            return []
    
    async def scan_cluster_info(self, cluster_name: str) -> Optional[ClusterInfo]:
        """扫描指定集群的详细信息"""
        try:
            print(f"🔍 扫描集群信息: {cluster_name}")
            
            result = await self.agent.run(
                f"使用 GET_CLUSTER_INFO 工具获取集群 {cluster_name} 的详细信息，"
                f"包括版本、端点、状态等。",
                max_steps=3
            )
            
            # 使用Gemini解析真实结果
            cluster_info = await self._parse_real_cluster_info(result, cluster_name)
            
            if cluster_info:
                # 保存到缓存
                self.cache_manager.create_record('clusters', cluster_info)
                print(f"✅ 集群信息已缓存: {cluster_info.name}")
                
            return cluster_info
            
        except Exception as e:
            print(f"❌ 集群信息扫描失败: {e}")
            return None
    
    async def _parse_real_cluster_info(self, result: str, cluster_name: str) -> Optional[ClusterInfo]:
        """使用Gemini解析真实的集群信息"""
        try:
            # 使用Gemini解析结构化数据
            parse_result = await self.agent.run(
                f"请从以下文本中提取集群 {cluster_name} 的信息，并以JSON格式返回：\n"
                f"需要提取的字段：name, version, endpoint, status, description\n\n"
                f"原始文本：\n{result}\n\n"
                f"请返回格式：{{'name': '...', 'version': '...', 'endpoint': '...', 'status': '...', 'description': '...'}}",
                max_steps=2
            )
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{[^}]+\}', parse_result)
                if json_match:
                    cluster_data = json.loads(json_match.group())
                else:
                    # 如果没有找到JSON，使用正则表达式提取
                    cluster_data = self._extract_cluster_data_regex(result, cluster_name)
            except json.JSONDecodeError:
                cluster_data = self._extract_cluster_data_regex(result, cluster_name)
            
            if cluster_data:
                # 确保api_server字段不为空
                api_server = cluster_data.get('endpoint') or cluster_data.get('api_server') or f'https://{cluster_name}:6443'

                return ClusterInfo(
                    name=cluster_data.get('name', cluster_name),
                    version=cluster_data.get('version', 'unknown'),
                    api_server=api_server,
                    node_count=0,  # 需要单独查询
                    ttl_expires_at=datetime.utcnow() + timedelta(minutes=30)
                )
            
            return None
            
        except Exception as e:
            print(f"⚠️ 集群信息解析失败: {e}")
            return None
    
    def _extract_cluster_data_regex(self, result: str, cluster_name: str) -> Dict[str, str]:
        """使用正则表达式提取集群数据"""
        cluster_data = {'name': cluster_name}
        
        # 提取版本
        version_match = re.search(r'Version:\s*([^\n\r]+)', result)
        if version_match:
            cluster_data['version'] = version_match.group(1).strip()
        
        # 提取端点
        endpoint_match = re.search(r'Endpoint:\s*([^\n\r]+)', result)
        if endpoint_match:
            cluster_data['endpoint'] = endpoint_match.group(1).strip()
        
        # 提取状态
        status_match = re.search(r'Status:\s*([^\n\r]+)', result)
        if status_match:
            cluster_data['status'] = status_match.group(1).strip()
        
        # 提取描述
        desc_match = re.search(r'Description:\s*([^\n\r]+)', result)
        if desc_match:
            cluster_data['description'] = desc_match.group(1).strip()
        
        return cluster_data
    
    async def scan_namespaces(self, cluster_name: str) -> List[NamespaceInfo]:
        """扫描指定集群的命名空间"""
        if 'LIST_NAMESPACES' not in self.available_tools:
            raise ToolNotFoundError("LIST_NAMESPACES工具不可用")
        
        try:
            print(f"🔍 扫描命名空间: {cluster_name}")
            
            result = await self.agent.run(
                f"使用 LIST_NAMESPACES 工具列出集群 {cluster_name} 的所有命名空间，"
                f"包括命名空间名称、状态、标签等信息。",
                max_steps=3
            )
            
            # 使用Gemini解析真实结果
            namespaces = await self._parse_real_namespaces(result, cluster_name)
            
            # 批量保存到缓存
            for ns in namespaces:
                self.cache_manager.create_record('namespaces', ns)
            
            print(f"✅ 命名空间已缓存: {len(namespaces)} 个")
            return namespaces
            
        except Exception as e:
            print(f"❌ 命名空间扫描失败: {e}")
            return []
    
    async def _parse_real_namespaces(self, result: str, cluster_name: str) -> List[NamespaceInfo]:
        """使用Gemini解析真实的命名空间信息"""
        try:
            # 使用Gemini提取命名空间列表
            parse_result = await self.agent.run(
                f"请从以下文本中提取所有命名空间的信息，每个命名空间包含name和status字段，"
                f"以JSON数组格式返回：[{{'name': '...', 'status': '...'}}]\n\n"
                f"原始文本：\n{result}",
                max_steps=2
            )
            
            namespaces = []
            
            try:
                # 尝试解析JSON
                json_match = re.search(r'\[.*\]', parse_result, re.DOTALL)
                if json_match:
                    ns_data_list = json.loads(json_match.group())
                    for ns_data in ns_data_list:
                        ns_info = NamespaceInfo(
                            cluster_name=cluster_name,
                            name=ns_data.get('name', ''),
                            status=ns_data.get('status', 'Active'),
                            labels={},
                            annotations={},
                            ttl_expires_at=datetime.utcnow() + timedelta(minutes=30)
                        )
                        namespaces.append(ns_info)
            except (json.JSONDecodeError, KeyError):
                # 如果JSON解析失败，使用正则表达式
                ns_names = re.findall(r'(\w+(?:-\w+)*)', result)
                for ns_name in set(ns_names):  # 去重
                    if len(ns_name) > 2:  # 过滤太短的匹配
                        ns_info = NamespaceInfo(
                            cluster_name=cluster_name,
                            name=ns_name,
                            status='Active',
                            labels={},
                            annotations={},
                            ttl_expires_at=datetime.utcnow() + timedelta(minutes=30)
                        )
                        namespaces.append(ns_info)
            
            return namespaces
            
        except Exception as e:
            print(f"⚠️ 命名空间解析失败: {e}")
            return []
    
    async def scan_full_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """执行完整的真实集群扫描"""
        start_time = datetime.utcnow()
        scan_result = {
            'cluster_name': cluster_name,
            'scan_start_time': start_time,
            'success': False,
            'resources': {},
            'errors': []
        }
        
        try:
            print(f"\n🚀 开始真实集群扫描: {cluster_name}")
            print("🤖 使用Gemini 2.5 Flash处理真实数据")
            print("=" * 50)
            
            # 扫描集群信息
            print("📊 扫描集群信息...")
            cluster_info = await self.scan_cluster_info(cluster_name)
            
            # 扫描命名空间
            print("📁 扫描命名空间...")
            namespaces = await self.scan_namespaces(cluster_name)
            
            # 汇总结果
            scan_result['resources'] = {
                'cluster': cluster_info,
                'namespaces': namespaces,
                'nodes': [],  # 可以扩展
                'pods': [],   # 可以扩展
                'services': [] # 可以扩展
            }
            
            # 更新统计信息
            total_resources = len(namespaces)
            if cluster_info:
                total_resources += 1
            
            scan_result['success'] = True
            scan_result['total_resources'] = total_resources
            scan_result['scan_duration'] = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新扫描统计
            self.scan_stats['total_scans'] += 1
            self.scan_stats['successful_scans'] += 1
            self.scan_stats['last_scan_time'] = datetime.utcnow()
            self.scan_stats['total_resources_scanned'] += total_resources
            
            print(f"\n✅ 真实集群扫描完成!")
            print(f"📊 扫描统计:")
            print(f"   - 集群: {1 if cluster_info else 0}")
            print(f"   - 命名空间: {len(namespaces)}")
            print(f"   - 总资源: {total_resources}")
            print(f"   - 扫描耗时: {scan_result['scan_duration']:.2f} 秒")
            
            return scan_result
            
        except Exception as e:
            scan_result['errors'].append(str(e))
            self.scan_stats['total_scans'] += 1
            self.scan_stats['failed_scans'] += 1
            print(f"❌ 真实集群扫描失败: {e}")
            return scan_result
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        return self.scan_stats.copy()


async def main():
    """主函数 - 测试真实集群扫描"""
    load_dotenv()
    
    print("=" * 60)
    print("🔍 真实K8s集群扫描应用程序 (Gemini 2.5 Flash)")
    print("=" * 60)
    
    try:
        # 创建并初始化真实扫描应用
        app = RealClusterScanApp()
        await app.initialize()
        
        # 发现所有集群
        clusters = await app.discover_all_clusters()
        
        if clusters:
            # 扫描第一个可用的集群
            available_clusters = [c for c in clusters if c.get('status') == 'Available']
            if available_clusters:
                test_cluster = available_clusters[0]['name']
                print(f"\n🎯 测试扫描集群: {test_cluster}")
                result = await app.scan_full_cluster(test_cluster)
            else:
                print("⚠️ 没有可用的集群进行扫描")
        
        # 显示最终统计
        stats = app.get_scan_statistics()
        print(f"\n📈 应用统计:")
        print(f"   - 发现集群: {stats['clusters_discovered']}")
        print(f"   - 总扫描次数: {stats['total_scans']}")
        print(f"   - 成功扫描: {stats['successful_scans']}")
        print(f"   - 失败扫描: {stats['failed_scans']}")
        print(f"   - 总资源数: {stats['total_resources_scanned']}")
        
        print("\n" + "=" * 60)
        print("✅ 真实扫描应用程序执行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 应用程序错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
