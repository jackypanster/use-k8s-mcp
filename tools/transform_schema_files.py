#!/usr/bin/env python3
"""
简单脚本：转换schema文件结构
将schema对象内容提升到根级别，移除外层包装字段
"""

import json
from pathlib import Path


def transform_schema_file(file_path):
    """转换单个schema文件"""
    print(f"begin transform_schema_file with {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict):
        print(f"跳过文件 {file_path} - 不是JSON对象")
        return False

    transformed = False

    # 如果有schema字段，提取schema内容
    if 'schema' in data:
        data = data['schema']
        transformed = True
        print(f"提取schema内容: {file_path}")

    # 如果有tool_name字段，重命名为name
    if 'tool_name' in data:
        data['name'] = data.pop('tool_name')
        transformed = True
        print(f"重命名tool_name为name: {file_path}")

    # 如果没有任何转换，跳过
    if not transformed:
        print(f"跳过文件 {file_path} - 无需转换")
        return False

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"已转换文件: {file_path}")
    print(f"end transform_schema_file")
    return True


def main():
    """主函数：处理tools/schemas/tools/目录下的所有JSON文件"""
    print("begin main")
    
    schema_dir = Path("schemas/tools")
    
    if not schema_dir.exists():
        print(f"目录不存在: {schema_dir}")
        return
    
    json_files = list(schema_dir.glob("*.json"))
    print(f"找到 {len(json_files)} 个JSON文件")
    
    transformed_count = 0
    
    for json_file in json_files:
        try:
            if transform_schema_file(json_file):
                transformed_count += 1
        except Exception as e:
            print(f"处理文件 {json_file} 时出错: {e}")
            continue
    
    print(f"总共转换了 {transformed_count} 个文件")
    print("end main")


if __name__ == "__main__":
    main()
