"""Manual DataGrid demo."""

from __future__ import annotations

import tkinter as tk

from .datagrid import DataGrid
from .datagrid_models import Column


def run_datagrid_demo() -> None:
    root = tk.Tk()
    root.title("DataGrid 测试")
    root.geometry("1000x600")
    root.configure(bg="#1a1a1a")

    columns = [
        Column(key="id", label="ID", width=80, align="center"),
        Column(key="name", label="姓名", width=150),
        Column(key="email", label="邮箱", width=250),
        Column(key="department", label="部门", width=150),
        Column(key="status", label="状态", width=100, align="center"),
        Column(
            key="score",
            label="评分",
            width=100,
            align="right",
            formatter=lambda x: f"{x:.1f}分" if isinstance(x, (int, float)) else str(x),
        ),
    ]

    test_data = [
        {
            "id": i,
            "name": f"用户{i}",
            "email": f"user{i}@example.com",
            "department": ["技术部", "市场部", "运营部"][i % 3],
            "status": ["在职", "离职"][i % 2],
            "score": 60 + (i % 40),
        }
        for i in range(1, 10001)
    ]

    def on_select(selected_indices: list[int]) -> None:
        print(f"选择了: {selected_indices}")

    def on_sort(column: str, order: str) -> None:
        print(f"排序: {column} {order}")

    grid = DataGrid(
        root,
        columns=columns,
        selectable=True,
        multi_select=True,
        on_row_select=on_select,
        on_sort=on_sort,
    )
    grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    grid.set_data(test_data)
    root.mainloop()
