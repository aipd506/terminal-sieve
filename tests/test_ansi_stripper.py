"""
Unit tests for ANSI escape code and terminal artifact stripping.
"""
import unittest
from terminal_sieve.engine import strip_ansi

class TestAnsiStripper(unittest.TestCase):
    def test_strip_color_codes(self):
        colored = "\x1b[31mRed text\x1b[0m and \x1b[32mGreen text\x1b[0m"
        clean = strip_ansi(colored)
        self.assertEqual(clean, "Red text and Green text")

    def test_strip_cursor_and_clear_codes(self):
        raw = "Processing...\x1b[2K\x1b[1GDone!"
        clean = strip_ansi(raw)
        self.assertNotIn("\x1b", clean)
        self.assertIn("Done!", clean)

    def test_carriage_return_resolution(self):
        progress = "Downloading: 10%\rDownloading: 50%\rDownloading: 100%\nCompleted"
        clean = strip_ansi(progress)
        self.assertEqual(clean, "Downloading: 100%\nCompleted")

    def test_plain_text_unaltered(self):
        text = "Standard stdout line 1\nStandard stdout line 2"
        clean = strip_ansi(text)
        self.assertEqual(clean, text)

if __name__ == "__main__":
    unittest.main()
