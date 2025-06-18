#!/usr/bin/env python3
"""
K8s集群扫描环境检查脚本
简化版本，专注于环境配置验证
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def check_environment():
    """检查环境配置"""
    print("🔧 检查环境配置...")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env 文件加载成功")
    except ImportError:
        print("⚠️ python-dotenv 未安装，尝试直接读取环境变量")
    except Exception as e:
        print(f"⚠️ .env 文件加载失败: {e}")
    
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
        value = os.getenv(var)
        # 隐藏敏感信息
        if 'URL' in var and value:
            if len(value) > 20:
                display_value = value[:10] + "..." + value[-10:]
            else:
                display_value = value
        else:
            display_value = value
        print(f"   {var}: {display_value}")
    
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
        print(f"⚠️ 数据库文件不存在: {db_path}")
        print("💡 这是正常的，首次运行扫描时会自动创建")
        return True  # 这不是错误
    
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
            print("⚠️ 数据库中没有表，可能需要初始化")
            return True  # 这也不是错误
        
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
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库访问失败: {e}")
        return False

def check_imports():
    """检查关键模块导入"""
    print("\n📦 检查模块导入...")
    
    # 检查关键依赖
    dependencies = [
        ('dotenv', 'python-dotenv'),
        ('mcp_use', 'mcp-use'),
        ('sqlite3', '内置模块')
    ]
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {module} ({package})")
        except ImportError:
            print(f"❌ {module} ({package}) - 请安装: pip install {package}")
    
    # 检查项目模块
    project_modules = [
        'src.cache',
        'src.scanner.cluster_scanner',
        'src.scanner.resource_parser',
        'src.scanner.scan_coordinator',
        'src.mcp_tools'
    ]
    
    print("\n🔧 检查项目模块:")
    all_imported = True
    
    for module in project_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            all_imported = False
    
    return all_imported

def check_mcp_connection():
    """检查MCP连接（基础测试）"""
    print("\n🔗 检查MCP连接配置...")
    
    mcp_url = os.getenv('MCP_SERVER_URL')
    mcp_type = os.getenv('MCP_SERVER_TYPE')
    
    if not mcp_url or not mcp_type:
        print("❌ MCP配置不完整")
        return False
    
    print(f"✅ MCP服务器类型: {mcp_type}")
    
    # 基础URL格式检查
    if mcp_type == 'sse':
        if not mcp_url.startswith(('http://', 'https://')):
            print(f"⚠️ SSE类型的URL格式可能不正确: {mcp_url}")
        else:
            print(f"✅ URL格式正确")
    
    print("💡 实际连接测试需要运行完整扫描程序")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 K8s集群扫描环境检查")
    print("=" * 60)
    
    # 检查步骤
    checks = [
        ("环境配置", check_environment),
        ("数据库状态", check_database),
        ("模块导入", check_imports),
        ("MCP连接配置", check_mcp_connection)
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
    
    if success_rate >= 75:
        print("🎉 环境配置良好，可以运行扫描程序！")
        print("\n💡 下一步操作:")
        print("   运行扫描演示: uv run python script/run-scanner-demo.py")
    else:
        print("❌ 环境配置存在问题，请解决后再运行")
        print("\n🔧 建议操作:")
        print("   1. 检查 .env 文件配置")
        print("   2. 安装缺失的依赖包")
        print("   3. 确认项目结构完整")

if __name__ == '__main__':
    main()
