"""
MCP工具Schema解析器
专注于解析MCP工具的schema定义和参数提取
遵循单一职责原则，文件大小控制在150行以内
"""

import json
import time
from typing import Dict, Any, List, Tuple, Optional

from .models import ToolSchema
from .exceptions import SchemaParseError
from src.fail_fast_exceptions import create_exception_context


class SchemaParser:
    """MCP工具Schema解析器 - 专注schema解析和验证"""
    
    def __init__(self) -> None:
        """初始化Schema解析器"""
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_tool_schema(self, tool_data: Dict[str, Any]) -> ToolSchema:
        """解析工具schema
        
        Args:
            tool_data: MCP工具原始数据
            
        Returns:
            解析后的工具schema对象
            
        Raises:
            SchemaParseError: schema解析失败时抛出
        """
        start_time = time.time()
        
        try:
            # 验证必需字段
            self._validate_required_fields(tool_data)
            
            # 提取基础信息
            name = tool_data['name']
            description = tool_data.get('description', '')
            
            # 解析输入schema
            input_schema = self._parse_input_schema(tool_data)
            
            # 解析输出schema（可选）
            output_schema = self._parse_output_schema(tool_data)
            
            # 创建ToolSchema对象
            schema = ToolSchema(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema
            )
            
            self.parsed_count += 1
            return schema
            
        except Exception as e:
            self.error_count += 1
            context = create_exception_context(
                operation=f"parse_tool_schema_{tool_data.get('name', 'unknown')}",
                tool_name=tool_data.get('name'),
                tool_data_keys=list(tool_data.keys()),
                execution_time=time.time() - start_time,
                original_error=str(e)
            )
            raise SchemaParseError(f"工具schema解析失败: {e}", context) from e
    
    def extract_parameters(
        self, 
        schema: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """提取schema中的必需和可选参数
        
        Args:
            schema: 输入schema字典
            
        Returns:
            (必需参数列表, 可选参数列表)
        """
        try:
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            required_params = [param for param in required if param in properties]
            optional_params = [
                param for param in properties.keys() 
                if param not in required
            ]
            
            return required_params, optional_params
            
        except Exception as e:
            context = create_exception_context(
                operation="extract_parameters",
                schema_keys=list(schema.keys()) if isinstance(schema, dict) else [],
                original_error=str(e)
            )
            raise SchemaParseError(f"参数提取失败: {e}", context) from e
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """验证schema有效性
        
        Args:
            schema: 待验证的schema
            
        Returns:
            是否有效
        """
        try:
            # 检查基本结构
            if not isinstance(schema, dict):
                return False
            
            # 检查type字段
            if 'type' not in schema:
                return False
            
            # 如果是object类型，检查properties
            if schema.get('type') == 'object':
                properties = schema.get('properties')
                if properties is not None and not isinstance(properties, dict):
                    return False
            
            # 检查required字段
            required = schema.get('required')
            if required is not None and not isinstance(required, list):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_required_fields(self, tool_data: Dict[str, Any]) -> None:
        """验证工具数据的必需字段"""
        required_fields = ['name']
        
        for field in required_fields:
            if field not in tool_data:
                raise ValueError(f"缺少必需字段: {field}")
        
        if not isinstance(tool_data['name'], str) or not tool_data['name'].strip():
            raise ValueError("工具名称必须是非空字符串")
    
    def _parse_input_schema(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析输入schema"""
        input_schema = tool_data.get('inputSchema', {})
        
        # 如果没有inputSchema，尝试其他可能的字段名
        if not input_schema:
            input_schema = tool_data.get('input_schema', {})
        
        # 如果仍然为空，创建默认schema
        if not input_schema:
            input_schema = {
                'type': 'object',
                'properties': {},
                'required': []
            }
        
        # 验证schema有效性
        if not self.validate_schema(input_schema):
            raise ValueError(f"无效的输入schema: {input_schema}")
        
        return input_schema
    
    def _parse_output_schema(self, tool_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析输出schema（可选）"""
        output_schema = tool_data.get('outputSchema')
        
        if not output_schema:
            output_schema = tool_data.get('output_schema')
        
        # 输出schema是可选的
        if output_schema and not self.validate_schema(output_schema):
            # 输出schema无效时记录警告但不抛出异常
            return None
        
        return output_schema
    
    def get_parsing_stats(self) -> Dict[str, int]:
        """获取解析统计信息"""
        return {
            'parsed_count': self.parsed_count,
            'error_count': self.error_count,
            'success_rate': (
                self.parsed_count / max(1, self.parsed_count + self.error_count)
            ) * 100
        }
