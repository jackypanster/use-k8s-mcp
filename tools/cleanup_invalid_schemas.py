#!/usr/bin/env python3
"""
清理无效的schema文件脚本
删除包含特定错误信息的schema文件，并从completed_schemas.json中移除对应条目
"""

import json
from pathlib import Path


def find_invalid_schemas(schemas_dir):
    """查找包含错误信息的无效schema文件"""
    print("begin find_invalid_schemas")
    
    invalid_files = []
    error_pattern = "Agent stopped after reaching the maximum number of steps (10)."
    
    json_files = list(schemas_dir.glob("*.json"))
    print(f"检查 {len(json_files)} 个JSON文件")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if error_pattern in content:
                base_name = json_file.stem  # 去掉.json后缀
                invalid_files.append((json_file, base_name))
                print(f"发现无效文件: {json_file.name}")
        
        except Exception as e:
            print(f"读取文件 {json_file} 时出错: {e}")
            continue
    
    print(f"找到 {len(invalid_files)} 个无效文件")
    print("end find_invalid_schemas")
    return invalid_files


def update_completed_schemas(completed_file, invalid_base_names):
    """从completed_schemas.json中移除无效条目"""
    print(f"begin update_completed_schemas with {len(invalid_base_names)} items")

    with open(completed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 获取completed_tools数组
    completed_tools = data.get("completed_tools", [])
    original_count = len(completed_tools)

    # 移除无效条目
    updated_tools = [name for name in completed_tools if name not in invalid_base_names]

    removed_count = original_count - len(updated_tools)
    print(f"从completed_schemas.json中移除了 {removed_count} 个条目")

    # 更新数据结构
    data["completed_tools"] = updated_tools
    data["total_completed"] = len(updated_tools)

    # 写回文件
    with open(completed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("end update_completed_schemas")
    return removed_count


def delete_invalid_files(invalid_files):
    """删除无效的schema文件"""
    print(f"begin delete_invalid_files with {len(invalid_files)} files")
    
    deleted_count = 0
    
    for file_path, base_name in invalid_files:
        try:
            file_path.unlink()
            print(f"已删除文件: {file_path.name}")
            deleted_count += 1
        except Exception as e:
            print(f"删除文件 {file_path} 时出错: {e}")
            continue
    
    print(f"成功删除 {deleted_count} 个文件")
    print("end delete_invalid_files")
    return deleted_count


def main():
    """主函数：清理无效schema文件"""
    print("begin main")
    
    schemas_dir = Path("schemas/tools")
    completed_file = Path("schemas/completed_schemas.json")
    
    if not schemas_dir.exists():
        print(f"目录不存在: {schemas_dir}")
        return
    
    if not completed_file.exists():
        print(f"文件不存在: {completed_file}")
        return
    
    # 查找无效文件
    invalid_files = find_invalid_schemas(schemas_dir)
    
    if not invalid_files:
        print("没有找到无效文件")
        print("end main")
        return
    
    # 提取基础名称
    invalid_base_names = [base_name for _, base_name in invalid_files]
    
    # 删除无效文件
    deleted_count = delete_invalid_files(invalid_files)
    
    # 更新completed_schemas.json
    removed_count = update_completed_schemas(completed_file, invalid_base_names)
    
    print(f"清理完成: 删除了 {deleted_count} 个文件，移除了 {removed_count} 个队列条目")
    print("end main")


if __name__ == "__main__":
    main()
