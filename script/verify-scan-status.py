#!/usr/bin/env python3
"""
K8s集群扫描状态验证脚本
快速检查扫描系统状态和数据库内容
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def check_environment():
    """检查环境配置"""
    print("🔧 检查环境配置...")

    # 首先加载.env文件
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        'MCP_SERVER_URL', 'MCP_SERVER_TYPE', 'MCP_SERVER_NAME'
    ]
    
    optional_vars = {
        'CACHE_DB_PATH': './data/k8s_cache.db',
        'CACHE_STATIC_TTL': '1800',
        'CACHE_DYNAMIC_TTL': '300'
    }
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ 缺少必需环境变量: {', '.join(missing)}")
        print("💡 请检查 .env 文件配置")
        return False
    
    print("✅ 必需环境变量配置正确")
    
    # 显示配置信息
    print("\n📋 当前配置:")
    for var in required_vars:
        print(f"   {var}: {os.getenv(var)}")
    
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"   {var}: {value}")
    
    return True

def check_database():
    """检查数据库状态"""
    print("\n💾 检查数据库状态...")
    
    db_path = os.getenv('CACHE_DB_PATH', './data/k8s_cache.db')
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        print("💡 请先运行扫描程序创建数据库")
        return False
    
    print(f"✅ 数据库文件存在: {db_path}")
    print(f"   文件大小: {db_file.stat().st_size / 1024:.1f} KB")
    print(f"   修改时间: {datetime.fromtimestamp(db_file.stat().st_mtime)}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row['name'] for row in cursor.fetchall()]
        
        if not tables:
            print("⚠️  数据库中没有表，可能需要初始化")
            return False
        
        print(f"✅ 数据库包含 {len(tables)} 个表: {', '.join(tables)}")
        
        # 检查数据统计
        print("\n📊 数据统计:")
        data_tables = ['clusters', 'namespaces', 'nodes', 'pods', 'services']
        total_records = 0
        
        for table in data_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                total_records += count
                print(f"   {table}: {count} 条记录")
        
        print(f"   总计: {total_records} 条记录")
        
        # 检查缓存元数据
        if 'cache_metadata' in tables:
            cursor.execute("""
                SELECT table_name, scan_status, last_scan_at
                FROM cache_metadata
                ORDER BY last_scan_at DESC
                LIMIT 5
            """)
            metadata = cursor.fetchall()
            
            if metadata:
                print("\n📈 最近扫描状态:")
                for meta in metadata:
                    status_icon = "✅" if meta['scan_status'] == 'completed' else "❌"
                    print(f"   {status_icon} {meta['table_name']}: {meta['scan_status']}")
                    if meta['last_scan_at']:
                        print(f"      最后扫描: {meta['last_scan_at']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库访问失败: {e}")
        return False

def check_ttl_status():
    """检查TTL状态"""
    print("\n⏰ 检查TTL状态...")
    
    db_path = os.getenv('CACHE_DB_PATH', './data/k8s_cache.db')
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        tables_with_ttl = ['clusters', 'namespaces', 'nodes', 'pods', 'services']
        
        for table in tables_with_ttl:
            try:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN ttl_expires_at < datetime('now') THEN 1 END) as expired,
                        COUNT(CASE WHEN ttl_expires_at >= datetime('now') THEN 1 END) as valid
                    FROM {table}
                """)
                
                result = cursor.fetchone()
                if result['total'] > 0:
                    expired_pct = (result['expired'] / result['total']) * 100
                    status_icon = "⚠️" if expired_pct > 50 else "✅"
                    print(f"   {status_icon} {table}: {result['valid']} 有效, {result['expired']} 过期 ({expired_pct:.1f}%)")
                
            except sqlite3.OperationalError:
                # 表可能不存在
                continue
        
        conn.close()
        
    except Exception as e:
        print(f"❌ TTL检查失败: {e}")

def check_scan_components():
    """检查扫描组件状态"""
    print("\n🔍 检查扫描组件...")
    
    try:
        # 尝试导入扫描组件
        from src.cache import CacheManager
        from src.scanner import ClusterScanner, ScanCoordinator, ResourceParser
        from src.mcp_tools import MCPToolLoader
        
        print("✅ 扫描组件导入成功")
        
        # 测试缓存管理器
        try:
            cache_manager = CacheManager()
            stats = cache_manager.get_cache_stats()
            print("✅ 缓存管理器工作正常")
        except Exception as e:
            print(f"❌ 缓存管理器错误: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 组件导入失败: {e}")
        print("💡 请检查项目结构和依赖")
        return False

def run_quick_scan_test():
    """运行快速扫描测试"""
    print("\n🧪 运行快速扫描测试...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 检查是否可以创建扫描组件
        from src.cache import CacheManager
        from src.scanner import ResourceParser
        
        cache_manager = CacheManager()
        resource_parser = ResourceParser()
        
        print("✅ 扫描组件创建成功")
        
        # 测试解析器
        parser_stats = resource_parser.get_parsing_stats()
        print(f"✅ 资源解析器状态: 解析 {parser_stats['parsed_count']} 次")
        
        return True
        
    except Exception as e:
        print(f"❌ 扫描测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 K8s集群扫描状态验证")
    print("=" * 60)
    
    # 检查步骤
    checks = [
        ("环境配置", check_environment),
        ("数据库状态", check_database),
        ("TTL状态", check_ttl_status),
        ("扫描组件", check_scan_components),
        ("快速测试", run_quick_scan_test)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name}检查失败: {e}")
            results[name] = False
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 检查结果总结:")
    print("=" * 60)
    
    passed = 0
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    print(f"\n🎯 总体状态: {passed}/{len(results)} 项通过 ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 扫描系统状态良好，可以正常使用！")
        print("\n💡 下一步操作:")
        print("   1. 运行扫描演示: uv run python src/scanner/scanner_demo.py")
        print("   2. 查看数据库内容: sqlite3 ./data/k8s_cache.db")
    elif success_rate >= 80:
        print("⚠️  扫描系统基本正常，但有一些问题需要解决")
    else:
        print("❌ 扫描系统存在严重问题，请检查配置和依赖")
        print("\n🔧 建议操作:")
        print("   1. 检查 .env 文件配置")
        print("   2. 确认MCP服务器运行状态")
        print("   3. 验证项目依赖安装")

if __name__ == '__main__':
    main()
