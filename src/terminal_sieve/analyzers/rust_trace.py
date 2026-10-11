"""
Rust, Cargo, and rustc diagnostic analyzer.
"""
import re
from typing import List, Optional, Dict, Any
from .base import BaseAnalyzer

class RustAnalyzer(BaseAnalyzer):
    name = "rust"

    def match(self, text: str) -> bool:
        indicators = [
            "error[E",
            "warning[W",
            "cargo test",
            "panicked at",
            "could not compile `",
        ]
        return any(ind in text for ind in indicators)

    def analyze(self, text: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        root_cause = ""
        key_context = []
        failing_items = []

        rust_err_regex = re.compile(r"^error\[(E\d+)\]:\s*(.+)$")
        arrow_regex = re.compile(r"^-->\s*(.+):(\d+):(\d+)$")
        panic_regex = re.compile(r"thread '.+' panicked at (.+)")

        for i, line in enumerate(lines):
            m = rust_err_regex.match(line)
            if m and not root_cause:
                root_cause = f"error[{m.group(1)}]: {m.group(2)}"
            
            p = panic_regex.search(line)
            if p and not root_cause:
                root_cause = f"panic: {p.group(1)}"

            arr = arrow_regex.match(line)
            if arr:
                key_context.append(f"{arr.group(1)}:{arr.group(2)}:{arr.group(3)}")
                # Capture adjacent code line if present
                if i + 1 < len(lines):
                    key_context.append(lines[i + 1])

        if not root_cause:
            for line in lines:
                if "could not compile" in line or "aborting due to" in line:
                    root_cause = line
                    break

        summary = f"Rust compilation/test failed: {root_cause}" if root_cause else "Rust execution failed"

        return {
            "root_cause": root_cause,
            "key_context": "\n".join(key_context[:4]) if key_context else "",
            "failing_items": failing_items[:10],
            "summary": summary
        }
