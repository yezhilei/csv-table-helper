import csv
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from table_helper import check_table, main


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

    def test_quoted_fields_whitespace_and_case(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "data.csv"
            source.write_text('值,备注\n A ,"包含,逗号"\nA,第二行\na,小写\n  ,空白\n', encoding="utf-8")
            result = check_table(source, "值", Path(temp) / "out")
            self.assertEqual((result["empty"], result["duplicate"]), (1, 2))
            with result["annotated_path"].open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))
            self.assertEqual(rows[1], [" A ", "包含,逗号", "重复"])
            self.assertEqual(rows[3][-1], "正常")

    def test_malformed_quotes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bad.csv"
            source.write_text('编号,名字\n1,"没有结束\n', encoding="utf-8")
            output = Path(temp) / "out"
            with self.assertRaises(csv.Error):
                check_table(source, "编号", output)
            self.assertFalse(output.exists())

    def test_interactive_column_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            source = str(Path(__file__).parent / "示例表格.csv")
            with patch("sys.argv", ["table_helper.py"]), patch("builtins.input", side_effect=[source, "1", str(Path(temp) / "out")]), redirect_stdout(StringIO()) as display:
                result = main()
            self.assertEqual(result, 0)
            self.assertIn("1. 学号", display.getvalue())
            self.assertIn("空值 1 条，重复 2 条", display.getvalue())


if __name__ == "__main__":
    unittest.main()
