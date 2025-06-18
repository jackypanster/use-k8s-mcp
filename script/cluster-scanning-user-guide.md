# K8s集群扫描系统用户指南

## 1. 扫描系统依赖关系

### 1.1 scan是否依赖main.py？

**答案：不依赖**。扫描系统可以独立运行，有以下几种启动方式：

1. **独立扫描演示**：`src/scanner/scanner_demo.py`
2. **集成测试运行**：`test/test_scan_integration.py`
3. **单元测试运行**：`test/test_cluster_scanner.py`

### 1.2 扫描系统架构

```
扫描系统独立组件:
├── ScanCoordinator (扫描协调器)
├── ClusterScanner (集群扫描器)
├── ResourceParser (资源解析器)
├── CacheManager (缓存管理器)
└── MCPToolLoader (工具加载器)

main.py 只是一个可选的集成入口点
```

## 2. 如何启动扫描

### 2.1 方法一：使用扫描演示程序（推荐）

```bash
# 进入项目根目录
cd /home/user/workspace/use-k8s-mcp

# 设置环境变量
export PYTHONPATH=$PWD/src:$PYTHONPATH

# 运行扫描演示
uv run python src/scanner/scanner_demo.py
```

### 2.2 方法二：使用集成测试

```bash
# 运行集成测试（包含扫描功能验证）
uv run python test/test_scan_integration.py
```

### 2.3 方法三：编程方式启动

创建自定义扫描脚本：

```python
# custom_scan.py
import asyncio
import os
from dotenv import load_dotenv
from mcp_use import MCPClient

# 添加src到路径
import sys
sys.path.insert(0, 'src')

from src.scanner import ClusterScanner, ScanCoordinator, ResourceParser
from src.cache import CacheManager
from src.mcp_tools import MCPToolLoader

async def run_custom_scan():
    """自定义扫描运行"""
    load_dotenv()
    
    # 1. 创建MCP客户端
    config = {
        "mcpServers": {
            os.getenv("MCP_SERVER_NAME", "k8s"): {
                "type": os.getenv("MCP_SERVER_TYPE", "stdio"),
                "url": os.getenv("MCP_SERVER_URL", "")
            }
        }
    }
    mcp_client = MCPClient.from_dict(config)
    
    # 2. 初始化组件
    cache_manager = CacheManager()
    tool_loader = MCPToolLoader(cache_manager)
    cluster_scanner = ClusterScanner(mcp_client, tool_loader)
    resource_parser = ResourceParser()
    
    scan_coordinator = ScanCoordinator(
        cluster_scanner=cluster_scanner,
        resource_parser=resource_parser,
        cache_manager=cache_manager,
        static_ttl=1800,  # 30分钟
        dynamic_ttl=300   # 5分钟
    )
    
    # 3. 执行扫描
    result = await scan_coordinator.scan_cluster_full(
        cluster_name="my-cluster",
        include_static=True,
        include_dynamic=True
    )
    
    print(f"扫描完成: {result}")

if __name__ == '__main__':
    asyncio.run(run_custom_scan())
```

## 3. 验证扫描已经生效

### 3.1 检查扫描状态

```python
# 检查扫描状态的方法
async def check_scan_status():
    # 1. 健康检查
    health = await scan_coordinator.health_check()
    print(f"系统状态: {health['status']}")
    print(f"组件状态: {health['components']}")
    
    # 2. 获取扫描历史
    history = await scan_coordinator.get_scan_history("my-cluster", limit=5)
    for record in history:
        print(f"表: {record['table_name']}, 状态: {record['scan_status']}")
        print(f"最后扫描: {record['last_scan_at']}")
    
    # 3. 获取统计信息
    stats = scan_coordinator.get_coordinator_stats()
    print(f"扫描会话: {stats['scan_sessions']}")
    print(f"成功扫描: {stats['successful_scans']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
```

### 3.2 验证扫描结果

扫描成功的标志：

```bash
# 运行扫描演示后，查看输出
✅ 集群扫描完成!
📊 扫描统计:
   - 集群名称: demo-cluster
   - 扫描时长: 2.34秒
   - 静态资源: 5 个
     * clusters: 1
     * namespaces: 2
     * nodes: 2
   - 动态资源: 15 个
     * pods: 10
     * services: 5
   - 总资源数: 20
```

## 4. 如何查看数据已经进入数据库

### 4.1 使用缓存管理器查询

```python
# 查询缓存数据的方法
def check_cached_data():
    cache_manager = CacheManager()
    
    # 1. 查询集群信息
    clusters = cache_manager.list_records('clusters')
    print(f"缓存的集群: {len(clusters)} 个")
    for cluster in clusters:
        print(f"  - {cluster.name}: {cluster.version}")
    
    # 2. 查询命名空间
    namespaces = cache_manager.list_records('namespaces')
    print(f"缓存的命名空间: {len(namespaces)} 个")
    
    # 3. 查询Pod
    pods = cache_manager.list_records('pods')
    print(f"缓存的Pod: {len(pods)} 个")
    
    # 4. 查询缓存元数据
    metadata = cache_manager.list_records('cache_metadata')
    print(f"缓存元数据: {len(metadata)} 条")
    for meta in metadata:
        print(f"  - 表: {meta.table_name}, 状态: {meta.scan_status}")
```

### 4.2 直接查询SQLite数据库

```bash
# 查看数据库文件位置
echo $CACHE_DB_PATH
# 或默认位置: ./data/k8s_cache.db

# 使用sqlite3命令行工具
sqlite3 ./data/k8s_cache.db

# 查看所有表
.tables

# 查看集群数据
SELECT name, version, node_count, created_at FROM clusters;

# 查看命名空间数据
SELECT cluster_name, name, status FROM namespaces;

# 查看Pod数据
SELECT cluster_name, namespace, name, phase, node_name FROM pods LIMIT 10;

# 查看缓存统计
SELECT 
    table_name,
    cluster_name,
    record_count,
    last_scan_at,
    scan_status
FROM cache_metadata;

# 检查TTL状态
SELECT 
    'clusters' as table_name,
    COUNT(*) as total,
    COUNT(CASE WHEN ttl_expires_at < datetime('now') THEN 1 END) as expired
FROM clusters
UNION ALL
SELECT 
    'pods' as table_name,
    COUNT(*) as total,
    COUNT(CASE WHEN ttl_expires_at < datetime('now') THEN 1 END) as expired
FROM pods;
```

### 4.3 使用数据库查询脚本

创建查询脚本：

```python
# db_query.py
import sqlite3
import os
from datetime import datetime

def query_database():
    """查询数据库内容"""
    db_path = os.getenv('CACHE_DB_PATH', './data/k8s_cache.db')
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        cursor = conn.cursor()
        
        print("=" * 60)
        print("📊 K8s缓存数据库查询结果")
        print("=" * 60)
        
        # 1. 查看表统计
        tables = ['clusters', 'namespaces', 'nodes', 'pods', 'services']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"📋 {table}: {count} 条记录")
        
        print("\n" + "-" * 40)
        
        # 2. 查看最新的集群信息
        cursor.execute("""
            SELECT name, version, node_count, created_at 
            FROM clusters 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        clusters = cursor.fetchall()
        if clusters:
            print("🏢 最新集群信息:")
            for cluster in clusters:
                print(f"  - {cluster['name']}: v{cluster['version']} ({cluster['node_count']} 节点)")
        
        # 3. 查看扫描状态
        cursor.execute("""
            SELECT table_name, cluster_name, scan_status, last_scan_at
            FROM cache_metadata
            ORDER BY last_scan_at DESC
            LIMIT 10
        """)
        
        metadata = cursor.fetchall()
        if metadata:
            print("\n📈 最近扫描状态:")
            for meta in metadata:
                print(f"  - {meta['table_name']} ({meta['cluster_name']}): {meta['scan_status']}")
                print(f"    最后扫描: {meta['last_scan_at']}")
        
        conn.close()
        print("\n✅ 数据库查询完成")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")

if __name__ == '__main__':
    query_database()
```

运行查询脚本：

```bash
uv run python db_query.py
```

## 5. 环境配置要求

### 5.1 必需的环境变量

```bash
# .env 文件配置
# MCP服务器配置
MCP_SERVER_URL=stdio:///path/to/k8s-mcp
MCP_SERVER_TYPE=stdio
MCP_SERVER_NAME=k8s-mcp

# 缓存配置
CACHE_DB_PATH=./data/k8s_cache.db
CACHE_STATIC_TTL=1800
CACHE_DYNAMIC_TTL=300

# 扫描配置
SCANNER_STATIC_INTERVAL=1800
SCANNER_DYNAMIC_INTERVAL=300
SCANNER_TIMEOUT=120
```

### 5.2 验证配置

```python
# 验证配置的脚本
def validate_scan_config():
    """验证扫描配置"""
    required_vars = [
        'MCP_SERVER_URL', 'MCP_SERVER_TYPE', 'MCP_SERVER_NAME',
        'CACHE_DB_PATH', 'CACHE_STATIC_TTL', 'CACHE_DYNAMIC_TTL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ 缺少环境变量: {', '.join(missing)}")
        return False
    
    print("✅ 扫描配置验证通过")
    return True
```

## 6. 故障排查

### 6.1 常见问题

**问题1：扫描失败**
```
❌ 集群扫描失败: Tool k8s_list_pods failed after 3 attempts
```
**解决方案：**
- 检查MCP服务器是否运行
- 验证MCP_SERVER_URL配置
- 检查网络连接

**问题2：数据库为空**
```
📋 clusters: 0 条记录
```
**解决方案：**
- 确认扫描已成功执行
- 检查TTL是否过期
- 验证数据库路径配置

**问题3：权限错误**
```
❌ 数据库查询失败: Permission denied
```
**解决方案：**
- 检查数据库文件权限
- 确认CACHE_DB_PATH目录存在
- 验证写入权限

### 6.2 调试命令

```bash
# 检查数据库文件
ls -la ./data/k8s_cache.db

# 检查数据库完整性
sqlite3 ./data/k8s_cache.db "PRAGMA integrity_check;"

# 查看最近的错误
sqlite3 ./data/k8s_cache.db "
SELECT table_name, error_message, updated_at 
FROM cache_metadata 
WHERE scan_status = 'failed' 
ORDER BY updated_at DESC 
LIMIT 5;
"
```

---

**总结：**
1. 扫描系统不依赖main.py，可独立运行
2. 使用`src/scanner/scanner_demo.py`是最简单的启动方式
3. 通过缓存管理器或SQLite命令可以验证数据
4. 配置正确的环境变量是成功运行的关键
