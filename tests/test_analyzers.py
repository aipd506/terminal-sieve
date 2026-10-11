"""
Unit tests for language-specific analyzers (Python, Node/TypeScript, Rust, Generic).
"""
import unittest
from terminal_sieve.analyzers.python_trace import PythonAnalyzer
from terminal_sieve.analyzers.node_trace import NodeAnalyzer
from terminal_sieve.analyzers.rust_trace import RustAnalyzer
from terminal_sieve.analyzers.generic_trace import GenericAnalyzer

class TestAnalyzers(unittest.TestCase):
    def test_python_traceback_extraction(self):
        sample = """
Traceback (most recent call last):
  File "src/service.py", line 45, in process_order
    total = calculate_discount(price, rate)
  File "src/math_utils.py", line 12, in calculate_discount
    return price * (1.0 - rate)
ZeroDivisionError: float division by zero
FAILED tests/test_service.py::test_order_processing - ZeroDivisionError
"""
        analyzer = PythonAnalyzer()
        self.assertTrue(analyzer.match(sample))
        diag = analyzer.analyze(sample)
        self.assertEqual(diag["root_cause"], "ZeroDivisionError: float division by zero")
        self.assertIn("calculate_discount", diag["key_context"])
        self.assertIn("tests/test_service.py::test_order_processing - ZeroDivisionError", diag["failing_items"])

    def test_typescript_error_extraction(self):
        sample = """
src/models/user.ts(42,15): error TS2322: Type 'string' is not assignable to type 'number'.
src/models/auth.ts(18,5): error TS2554: Expected 2 arguments, but got 1.
Found 2 errors in 2 files.
"""
        analyzer = NodeAnalyzer()
        self.assertTrue(analyzer.match(sample))
        diag = analyzer.analyze(sample)
        self.assertIn("error TS2322", diag["root_cause"])
        self.assertEqual(len(diag["failing_items"]), 2)

    def test_node_runtime_error(self):
        sample = """
TypeError: Cannot read properties of undefined (reading 'status')
    at handleRequest (/app/src/server.ts:88:24)
    at Layer.handle [as handle_request] (/app/node_modules/express/lib/router/layer.js:95:5)
"""
        analyzer = NodeAnalyzer()
        self.assertTrue(analyzer.match(sample))
        diag = analyzer.analyze(sample)
        self.assertEqual(diag["root_cause"], "TypeError: Cannot read properties of undefined (reading 'status')")
        # node_modules should be filtered out from key context
        self.assertNotIn("node_modules", diag["key_context"])
        self.assertIn("/app/src/server.ts:88 in handleRequest", diag["key_context"])

    def test_rust_cargo_error(self):
        sample = """
error[E0382]: borrow of moved value: `data`
  --> src/main.rs:14:20
   |
12 |     let data = vec![1, 2, 3];
14 |     consume_data(data);
   |                  ---- value moved here
16 |     println!("{:?}", data);
   |                      ^^^^ value borrowed here after move
error: aborting due to 1 previous error
"""
        analyzer = RustAnalyzer()
        self.assertTrue(analyzer.match(sample))
        diag = analyzer.analyze(sample)
        self.assertIn("error[E0382]: borrow of moved value: `data`", diag["root_cause"])
        self.assertIn("src/main.rs:14:20", diag["key_context"])

    def test_generic_fallback(self):
        sample = """
[INFO] Starting build...
[WARN] Deprecated dependency in use
fatal: destination path 'target_dir' already exists and is not an empty directory.
[INFO] Build aborted.
"""
        analyzer = GenericAnalyzer()
        diag = analyzer.analyze(sample)
        self.assertIn("destination path 'target_dir' already exists", diag["root_cause"])

if __name__ == "__main__":
    unittest.main()
