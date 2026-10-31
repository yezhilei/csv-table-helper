import csv
import tempfile
import unittest
from pathlib import Path

from table_helper import check_table


class TableHelperTests(unittest.TestCase):
    def test_example_detects_all_duplicate_rows_and_blank(self):
        with tempfile.TemporaryDirectory() as temp:
            result = check_table(Path(__file__).parent / "示例表格.csv", "学号", temp)
            self.assertEqual((result["total"], result["empty"], result["duplicate"]), (5, 1, 2))
            with result["issues_path"].open(encoding="utf-8-sig", newline="") as file:
                issues = list(csv.reader(file))
            self.assertEqual([row[:2] for row in issues[1:]], [["2", "重复"], ["3", "重复"], ["4", "空值"]])
            with self.assertRaises(FileExistsError):
                check_table(Path(__file__).parent / "示例表格.csv", "学号", temp)

    def test_invalid_rows_are_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bad.csv"
            source.write_text("编号,名字\n1\n", encoding="utf-8")
            output = Path(temp) / "output"
            with self.assertRaises(ValueError):
                check_table(source, "编号", output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
