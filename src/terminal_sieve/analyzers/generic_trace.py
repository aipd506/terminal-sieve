"""
Fallback generic error and failure diagnostic analyzer.
"""
import re
from typing import List, Optional, Dict, Any
from .base import BaseAnalyzer

class GenericAnalyzer(BaseAnalyzer):
    name = "generic"

    def match(self, text: str) -> bool:
        return True

    def analyze(self, text: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        root_cause = ""
        key_context = []
        failing_items = []

        severity_keywords = [
            "fatal:", "fatal error:", "error:", "failed:", "failure:", "panic:",
            "exception:", "reverted", "aborted", "cannot find", "command not found"
        ]

        scored_lines = []
        for line in lines:
            line_lower = line.lower()
            for kw in severity_keywords:
                if kw in line_lower:
                    scored_lines.append(line)
                    break

        if scored_lines:
            root_cause = scored_lines[0]
            key_context = scored_lines[1:5]
        elif lines:
            root_cause = lines[-1]

        summary = f"Command failed with {root_cause}" if root_cause else "Command execution failed"

        return {
            "root_cause": root_cause,
            "key_context": "\n".join(key_context) if key_context else "",
            "failing_items": failing_items,
            "summary": summary
        }
