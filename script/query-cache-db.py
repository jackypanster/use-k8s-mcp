#!/usr/bin/env python3
"""
K8s缓存数据库查询脚本
快速查看缓存数据库中的内容
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def format_json_field(json_str):
    """格式化JSON字段显示"""
    if not json_str:
        return "无"
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and len(data) <= 3:
            return ", ".join([f"{k}:{v}" for k, v in data.items()])
        elif isinstance(data, list) and len(data) <= 3:
            return ", ".join(str(item) for item in data)
        else:
            return f"({len(data)} 项)" if isinstance(data, (dict, list)) else str(data)[:50]
    except:
        return str(json_str)[:50]

def query_clusters(cursor):
    """查询集群信息"""
    print("🏢 集群信息:")
    cursor.execute("""
        SELECT name, version, api_server, node_count, 
               created_at, ttl_expires_at
        FROM clusters 
        ORDER BY created_at DESC
    """)
    
    clusters = cursor.fetchall()
    if not clusters:
        print("   无集群数据")
        return
    
    for cluster in clusters:
        expired = datetime.fromisoformat(cluster['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
        status = "⚠️过期" if expired else "✅有效"
        print(f"   - {cluster['name']}: v{cluster['version']} ({cluster['node_count']} 节点) {status}")
        print(f"     API服务器: {cluster['api_server']}")
        print(f"     创建时间: {cluster['created_at']}")

def query_namespaces(cursor):
    """查询命名空间信息"""
    print("\n📁 命名空间信息:")
    cursor.execute("""
        SELECT cluster_name, name, status, labels,
               created_at, ttl_expires_at
        FROM namespaces 
        ORDER BY cluster_name, name
        LIMIT 10
    """)
    
    namespaces = cursor.fetchall()
    if not namespaces:
        print("   无命名空间数据")
        return
    
    for ns in namespaces:
        expired = datetime.fromisoformat(ns['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
        status_icon = "⚠️" if expired else "✅"
        labels = format_json_field(ns['labels'])
        print(f"   {status_icon} {ns['cluster_name']}/{ns['name']}: {ns['status']}")
        print(f"     标签: {labels}")

def query_nodes(cursor):
    """查询节点信息"""
    print("\n🖥️  节点信息:")
    cursor.execute("""
        SELECT cluster_name, name, status, roles, capacity,
               created_at, ttl_expires_at
        FROM nodes 
        ORDER BY cluster_name, name
        LIMIT 10
    """)
    
    nodes = cursor.fetchall()
    if not nodes:
        print("   无节点数据")
        return
    
    for node in nodes:
        expired = datetime.fromisoformat(node['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
        status_icon = "⚠️" if expired else "✅"
        roles = format_json_field(node['roles'])
        capacity = format_json_field(node['capacity'])
        print(f"   {status_icon} {node['cluster_name']}/{node['name']}: {node['status']}")
        print(f"     角色: {roles}")
        print(f"     容量: {capacity}")

def query_pods(cursor):
    """查询Pod信息"""
    print("\n🐳 Pod信息:")

    # 首先检查表结构
    try:
        cursor.execute("PRAGMA table_info(pods)")
        columns = [row[1] for row in cursor.fetchall()]

        # 根据实际存在的列构建查询
        base_columns = ['cluster_name', 'namespace', 'name', 'phase', 'node_name', 'created_at', 'ttl_expires_at']
        available_columns = [col for col in base_columns if col in columns]

        if 'restart_count' in columns:
            available_columns.insert(-2, 'restart_count')  # 在created_at之前插入

        query = f"""
            SELECT {', '.join(available_columns)}
            FROM pods
            ORDER BY created_at DESC
            LIMIT 15
        """
        cursor.execute(query)
    except Exception as e:
        print(f"   ❌ 查询Pod信息失败: {e}")
        return
    
    pods = cursor.fetchall()
    if not pods:
        print("   无Pod数据")
        return

    for pod in pods:
        try:
            expired = datetime.fromisoformat(pod['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
        except:
            expired = False

        status_icon = "⚠️" if expired else "✅"
        phase_icon = {
            'Running': '🟢',
            'Pending': '🟡',
            'Failed': '🔴',
            'Succeeded': '✅',
            'Unknown': '❓'
        }.get(pod.get('phase', 'Unknown'), '❓')

        restart_info = f" | 重启: {pod['restart_count']}" if 'restart_count' in pod.keys() else ""

        print(f"   {status_icon} {pod['cluster_name']}/{pod['namespace']}/{pod['name']}")
        print(f"     {phase_icon} {pod.get('phase', 'Unknown')} | 节点: {pod.get('node_name', 'Unknown')}{restart_info}")

def query_services(cursor):
    """查询服务信息"""
    print("\n🌐 服务信息:")
    cursor.execute("""
        SELECT cluster_name, namespace, name, type, cluster_ip,
               external_ip, created_at, ttl_expires_at
        FROM services 
        ORDER BY cluster_name, namespace, name
        LIMIT 10
    """)
    
    services = cursor.fetchall()
    if not services:
        print("   无服务数据")
        return
    
    for svc in services:
        expired = datetime.fromisoformat(svc['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
        status_icon = "⚠️" if expired else "✅"
        external = f" | 外部IP: {svc['external_ip']}" if svc['external_ip'] else ""
        print(f"   {status_icon} {svc['cluster_name']}/{svc['namespace']}/{svc['name']}")
        print(f"     类型: {svc['type']} | 集群IP: {svc['cluster_ip']}{external}")

def query_cache_metadata(cursor):
    """查询缓存元数据"""
    print("\n📊 缓存元数据:")

    # 检查表结构
    try:
        cursor.execute("PRAGMA table_info(cache_metadata)")
        columns = [row[1] for row in cursor.fetchall()]

        base_columns = ['table_name', 'cluster_name', 'scan_status', 'record_count',
                       'last_scan_at', 'next_scan_at', 'error_message']
        available_columns = [col for col in base_columns if col in columns]

        if 'scan_duration_ms' in columns:
            available_columns.append('scan_duration_ms')

        query = f"""
            SELECT {', '.join(available_columns)}
            FROM cache_metadata
            ORDER BY last_scan_at DESC
        """
        cursor.execute(query)
    except Exception as e:
        print(f"   ❌ 查询缓存元数据失败: {e}")
        return
    
    metadata = cursor.fetchall()
    if not metadata:
        print("   无缓存元数据")
        return
    
    for meta in metadata:
        status_icon = {
            'completed': '✅',
            'running': '🔄',
            'failed': '❌',
            'pending': '⏳'
        }.get(meta['scan_status'], '❓')
        
        print(f"   {status_icon} {meta['table_name']} ({meta['cluster_name']})")
        print(f"     状态: {meta['scan_status']} | 记录数: {meta['record_count']}")
        print(f"     最后扫描: {meta['last_scan_at']}")
        if meta.get('next_scan_at'):
            print(f"     下次扫描: {meta['next_scan_at']}")
        if meta.get('error_message'):
            print(f"     错误: {meta['error_message']}")
        if 'scan_duration_ms' in meta.keys() and meta['scan_duration_ms']:
            print(f"     耗时: {meta['scan_duration_ms']}ms")

def query_mcp_tools(cursor):
    """查询MCP工具信息"""
    print("\n🛠️  MCP工具:")

    # 检查表结构
    try:
        cursor.execute("PRAGMA table_info(mcp_tools)")
        columns = [row[1] for row in cursor.fetchall()]

        base_columns = ['name', 'description', 'resource_types', 'operation_types', 'created_at']
        available_columns = [col for col in base_columns if col in columns]

        if 'ttl_expires_at' in columns:
            available_columns.append('ttl_expires_at')

        query = f"""
            SELECT {', '.join(available_columns)}
            FROM mcp_tools
            ORDER BY name
            LIMIT 10
        """
        cursor.execute(query)
    except Exception as e:
        print(f"   ❌ 查询MCP工具失败: {e}")
        return
    
    tools = cursor.fetchall()
    if not tools:
        print("   无MCP工具数据")
        return

    for tool in tools:
        # 检查是否有TTL字段
        try:
            if hasattr(tool, 'keys') and 'ttl_expires_at' in tool.keys() and tool['ttl_expires_at']:
                expired = datetime.fromisoformat(tool['ttl_expires_at'].replace('Z', '+00:00')) < datetime.now()
                status_icon = "⚠️" if expired else "✅"
            else:
                status_icon = "✅"
        except:
            status_icon = "✅"

        # 安全获取字段值
        name = tool['name'] if hasattr(tool, '__getitem__') else getattr(tool, 'name', 'Unknown')
        description = tool.get('description', '无描述') if hasattr(tool, 'get') else getattr(tool, 'description', '无描述')
        resource_types = format_json_field(tool.get('resource_types') if hasattr(tool, 'get') else getattr(tool, 'resource_types', None))
        operation_types = format_json_field(tool.get('operation_types') if hasattr(tool, 'get') else getattr(tool, 'operation_types', None))

        print(f"   {status_icon} {name}")
        print(f"     描述: {description}")
        print(f"     资源类型: {resource_types}")
        print(f"     操作类型: {operation_types}")

def show_statistics(cursor):
    """显示统计信息"""
    print("\n📈 数据库统计:")
    
    tables = ['clusters', 'namespaces', 'nodes', 'pods', 'services', 'mcp_tools', 'cache_metadata']
    total_records = 0
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            total_records += count
            print(f"   {table}: {count} 条记录")
        except sqlite3.OperationalError:
            print(f"   {table}: 表不存在")
    
    print(f"   总计: {total_records} 条记录")
    
    # TTL统计
    print("\n⏰ TTL状态统计:")
    ttl_tables = ['clusters', 'namespaces', 'nodes', 'pods', 'services', 'mcp_tools']
    
    for table in ttl_tables:
        try:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN ttl_expires_at < datetime('now') THEN 1 END) as expired
                FROM {table}
            """)
            result = cursor.fetchone()
            if result['total'] > 0:
                expired_pct = (result['expired'] / result['total']) * 100
                status = "⚠️" if expired_pct > 50 else "✅"
                print(f"   {status} {table}: {result['total'] - result['expired']} 有效, {result['expired']} 过期")
        except sqlite3.OperationalError:
            continue

def main():
    """主函数"""
    print("=" * 60)
    print("📊 K8s缓存数据库查询")
    print("=" * 60)
    
    # 获取数据库路径
    db_path = os.getenv('CACHE_DB_PATH', './data/k8s_cache.db')
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        print("💡 请先运行扫描程序创建数据库")
        return
    
    print(f"📁 数据库文件: {db_path}")
    print(f"📏 文件大小: {db_file.stat().st_size / 1024:.1f} KB")
    print(f"🕒 修改时间: {datetime.fromtimestamp(db_file.stat().st_mtime)}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 执行查询
        show_statistics(cursor)
        query_clusters(cursor)
        query_namespaces(cursor)
        query_nodes(cursor)
        query_pods(cursor)
        query_services(cursor)
        query_mcp_tools(cursor)
        query_cache_metadata(cursor)
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 数据库查询完成")
        print("💡 使用 'sqlite3 " + db_path + "' 进行更详细的查询")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")

if __name__ == '__main__':
    main()
