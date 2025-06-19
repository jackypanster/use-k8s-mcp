#!/usr/bin/env python3
"""
主程序入口点
重新组织项目结构后的入口文件
"""

# 导入并运行主程序
if __name__ == "__main__":
    from src.main import main
    import asyncio
    asyncio.run(main())
