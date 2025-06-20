#!/usr/bin/env python3
"""
批量处理schema文件，提取Final Answer中的JSON内容并重新组织结构
"""

import json
import re
from pathlib import Path


def extract_final_answer_json(schema_text):
    """
    从schema文本中提取Final Answer的JSON内容

    Args:
        schema_text: 包含Thought/Action/Final Answer的文本

    Returns:
        dict: 提取的JSON对象，如果失败返回None
    """
    try:
        # 方法1: 查找Final Answer后的完整JSON内容（带```json```包装）
        final_answer_pattern = r'Final Answer:\s*```json\s*(\{.*?\})\s*```'
        match = re.search(final_answer_pattern, schema_text, re.DOTALL)

        if match:
            json_str = match.group(1)
            return json.loads(json_str)

        # 方法2: 查找Final Answer后的JSON内容（不完整的```结尾）
        final_answer_incomplete_pattern = r'Final Answer:\s*```json\s*(\{.*?)(?:\s*```|\s*$)'
        match = re.search(final_answer_incomplete_pattern, schema_text, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
            # 尝试修复不完整的JSON
            if not json_str.endswith('}'):
                # 尝试找到最后一个完整的对象
                brace_count = 0
                last_complete_pos = -1
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_complete_pos = i + 1

                if last_complete_pos > 0:
                    json_str = json_str[:last_complete_pos]

            return json.loads(json_str)

        # 方法3: 查找任何JSON格式（带```json```包装）
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, schema_text, re.DOTALL)

        if match:
            json_str = match.group(1)
            return json.loads(json_str)

        # 方法4: 查找不完整的JSON格式（只有开头```json，没有结尾```）
        incomplete_json_pattern = r'```json\s*(\{.*?)(?:\s*```|\s*$)'
        match = re.search(incomplete_json_pattern, schema_text, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
            # 尝试修复不完整的JSON
            if not json_str.endswith('}'):
                # 尝试找到最后一个完整的对象
                brace_count = 0
                last_complete_pos = -1
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_complete_pos = i + 1

                if last_complete_pos > 0:
                    json_str = json_str[:last_complete_pos]

            return json.loads(json_str)

        return None

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"   ❌ 提取错误: {e}")
        return None


def process_single_schema_file(file_path):
    """
    处理单个schema文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否成功处理
    """
    print(f"🔧 处理文件: {file_path.name}")
    
    try:
        # 读取原始文件
        with open(file_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 检查是否需要处理
        if not isinstance(original_data.get('schema'), str):
            print(f"   ℹ️  跳过: schema字段已经是对象格式")
            return True
            
        schema_text = original_data['schema']
        
        # 检查是否包含Final Answer或JSON格式
        if 'Final Answer:' not in schema_text and '```json' not in schema_text:
            print(f"   ℹ️  跳过: 不包含Final Answer或JSON格式")
            return True
        
        # 提取JSON内容
        extracted_json = extract_final_answer_json(schema_text)
        
        if extracted_json is None:
            print(f"   ❌ 无法提取JSON内容")
            return False
        
        # 重新组织数据结构
        new_data = {
            "tool_name": original_data.get("tool_name"),
            "extraction_timestamp": original_data.get("extraction_timestamp"),
            "data_integrity_principle": original_data.get("data_integrity_principle"),
            "schema": extracted_json  # 使用提取的JSON对象
        }
        
        # 保存处理后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 成功处理: 提取了 {len(str(extracted_json))} 字符的JSON")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ 文件JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始批量处理schema文件...")
    
    # 定义文件目录
    schemas_dir = Path("schemas/tools")
    
    if not schemas_dir.exists():
        print(f"❌ 目录不存在: {schemas_dir}")
        return
    
    # 获取所有JSON文件
    json_files = list(schemas_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ 未找到JSON文件: {schemas_dir}")
        return
    
    print(f"📁 找到 {len(json_files)} 个JSON文件")
    
    # 统计变量
    success_count = 0
    skip_count = 0
    error_count = 0
    error_files = []
    
    # 逐个处理文件
    for i, file_path in enumerate(json_files, 1):
        print(f"\n📋 [{i}/{len(json_files)}] 处理: {file_path.name}")
        
        try:
            result = process_single_schema_file(file_path)
            if result:
                success_count += 1
            else:
                error_count += 1
                error_files.append(file_path.name)
        except Exception as e:
            print(f"   💥 意外错误: {e}")
            error_count += 1
            error_files.append(file_path.name)
    
    # 输出统计结果
    print(f"\n📊 处理完成统计:")
    print(f"   总文件数: {len(json_files)}")
    print(f"   成功处理: {success_count}")
    print(f"   跳过文件: {skip_count}")
    print(f"   错误文件: {error_count}")
    
    if error_files:
        print(f"\n❌ 错误文件列表:")
        for error_file in error_files:
            print(f"   - {error_file}")
    
    print(f"\n✅ 批量处理完成!")


if __name__ == "__main__":
    main()
