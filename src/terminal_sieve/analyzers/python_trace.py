"""
Python traceback and pytest/unittest diagnostic analyzer.
"""
import re
from typing import List, Optional, Dict, Any
from .base import BaseAnalyzer

class PythonAnalyzer(BaseAnalyzer):
    name = "python"

    def match(self, text: str) -> bool:
        indicators = [
            "Traceback (most recent call last):",
            "=== FAILURES ===",
            "=== short test summary info ===",
            "pytest",
            "FAILED (failures=",
            "FAILED (errors=",
            "SyntaxError:",
            "IndentationError:",
            "ImportError:",
            "ModuleNotFoundError:",
        ]
        return any(ind in text for ind in indicators)

    def analyze(self, text: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        root_cause = ""
        key_context = []
        failing_items = []

        # 1. Look for standard Python unhandled exception
        exception_regex = re.compile(r"^([A-Z][a-zA-Z0-9_.]*(?:Error|Exception|Warning|Interrupt|Exit)): (.*)$")
        file_frame_regex = re.compile(r'^File "([^"]+)", line (\d+)(?:, in (.+))?')

        found_exception_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            m = exception_regex.match(lines[i])
            if m:
                root_cause = lines[i]
                found_exception_idx = i
                break

        if found_exception_idx != -1:
            # Gather preceding stack frames (skip site-packages when possible)
            user_frames = []
            for j in range(max(0, found_exception_idx - 15), found_exception_idx):
                frame_m = file_frame_regex.search(lines[j])
                if frame_m:
                    file_path = frame_m.group(1)
                    line_no = frame_m.group(2)
                    func = frame_m.group(3) or "<module>"
                    # Code snippet usually follows on the next line
                    snippet = lines[j + 1] if j + 1 < found_exception_idx and not lines[j + 1].startswith("File ") else ""
                    user_frames.append(f"{file_path}:{line_no} in {func}\n    {snippet}".strip())

            if user_frames:
                key_context = user_frames[-3:]  # Keep the 3 closest frames

        # 2. Look for pytest failures
        for i, line in enumerate(lines):
            if line.startswith("FAILED ") and (" - " in line or "::" in line):
                parts = line.split(" ", 1)[1]
                failing_items.append(parts)

        # 3. Check for syntax / indentation errors
        if not root_cause:
            for line in lines:
                if any(err in line for err in ["SyntaxError:", "IndentationError:", "ModuleNotFoundError:"]):
                    root_cause = line
                    break

        summary = f"Python execution failed with {root_cause}" if root_cause else "Python execution failed"

        return {
            "root_cause": root_cause,
            "key_context": "\n".join(key_context) if key_context else "",
            "failing_items": failing_items[:10],
            "summary": summary
        }
