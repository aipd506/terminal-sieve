"""
Node.js, TypeScript, Jest, Vitest, and npm diagnostic analyzer.
"""
import re
from typing import List, Optional, Dict, Any
from .base import BaseAnalyzer

class NodeAnalyzer(BaseAnalyzer):
    name = "node"

    def match(self, text: str) -> bool:
        indicators = [
            "at ",
            "TypeError:",
            "ReferenceError:",
            "SyntaxError:",
            "npm ERR!",
            "FAIL ",
            "vitest",
            "jest",
            "ts(",
            "TS",
            "Error: Cannot find module",
        ]
        return any(ind in text for ind in indicators)

    def analyze(self, text: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        root_cause = ""
        key_context = []
        failing_items = []

        # 1. Match TypeScript compiler errors: path.ts(42,10): error TS2322: ...
        ts_regex = re.compile(r"^(.+\.tsx?)\((\d+),(\d+)\):\s*error\s*(TS\d+):\s*(.+)$")
        ts_errors = []
        for line in lines:
            m = ts_regex.match(line)
            if m:
                ts_errors.append(f"{m.group(1)}:{m.group(2)}:{m.group(3)} - error {m.group(4)}: {m.group(5)}")

        if ts_errors:
            root_cause = ts_errors[0]
            failing_items = ts_errors
            return {
                "root_cause": root_cause,
                "key_context": "\n".join(ts_errors[:5]),
                "failing_items": ts_errors[:10],
                "summary": f"TypeScript compilation failed with {len(ts_errors)} error(s)"
            }

        # 2. Match Jest / Vitest FAIL items
        for line in lines:
            if line.startswith("FAIL "):
                failing_items.append(line.replace("FAIL ", "").strip())

        # 3. Match Standard Error: ...
        error_regex = re.compile(r"^([A-Z][a-zA-Z0-9_.]*(?:Error|Exception)): (.*)$")
        stack_frame_regex = re.compile(r"^\s*at\s+(.+)\s+\((.+):(\d+):(\d+)\)")

        frames = []
        for i, line in enumerate(lines):
            m = error_regex.match(line)
            if m and not root_cause:
                root_cause = line
            frame_m = stack_frame_regex.match(line)
            if frame_m and "node_modules" not in line and "node:internal" not in line:
                frames.append(f"{frame_m.group(2)}:{frame_m.group(3)} in {frame_m.group(1)}")

        # 4. Fallback to npm ERR!
        if not root_cause:
            npm_errors = [line for line in lines if line.startswith("npm ERR!")]
            if npm_errors:
                root_cause = npm_errors[0]

        summary = f"JavaScript/TypeScript execution failed with {root_cause}" if root_cause else "Node.js execution failed"

        return {
            "root_cause": root_cause,
            "key_context": "\n".join(frames[:4]) if frames else "",
            "failing_items": failing_items[:10],
            "summary": summary
        }
