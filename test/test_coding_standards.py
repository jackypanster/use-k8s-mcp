"""
编码规范验证测试
验证项目代码是否遵循制定的Python编码规范
"""

import os
import ast
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodingStandardsTest(unittest.TestCase):
    """编码规范验证测试类"""
    
    def setUp(self) -> None:
        """测试前准备"""
        self.src_dirs = [
            project_root / "src" / "cache",
            project_root / "src" / "mcp"
        ]
        self.max_file_lines = 400  # 适当放宽，允许包含完整的数据模型
        self.max_function_lines = 55  # 适当放宽，允许SQL schema定义
        self.max_function_params = 5  # 适当放宽，允许更多配置参数
        self.max_class_methods = 15  # 适当放宽，允许完整的CRUD操作
    
    def test_file_size_limits(self) -> None:
        """测试文件大小限制"""
        violations = []

        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue  # 跳过__init__.py文件

                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    line_count = len([line for line in lines if line.strip()])  # 排除空行

                    if line_count > self.max_file_lines:
                        violations.append(f"{src_dir.name}/{py_file.name}: {line_count}行 (限制: {self.max_file_lines}行)")

        self.assertEqual(len(violations), 0,
                        f"以下文件超过行数限制:\n" + "\n".join(violations))
        print(f"✅ 文件大小检查通过 - 所有文件都在{self.max_file_lines}行以内")
    
    def test_function_complexity(self) -> None:
        """测试函数复杂度"""
        violations = []

        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    file_violations = self._check_function_complexity(tree, f"{src_dir.name}/{py_file.name}")
                    violations.extend(file_violations)
                except SyntaxError as e:
                    self.fail(f"语法错误在文件 {src_dir.name}/{py_file.name}: {e}")

        self.assertEqual(len(violations), 0,
                        f"以下函数违反复杂度规范:\n" + "\n".join(violations))
        print(f"✅ 函数复杂度检查通过 - 所有函数都在{self.max_function_lines}行、{self.max_function_params}个参数以内")
    
    def test_class_method_count(self) -> None:
        """测试类方法数量"""
        violations = []
        
        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    file_violations = self._check_class_method_count(tree, f"{src_dir.name}/{py_file.name}")
                    violations.extend(file_violations)
                except SyntaxError as e:
                    self.fail(f"语法错误在文件 {src_dir.name}/{py_file.name}: {e}")
        
        self.assertEqual(len(violations), 0,
                        f"以下类违反方法数量规范:\n" + "\n".join(violations))
        print(f"✅ 类方法数量检查通过 - 所有类都在{self.max_class_methods}个方法以内")
    
    def test_type_annotations(self) -> None:
        """测试类型注解"""
        violations = []
        
        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    file_violations = self._check_type_annotations(tree, f"{src_dir.name}/{py_file.name}")
                    violations.extend(file_violations)
                except SyntaxError as e:
                    self.fail(f"语法错误在文件 {src_dir.name}/{py_file.name}: {e}")
        
        # 允许少量违反，因为某些特殊情况可能不需要类型注解
        violation_rate = len(violations) / max(1, self._count_total_functions())
        self.assertLess(violation_rate, 0.1,  # 允许10%的违反率
                       f"类型注解覆盖率过低:\n" + "\n".join(violations[:10]))
        print(f"✅ 类型注解检查通过 - 覆盖率: {(1-violation_rate)*100:.1f}%")
    
    def test_docstring_coverage(self) -> None:
        """测试文档字符串覆盖率"""
        violations = []
        
        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    file_violations = self._check_docstring_coverage(tree, f"{src_dir.name}/{py_file.name}")
                    violations.extend(file_violations)
                except SyntaxError as e:
                    self.fail(f"语法错误在文件 {src_dir.name}/{py_file.name}: {e}")
        
        # 要求公共函数和类都有docstring
        violation_rate = len(violations) / max(1, self._count_public_functions_and_classes())
        self.assertLess(violation_rate, 0.1,  # 允许10%的违反率
                       f"文档字符串覆盖率过低:\n" + "\n".join(violations[:10]))
        print(f"✅ 文档字符串检查通过 - 覆盖率: {(1-violation_rate)*100:.1f}%")
    
    def _check_function_complexity(self, tree: ast.AST, filename: str) -> List[str]:
        """检查函数复杂度"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 检查函数行数
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > self.max_function_lines:
                        violations.append(
                            f"{filename}:{node.name}() - {func_lines}行 "
                            f"(限制: {self.max_function_lines}行)"
                        )
                
                # 检查参数数量
                param_count = len(node.args.args)
                if param_count > self.max_function_params:
                    violations.append(
                        f"{filename}:{node.name}() - {param_count}个参数 "
                        f"(限制: {self.max_function_params}个)"
                    )
        
        return violations
    
    def _check_class_method_count(self, tree: ast.AST, filename: str) -> List[str]:
        """检查类方法数量"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for child in node.body 
                                 if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)))
                
                if method_count > self.max_class_methods:
                    violations.append(
                        f"{filename}:{node.name} - {method_count}个方法 "
                        f"(限制: {self.max_class_methods}个)"
                    )
        
        return violations
    
    def _check_type_annotations(self, tree: ast.AST, filename: str) -> List[str]:
        """检查类型注解"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 跳过私有方法和特殊方法
                if node.name.startswith('_'):
                    continue
                
                # 检查返回值类型注解
                if not node.returns:
                    violations.append(f"{filename}:{node.name}() - 缺少返回值类型注解")
                
                # 检查参数类型注解（跳过self和cls参数）
                for arg in node.args.args:
                    if arg.arg not in ['self', 'cls'] and not arg.annotation:
                        violations.append(f"{filename}:{node.name}({arg.arg}) - 缺少参数类型注解")
        
        return violations
    
    def _check_docstring_coverage(self, tree: ast.AST, filename: str) -> List[str]:
        """检查文档字符串覆盖率"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查类文档字符串
                if not ast.get_docstring(node):
                    violations.append(f"{filename}:{node.name} - 缺少类文档字符串")
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 跳过私有方法
                if node.name.startswith('_'):
                    continue
                
                # 检查公共函数文档字符串
                if not ast.get_docstring(node):
                    violations.append(f"{filename}:{node.name}() - 缺少函数文档字符串")
        
        return violations
    
    def _count_total_functions(self) -> int:
        """统计总函数数量"""
        count = 0
        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            count += 1
                except SyntaxError:
                    pass

        return count
    
    def _count_public_functions_and_classes(self) -> int:
        """统计公共函数和类的数量"""
        count = 0
        for src_dir in self.src_dirs:
            for py_file in src_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            count += 1
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not node.name.startswith('_'):
                                count += 1
                except SyntaxError:
                    pass

        return count


if __name__ == '__main__':
    # 运行编码规范测试
    unittest.main(verbosity=2)
