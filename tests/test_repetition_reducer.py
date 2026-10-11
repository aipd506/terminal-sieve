"""
Unit tests for repetitive log compression.
"""
import unittest
from terminal_sieve.engine import compress_repetitions

class TestRepetitionReducer(unittest.TestCase):
    def test_collapses_consecutive_duplicates(self):
        lines = [
            "Initializing worker...",
            "Retrying database connection (attempt 1)",
            "Retrying database connection (attempt 2)",
            "Retrying database connection (attempt 3)",
            "Retrying database connection (attempt 4)",
            "Connected successfully."
        ]
        compressed = compress_repetitions(lines, max_consecutive=2)
        # Should collapse attempts 1-4
        self.assertIn("Retrying database connection (attempt 1)", compressed)
        self.assertTrue(any("repeated 3 times" in line for line in compressed))
        self.assertIn("Connected successfully.", compressed)

    def test_preserves_unique_lines(self):
        lines = [
            "Step 1: Compile",
            "Step 2: Link",
            "Step 3: Test",
            "Step 4: Package"
        ]
        compressed = compress_repetitions(lines)
        self.assertEqual(lines, compressed)

if __name__ == "__main__":
    unittest.main()
