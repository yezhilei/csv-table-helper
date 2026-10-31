"""检查 CSV 文件中的空值和重复值，并生成两份新表格。"""

import argparse
import csv
from collections import Counter
from pathlib import Path


def check_table(input_path, column_name, output_dir):
    """读取原表格；输出带检查结果的表格和问题清单。"""
    input_path = Path(input_path).resolve()
    output_dir = Path(output_dir).resolve()
    annotated_path = output_dir / "检查结果.csv"
    issues_path = output_dir / "问题清单.csv"

    if input_path in (annotated_path, issues_path):
        raise ValueError("输出文件不能与原文件相同，请选择其他输出文件夹。")
    if annotated_path.exists() or issues_path.exists():
        raise FileExistsError("输出文件已存在。请换一个空文件夹，避免覆盖已有结果。")

    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        headers = next(reader, None)
        if not headers:
            raise ValueError("文件为空，或缺少表头。")
        if any(not header.strip() for header in headers):
            raise ValueError("表头不能包含空列名。")
        if len(set(headers)) != len(headers):
            raise ValueError("表头有重复列名，请先修改表头。")
        if "检查结果" in headers:
            raise ValueError("原表格已有“检查结果”列，请先修改该列名。")
        if column_name not in headers:
            raise ValueError("找不到指定列。可用列名：" + "、".join(headers))
        rows = []
        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(headers):
                raise ValueError(f"第 {line_number} 条数据的列数与表头不同，请先检查文件。")
            rows.append(row)

    column_index = headers.index(column_name)
    # 检查时忽略首尾空格；空值单独统计，不参与重复值比较。
    values = [row[column_index].strip() for row in rows]
    counts = Counter(value for value in values if value)
    statuses = ["空值" if not value else "重复" if counts[value] > 1 else "正常" for value in values]

    output_dir.mkdir(parents=True, exist_ok=True)
    with annotated_path.open("x", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers + ["检查结果"])
        writer.writerows(row + [status] for row, status in zip(rows, statuses))
    with issues_path.open("x", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["原表格数据序号", "问题类型"] + headers)
        for number, (row, status) in enumerate(zip(rows, statuses), start=1):
            if status != "正常":
                writer.writerow([number, status] + row)

    return {
        "total": len(rows),
        "empty": statuses.count("空值"),
        "duplicate": statuses.count("重复"),
        "annotated_path": annotated_path,
        "issues_path": issues_path,
    }


def main():
    parser = argparse.ArgumentParser(description="检查 CSV 指定列的空值和重复值。")
    parser.add_argument("input", nargs="?", help="输入的 CSV 文件路径")
    parser.add_argument("column", nargs="?", help="需要检查的列名")
    parser.add_argument("output", nargs="?", help="保存结果的文件夹")
    args = parser.parse_args()

    try:
        input_path = args.input or input("CSV 文件路径：").strip().strip('"')
        column = args.column or input("要检查的列名：").strip()
        output = args.output or input("结果保存文件夹：").strip().strip('"')
        if not input_path or not column or not output:
            raise ValueError("文件路径、列名和输出文件夹都不能为空。")
        result = check_table(input_path, column, output)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"无法完成检查：{error}")
        return 1

    print(f"检查完成：共 {result['total']} 条，空值 {result['empty']} 条，重复 {result['duplicate']} 条。")
    print(f"检查结果：{result['annotated_path']}")
    print(f"问题清单：{result['issues_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
