"""应用层

应用层负责用例编排，协调领域层和基础设施层。

包含：
- ports: 端口定义（入站/出站）
- use_cases: 应用用例
- dto: 数据传输对象

说明：
此处不再使用 `import *` 以便静态分析工具（ruff/mypy）正确工作。
"""

from . import dto, ports, use_cases

__all__ = [
    "dto",
    "ports",
    "use_cases",
]
