"""
Unit and integration tests for SieveEngine and CLI execution.
"""
import unittest
from unittest.mock import patch
import io
import sys
from terminal_sieve.engine import SieveEngine
from terminal_sieve.cli import main

class TestCliAndEngine(unittest.TestCase):
    def test_engine_success_compression(self):
        engine = SieveEngine()
        # 50 lines of passing tests
        raw = "\n".join(f"test_{i} ... ok" for i in range(100)) + "\n\n100 passed in 0.82s"
        result = engine.compress(raw_output=raw, exit_code=0, duration=0.82)
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("100 test(s) passed successfully.", result.summary)
        self.assertGreater(result.compression_ratio, 0.70)  # >70% compression

    def test_engine_failure_compression(self):
        engine = SieveEngine()
        raw = """
[1/5] Building dependencies...
[2/5] Compiling typescript...
src/auth.ts(10,5): error TS2304: Cannot find name 'jwt'.
[3/5] Done with errors.
"""
        result = engine.compress(raw_output=raw, exit_code=1, duration=1.25)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("error TS2304", result.root_cause)
        self.assertIn("--- ROOT CAUSE ---", result.formatted_envelope)

    def test_cli_version_flag(self):
        with io.StringIO() as buf, unittest.mock.patch("sys.stdout", buf):
            with self.assertRaises(SystemExit) as cm:
                main(["--version"])
            self.assertEqual(cm.exception.code, 0)

    def test_cli_run_wrapper_success(self):
        # Run python -c "print('hello world')"
        with io.StringIO() as buf, unittest.mock.patch("sys.stdout", buf):
            ret = main(["run", sys.executable, "-c", "print('hello world')"])
            self.assertEqual(ret, 0)

    def test_cli_run_wrapper_failure(self):
        # Run python -c "raise ValueError('boom')"
        with io.StringIO() as buf, unittest.mock.patch("sys.stdout", buf):
            ret = main(["run", sys.executable, "-c", "raise ValueError('boom')"])
            self.assertNotEqual(ret, 0)

if __name__ == "__main__":
    unittest.main()
