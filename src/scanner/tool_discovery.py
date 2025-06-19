"""
MCP工具发现和缓存模块
通过Agent调用大模型获取完整的K8s MCP工具列表并保存到数据库
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from mcp_use import MCPClient, MCPAgent

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.llm_config import create_llm
from src.cache.cache_manager import CacheManager
from src.cache.models import MCPToolInfo
from src.scanner.exceptions import ToolDiscoveryError


class ToolDiscovery:
    """MCP工具发现器 - 获取和缓存所有可用的K8s MCP工具"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.agent: Optional[MCPAgent] = None
        self.discovery_stats = {
            'tools_discovered': 0,
            'tools_cached': 0,
            'discovery_time': 0.0,
            'last_discovery': None
        }
    
    async def initialize_agent(self) -> None:
        """初始化MCP Agent"""
        try:
            # 验证环境配置
            required_vars = ["MCP_SERVER_URL", "MCP_SERVER_TYPE", "MCP_SERVER_NAME"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ToolDiscoveryError(
                    f"缺少必需的MCP配置环境变量: {', '.join(missing_vars)}"
                )
            
            # 创建MCP客户端
            config = {
                "mcpServers": {
                    os.getenv("MCP_SERVER_NAME"): {
                        "type": os.getenv("MCP_SERVER_TYPE"),
                        "url": os.getenv("MCP_SERVER_URL")
                    }
                }
            }
            
            mcp_client = MCPClient.from_dict(config)
            
            # 创建Agent
            self.agent = MCPAgent(
                llm=create_llm(),
                client=mcp_client,
                max_steps=30
            )
            
        except Exception as e:
            raise ToolDiscoveryError(f"Agent初始化失败: {e}") from e
    
    async def discover_all_tools(self) -> List[Dict[str, Any]]:
        """发现所有可用的MCP工具"""
        if not self.agent:
            await self.initialize_agent()
        
        start_time = datetime.utcnow()
        
        try:
            # 使用Agent获取工具列表
            result = await self.agent.run(
                "请列出所有可用的K8s MCP工具，包括每个工具的名称、描述、输入参数、输出格式等详细信息。"
                "请以结构化的JSON格式返回，包含以下字段：name, description, input_schema, output_schema, "
                "resource_types, operation_types, required_params, optional_params。",
                max_steps=30
            )
            
            # 解析Agent返回的结果
            tools = self._parse_tool_discovery_result(result)
            
            # 更新统计信息
            self.discovery_stats['tools_discovered'] = len(tools)
            self.discovery_stats['discovery_time'] = (datetime.utcnow() - start_time).total_seconds()
            self.discovery_stats['last_discovery'] = datetime.utcnow()
            
            return tools
            
        except Exception as e:
            raise ToolDiscoveryError(f"工具发现失败: {e}") from e
    
    def _parse_tool_discovery_result(self, result: str) -> List[Dict[str, Any]]:
        """解析工具发现结果"""
        tools = []
        
        try:
            # 尝试直接解析JSON
            if result.strip().startswith('[') or result.strip().startswith('{'):
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    tools = parsed
                elif isinstance(parsed, dict) and 'tools' in parsed:
                    tools = parsed['tools']
                else:
                    tools = [parsed]
            else:
                # 从文本中提取工具信息
                tools = self._extract_tools_from_text(result)
            
            # 验证和标准化工具信息
            validated_tools = []
            for tool in tools:
                validated_tool = self._validate_and_normalize_tool(tool)
                if validated_tool:
                    validated_tools.append(validated_tool)
            
            return validated_tools
            
        except Exception as e:
            raise ToolDiscoveryError(f"工具结果解析失败: {e}") from e
    
    def _extract_tools_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取工具信息"""
        tools = []
        
        # 基于已知的工具模式提取
        known_tool_patterns = [
            'GET_CLUSTER_INFO', 'LIST_NAMESPACES', 'LIST_NODES', 'LIST_CORE_RESOURCES',
            'LIST_APPS_RESOURCES', 'LIST_BATCH_RESOURCES', 'LIST_NETWORKING_RESOURCES',
            'LIST_STORAGE_RESOURCES', 'LIST_RBAC_RESOURCES', 'LIST_POLICY_RESOURCES',
            'DESCRIBE_CLUSTER', 'DESCRIBE_CORE_RESOURCE', 'DESCRIBE_APPS_RESOURCE',
            'GET_POD_LOGS', 'GET_EVENTS', 'SEARCH_RESOURCES', 'VALIDATE_MANIFEST'
        ]
        
        for tool_name in known_tool_patterns:
            if tool_name in text:
                tool_info = {
                    'name': tool_name,
                    'description': self._extract_tool_description(text, tool_name),
                    'resource_types': self._infer_resource_types(tool_name),
                    'operation_types': self._infer_operation_types(tool_name),
                    'required_params': self._infer_required_params(tool_name),
                    'optional_params': self._infer_optional_params(tool_name)
                }
                tools.append(tool_info)
        
        return tools
    
    def _extract_tool_description(self, text: str, tool_name: str) -> str:
        """提取工具描述"""
        # 简单的描述映射
        descriptions = {
            'GET_CLUSTER_INFO': '获取Kubernetes集群信息',
            'LIST_NAMESPACES': '列出所有命名空间',
            'LIST_NODES': '列出所有节点',
            'LIST_CORE_RESOURCES': '列出核心资源',
            'LIST_APPS_RESOURCES': '列出应用资源',
            'LIST_BATCH_RESOURCES': '列出批处理资源',
            'LIST_NETWORKING_RESOURCES': '列出网络资源',
            'LIST_STORAGE_RESOURCES': '列出存储资源',
            'LIST_RBAC_RESOURCES': '列出RBAC资源',
            'LIST_POLICY_RESOURCES': '列出策略资源',
            'DESCRIBE_CLUSTER': '描述集群',
            'DESCRIBE_CORE_RESOURCE': '描述核心资源',
            'DESCRIBE_APPS_RESOURCE': '描述应用资源',
            'GET_POD_LOGS': '获取Pod日志',
            'GET_EVENTS': '获取资源事件',
            'SEARCH_RESOURCES': '搜索资源',
            'VALIDATE_MANIFEST': '验证Kubernetes清单'
        }
        return descriptions.get(tool_name, f'{tool_name}工具')
    
    def _infer_resource_types(self, tool_name: str) -> List[str]:
        """推断工具支持的资源类型"""
        if 'CORE' in tool_name:
            return ['Pod', 'Service', 'ConfigMap', 'Secret', 'PersistentVolume']
        elif 'APPS' in tool_name:
            return ['Deployment', 'ReplicaSet', 'DaemonSet', 'StatefulSet']
        elif 'BATCH' in tool_name:
            return ['Job', 'CronJob']
        elif 'NETWORKING' in tool_name:
            return ['NetworkPolicy', 'Ingress']
        elif 'STORAGE' in tool_name:
            return ['StorageClass', 'PersistentVolumeClaim']
        elif 'RBAC' in tool_name:
            return ['Role', 'RoleBinding', 'ClusterRole', 'ClusterRoleBinding']
        elif 'POLICY' in tool_name:
            return ['PodSecurityPolicy', 'NetworkPolicy']
        elif 'CLUSTER' in tool_name:
            return ['Cluster']
        elif 'NAMESPACE' in tool_name:
            return ['Namespace']
        elif 'NODE' in tool_name:
            return ['Node']
        else:
            return ['All']
    
    def _infer_operation_types(self, tool_name: str) -> List[str]:
        """推断工具支持的操作类型"""
        if tool_name.startswith('LIST_'):
            return ['list']
        elif tool_name.startswith('GET_'):
            return ['get']
        elif tool_name.startswith('DESCRIBE_'):
            return ['describe']
        elif tool_name.startswith('SEARCH_'):
            return ['search']
        elif tool_name.startswith('VALIDATE_'):
            return ['validate']
        else:
            return ['unknown']
    
    def _infer_required_params(self, tool_name: str) -> List[str]:
        """推断工具的必需参数"""
        base_params = ['cluster']
        
        if 'CORE' in tool_name or 'APPS' in tool_name or 'BATCH' in tool_name:
            base_params.extend(['apiVersion', 'kind'])
        
        return base_params
    
    def _infer_optional_params(self, tool_name: str) -> List[str]:
        """推断工具的可选参数"""
        return ['namespace', 'labelSelector', 'fieldSelector', 'limit']
    
    def _validate_and_normalize_tool(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证和标准化工具信息"""
        if not isinstance(tool, dict) or 'name' not in tool:
            return None
        
        normalized = {
            'name': tool['name'],
            'description': tool.get('description', ''),
            'input_schema': tool.get('input_schema'),
            'output_schema': tool.get('output_schema'),
            'resource_types': tool.get('resource_types', []),
            'operation_types': tool.get('operation_types', []),
            'required_params': tool.get('required_params', []),
            'optional_params': tool.get('optional_params', [])
        }
        
        return normalized
    
    async def cache_discovered_tools(self, tools: List[Dict[str, Any]]) -> int:
        """将发现的工具缓存到数据库"""
        cached_count = 0
        
        try:
            for tool_data in tools:
                # 创建MCPToolInfo实例
                tool_info = MCPToolInfo(
                    name=tool_data['name'],
                    description=tool_data.get('description'),
                    input_schema=tool_data.get('input_schema'),
                    output_schema=tool_data.get('output_schema'),
                    resource_types=tool_data.get('resource_types'),
                    operation_types=tool_data.get('operation_types'),
                    required_params=tool_data.get('required_params'),
                    optional_params=tool_data.get('optional_params')
                )
                
                # 保存到缓存
                try:
                    self.cache_manager.create_record('mcp_tools', tool_info)
                    cached_count += 1
                except Exception as e:
                    # 如果工具已存在，尝试更新
                    try:
                        existing_tools = self.cache_manager.query_records(
                            'mcp_tools', 
                            {'name': tool_data['name']}
                        )
                        if existing_tools:
                            tool_info.id = existing_tools[0].id
                            self.cache_manager.update_record('mcp_tools', tool_info)
                            cached_count += 1
                    except Exception:
                        # 忽略无法缓存的工具
                        pass
            
            self.discovery_stats['tools_cached'] = cached_count
            return cached_count
            
        except Exception as e:
            raise ToolDiscoveryError(f"工具缓存失败: {e}") from e
    
    async def run_full_discovery(self) -> Dict[str, Any]:
        """执行完整的工具发现和缓存流程"""
        try:
            print("🔍 开始MCP工具发现...")
            
            # 发现工具
            tools = await self.discover_all_tools()
            print(f"✅ 发现 {len(tools)} 个MCP工具")
            
            # 缓存工具
            cached_count = await self.cache_discovered_tools(tools)
            print(f"✅ 成功缓存 {cached_count} 个工具")
            
            return {
                'success': True,
                'tools_discovered': len(tools),
                'tools_cached': cached_count,
                'discovery_time': self.discovery_stats['discovery_time'],
                'tools': tools
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tools_discovered': 0,
                'tools_cached': 0
            }
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """获取发现统计信息"""
        return self.discovery_stats.copy()


async def main():
    """主函数 - 执行工具发现"""
    load_dotenv()
    
    print("=" * 60)
    print("🛠️ K8s MCP工具发现和缓存系统")
    print("=" * 60)
    
    try:
        # 初始化缓存管理器
        cache_manager = CacheManager()
        
        # 创建工具发现器
        discovery = ToolDiscovery(cache_manager)
        
        # 执行完整发现流程
        result = await discovery.run_full_discovery()
        
        if result['success']:
            print(f"\n📊 发现结果:")
            print(f"   - 发现工具: {result['tools_discovered']} 个")
            print(f"   - 缓存工具: {result['tools_cached']} 个")
            print(f"   - 发现耗时: {result['discovery_time']:.2f} 秒")
            
            # 显示工具列表
            print(f"\n🛠️ 发现的工具:")
            for tool in result['tools'][:10]:  # 只显示前10个
                print(f"   - {tool['name']}: {tool['description']}")
            
            if len(result['tools']) > 10:
                print(f"   ... 还有 {len(result['tools']) - 10} 个工具")
        else:
            print(f"❌ 工具发现失败: {result['error']}")
        
        print("\n" + "=" * 60)
        print("✅ 工具发现完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
