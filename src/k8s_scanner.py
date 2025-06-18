#!/usr/bin/env python3
"""
K8s集群扫描器 - 生产级应用程序
统一的入口点，包含工具发现和集群扫描功能
"""

import asyncio
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.cache.cache_manager import CacheManager
from src.scanner.tool_discovery import ToolDiscovery
from src.scanner.cluster_scan_app import ClusterScanApp
from src.scanner.real_cluster_scan_app import RealClusterScanApp


class K8sScanner:
    """K8s集群扫描器主应用"""
    
    def __init__(self, use_real_scanner=True):
        self.cache_manager = CacheManager()
        self.tool_discovery = ToolDiscovery(self.cache_manager)
        # 使用真实的扫描器，集成Gemini 2.5 Flash
        self.scan_app = RealClusterScanApp() if use_real_scanner else ClusterScanApp()
        self.use_real_scanner = use_real_scanner
    
    async def discover_tools(self) -> bool:
        """发现和缓存MCP工具"""
        print("🛠️ 开始MCP工具发现...")
        
        try:
            result = await self.tool_discovery.run_full_discovery()
            
            if result['success']:
                print(f"✅ 工具发现成功: {result['tools_discovered']} 个工具")
                return True
            else:
                print(f"❌ 工具发现失败: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ 工具发现异常: {e}")
            return False
    
    async def scan_cluster(self, cluster_name: str) -> bool:
        """扫描指定集群"""
        scanner_type = "真实扫描器(Gemini 2.5 Flash)" if self.use_real_scanner else "模拟扫描器"
        print(f"🔍 开始扫描集群: {cluster_name} (使用{scanner_type})")

        try:
            await self.scan_app.initialize()
            result = await self.scan_app.scan_full_cluster(cluster_name)

            if result['success']:
                print(f"✅ 集群扫描成功: {result['total_resources']} 个资源")
                return True
            else:
                print(f"❌ 集群扫描失败: {result.get('errors', [])}")
                return False

        except Exception as e:
            print(f"❌ 集群扫描异常: {e}")
            return False

    async def discover_clusters(self) -> bool:
        """发现所有可用集群"""
        if not self.use_real_scanner:
            print("⚠️ 集群发现功能需要使用真实扫描器")
            return False

        try:
            await self.scan_app.initialize()
            clusters = await self.scan_app.discover_all_clusters()

            if clusters:
                print(f"✅ 集群发现成功: {len(clusters)} 个集群")
                return True
            else:
                print("❌ 未发现任何集群")
                return False

        except Exception as e:
            print(f"❌ 集群发现异常: {e}")
            return False
    
    async def run_full_scan(self, cluster_name: str) -> bool:
        """执行完整的扫描流程：工具发现 + 集群扫描"""
        print("=" * 60)
        print("🚀 K8s集群扫描器 - 完整扫描流程")
        print("=" * 60)
        
        # 1. 检查工具是否已发现
        tools = self.cache_manager.list_records('mcp_tools')
        if not tools:
            print("📋 未发现缓存的MCP工具，开始工具发现...")
            if not await self.discover_tools():
                print("❌ 工具发现失败，无法继续扫描")
                return False
        else:
            print(f"📋 已发现 {len(tools)} 个缓存的MCP工具")
        
        # 2. 执行集群扫描
        success = await self.scan_cluster(cluster_name)
        
        if success:
            # 3. 显示扫描结果统计
            await self.show_scan_summary()
        
        return success
    
    async def show_scan_summary(self):
        """显示扫描结果摘要"""
        print("\n📊 扫描结果摘要:")
        
        try:
            # 查询各类资源数量
            clusters = self.cache_manager.list_records('clusters')
            namespaces = self.cache_manager.list_records('namespaces')
            nodes = self.cache_manager.list_records('nodes')
            pods = self.cache_manager.list_records('pods')
            services = self.cache_manager.list_records('services')
            tools = self.cache_manager.list_records('mcp_tools')
            
            print(f"   🏢 集群: {len(clusters)} 个")
            print(f"   📁 命名空间: {len(namespaces)} 个")
            print(f"   🖥️ 节点: {len(nodes)} 个")
            print(f"   🐳 Pod: {len(pods)} 个")
            print(f"   🌐 服务: {len(services)} 个")
            print(f"   🛠️ MCP工具: {len(tools)} 个")
            
            total_resources = len(clusters) + len(namespaces) + len(nodes) + len(pods) + len(services)
            print(f"   📦 总资源: {total_resources} 个")
            
            # 显示最新的集群信息
            if clusters:
                latest_cluster = clusters[0]
                print(f"\n🏢 最新集群信息:")
                print(f"   - 名称: {latest_cluster.name}")
                print(f"   - 版本: {latest_cluster.version}")
                print(f"   - 节点数: {latest_cluster.node_count}")
                print(f"   - API服务器: {latest_cluster.api_server}")
            
        except Exception as e:
            print(f"⚠️ 获取扫描摘要失败: {e}")
    
    async def list_cached_resources(self):
        """列出缓存的资源"""
        print("📋 缓存的资源列表:")
        
        try:
            # 列出集群
            clusters = self.cache_manager.list_records('clusters')
            if clusters:
                print(f"\n🏢 集群 ({len(clusters)} 个):")
                for cluster in clusters:
                    print(f"   - {cluster.name} (v{cluster.version})")
            
            # 列出命名空间
            namespaces = self.cache_manager.list_records('namespaces')
            if namespaces:
                print(f"\n📁 命名空间 ({len(namespaces)} 个):")
                for ns in namespaces[:10]:  # 只显示前10个
                    print(f"   - {ns.cluster_name}/{ns.name} ({ns.status})")
                if len(namespaces) > 10:
                    print(f"   ... 还有 {len(namespaces) - 10} 个")
            
            # 列出Pod
            pods = self.cache_manager.list_records('pods')
            if pods:
                print(f"\n🐳 Pod ({len(pods)} 个):")
                for pod in pods[:10]:  # 只显示前10个
                    print(f"   - {pod.cluster_name}/{pod.namespace}/{pod.name} ({pod.phase})")
                if len(pods) > 10:
                    print(f"   ... 还有 {len(pods) - 10} 个")
            
            # 列出服务
            services = self.cache_manager.list_records('services')
            if services:
                print(f"\n🌐 服务 ({len(services)} 个):")
                for service in services[:10]:  # 只显示前10个
                    print(f"   - {service.cluster_name}/{service.namespace}/{service.name} ({service.type})")
                if len(services) > 10:
                    print(f"   ... 还有 {len(services) - 10} 个")
            
        except Exception as e:
            print(f"❌ 列出资源失败: {e}")


async def main():
    """主函数"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='K8s集群扫描器')
    parser.add_argument('command', choices=['discover', 'scan', 'full-scan', 'list', 'discover-clusters'],
                       help='执行的命令')
    parser.add_argument('--cluster', '-c', default='default-cluster',
                       help='集群名称 (默认: default-cluster)')
    parser.add_argument('--use-mock', action='store_true',
                       help='使用模拟扫描器而不是真实扫描器')
    
    args = parser.parse_args()

    # 创建扫描器，默认使用真实扫描器
    use_real_scanner = not args.use_mock
    scanner = K8sScanner(use_real_scanner=use_real_scanner)

    if use_real_scanner:
        print("🤖 使用真实扫描器 (集成Gemini 2.5 Flash)")
    else:
        print("🎭 使用模拟扫描器")
    
    try:
        if args.command == 'discover':
            # 只执行工具发现
            success = await scanner.discover_tools()
            sys.exit(0 if success else 1)
            
        elif args.command == 'scan':
            # 只执行集群扫描
            success = await scanner.scan_cluster(args.cluster)
            sys.exit(0 if success else 1)
            
        elif args.command == 'full-scan':
            # 执行完整扫描流程
            success = await scanner.run_full_scan(args.cluster)
            sys.exit(0 if success else 1)
            
        elif args.command == 'list':
            # 列出缓存的资源
            await scanner.list_cached_resources()
            sys.exit(0)

        elif args.command == 'discover-clusters':
            # 发现所有可用集群
            success = await scanner.discover_clusters()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
