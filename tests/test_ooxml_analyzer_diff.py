import sys
import unittest
from io import StringIO
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ooxml_analyzer import OOXMLAnalyzer


class TestOOXMLAnalyzerDiff(unittest.TestCase):
    def test_print_diff_output(self):
        analyzer = OOXMLAnalyzer('dummy.pptx')
        original = {'a': 1, 'b': 2}
        processed = {'a': 1, 'b': 3, 'c': 4}
        captured = StringIO()
        stdout = sys.stdout
        try:
            sys.stdout = captured
            analyzer.print_diff(original, processed)
        finally:
            sys.stdout = stdout
        output = captured.getvalue()
        self.assertIn('-  "b": 2', output)
        self.assertIn('+  "b": 3,', output)
        self.assertIn('+  "c": 4', output)


if __name__ == '__main__':
    unittest.main()
