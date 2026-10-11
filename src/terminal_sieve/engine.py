"""
Core terminal compression and diagnostic extraction engine.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .analyzers import ANALYZERS

# Regular expression matching standard ANSI escape sequences
ANSI_ESCAPE_REGEX = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
)

# Common progress bar patterns
PROGRESS_REGEX = re.compile(
    r"(?:\[[=#\->\s]{4,}\]|\b\d{1,3}%\b|\b\d+\/\d+\b\s*(?:MB|kB|GB|B|KB))"
)

def strip_ansi(text: str) -> str:
    """
    Strips ANSI color codes, cursor movement sequences, clear lines,
    and resolves carriage-return overwritten lines.
    """
    # Remove ANSI escape sequences
    text = ANSI_ESCAPE_REGEX.sub("", text)

    # Handle carriage returns (\r) by taking the final overwritten line segment
    processed_lines = []
    for raw_line in text.split("\n"):
        if "\r" in raw_line:
            parts = [p for p in raw_line.split("\r") if p]
            final_part = parts[-1] if parts else ""
            processed_lines.append(final_part)
        else:
            processed_lines.append(raw_line)

    return "\n".join(processed_lines)

def normalize_line_for_repetition(line: str) -> str:
    """Replaces numbers, timestamps, and progress bars to detect cyclic logs."""
    norm = PROGRESS_REGEX.sub("<PROGRESS>", line)
    norm = re.sub(r"\b\d{1,4}[-/:.]\d{1,2}[-/:.]\d{1,4}\b", "<DATE>", norm)
    norm = re.sub(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\b", "<TIME>", norm)
    norm = re.sub(r"\b0x[0-9a-fA-F]+\b", "<HEX>", norm)
    norm = re.sub(r"\b\d+\b", "<NUM>", norm)
    return norm.strip()

def compress_repetitions(lines: List[str], max_consecutive: int = 2) -> List[str]:
    """
    Compresses consecutive repetitive or progress lines into concise summary markers.
    """
    if not lines:
        return []

    compressed = []
    i = 0
    n = len(lines)

    while i < n:
        current_line = lines[i]
        norm_current = normalize_line_for_repetition(current_line)
        count = 1
        j = i + 1

        while j < n and normalize_line_for_repetition(lines[j]) == norm_current:
            count += 1
            j += 1

        if count > max_consecutive:
            compressed.append(current_line)
            compressed.append(f"[sieve: repeated {count - 1} times identical or progress lines]")
            i = j
        else:
            compressed.append(current_line)
            i += 1

    return compressed

def estimate_tokens(text: str) -> int:
    """
    Approximates BPE token count (~4 characters per token heuristic).
    """
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    # Blend of character and word heuristic
    return max(1, int(chars / 3.8))

@dataclass
class SieveResult:
    status: str
    exit_code: Optional[int]
    duration: Optional[float]
    raw_chars: int
    raw_tokens: int
    compressed_chars: int
    compressed_tokens: int
    compression_ratio: float
    root_cause: str
    key_context: str
    failing_items: List[str]
    summary: str
    formatted_envelope: str

class SieveEngine:
    """Main compression and diagnostics extraction engine."""

    def __init__(self, max_lines: int = 30):
        self.max_lines = max_lines

    def compress(
        self,
        raw_output: str,
        exit_code: Optional[int] = None,
        duration: Optional[float] = None
    ) -> SieveResult:
        raw_chars = len(raw_output)
        raw_tokens = estimate_tokens(raw_output)

        clean_text = strip_ansi(raw_output)
        lines = [line.rstrip() for line in clean_text.splitlines() if line.strip()]
        compressed_lines = compress_repetitions(lines)
        reconstructed_text = "\n".join(compressed_lines)

        # Determine success / failure
        is_success = False
        if exit_code is not None:
            is_success = (exit_code == 0)
        else:
            # Heuristic check for success in test runners
            success_indicators = [
                "OK",
                "passed",
                "Success",
                "SUCCESS",
                "tests passed",
                "BUILD SUCCESSFUL",
            ]
            failure_indicators = [
                "FAILED",
                "ERROR",
                "Error:",
                "Exception:",
                "panic:",
                "FAIL",
                "npm ERR!",
            ]
            has_fail = any(ind in reconstructed_text for ind in failure_indicators)
            has_pass = any(ind in reconstructed_text for ind in success_indicators)
            is_success = has_pass and not has_fail

        status_str = "SUCCESS" if is_success else "FAILED"

        # If clean success, generate minimal high-signal envelope
        if is_success:
            pass_summary = "Execution completed successfully."
            # Extract test counts if present
            count_match = re.search(r"(\d+)\s+passed", reconstructed_text, re.IGNORECASE)
            if count_match:
                pass_summary = f"{count_match.group(1)} test(s) passed successfully."

            envelope = self._build_success_envelope(
                status=status_str,
                exit_code=exit_code or 0,
                duration=duration,
                summary=pass_summary,
                raw_tokens=raw_tokens
            )
            comp_tokens = estimate_tokens(envelope)
            comp_chars = len(envelope)
            ratio = max(0.0, 1.0 - (comp_tokens / max(1, raw_tokens)))

            return SieveResult(
                status=status_str,
                exit_code=exit_code if exit_code is not None else 0,
                duration=duration,
                raw_chars=raw_chars,
                raw_tokens=raw_tokens,
                compressed_chars=comp_chars,
                compressed_tokens=comp_tokens,
                compression_ratio=ratio,
                root_cause="",
                key_context="",
                failing_items=[],
                summary=pass_summary,
                formatted_envelope=envelope
            )

        # For failures, dispatch to specialized analyzers
        diagnostics = {}
        for analyzer in ANALYZERS:
            if analyzer.match(reconstructed_text):
                diagnostics = analyzer.analyze(reconstructed_text, exit_code)
                break

        root_cause = diagnostics.get("root_cause", "")
        key_context = diagnostics.get("key_context", "")
        failing_items = diagnostics.get("failing_items", [])
        summary = diagnostics.get("summary", "Command execution failed.")

        envelope = self._build_failure_envelope(
            status=status_str,
            exit_code=exit_code if exit_code is not None else 1,
            duration=duration,
            root_cause=root_cause,
            key_context=key_context,
            failing_items=failing_items,
            summary=summary,
            raw_tokens=raw_tokens
        )

        comp_tokens = estimate_tokens(envelope)
        comp_chars = len(envelope)
        ratio = max(0.0, 1.0 - (comp_tokens / max(1, raw_tokens)))

        return SieveResult(
            status=status_str,
            exit_code=exit_code if exit_code is not None else 1,
            duration=duration,
            raw_chars=raw_chars,
            raw_tokens=raw_tokens,
            compressed_chars=comp_chars,
            compressed_tokens=comp_tokens,
            compression_ratio=ratio,
            root_cause=root_cause,
            key_context=key_context,
            failing_items=failing_items,
            summary=summary,
            formatted_envelope=envelope
        )

    def _build_success_envelope(
        self,
        status: str,
        exit_code: int,
        duration: Optional[float],
        summary: str,
        raw_tokens: int
    ) -> str:
        dur_str = f" | Duration: {duration:.2f}s" if duration is not None else ""
        return (
            f"[sieve] Status: {status} (exit {exit_code}){dur_str}\n"
            f"[sieve] Summary: {summary}"
        )

    def _build_failure_envelope(
        self,
        status: str,
        exit_code: int,
        duration: Optional[float],
        root_cause: str,
        key_context: str,
        failing_items: List[str],
        summary: str,
        raw_tokens: int
    ) -> str:
        dur_str = f" | Duration: {duration:.2f}s" if duration is not None else ""
        parts = [
            f"[sieve] Status: {status} (exit {exit_code}){dur_str}",
            f"[sieve] Summary: {summary}"
        ]

        if root_cause:
            parts.append(f"\n--- ROOT CAUSE ---\n{root_cause}")

        if key_context:
            parts.append(f"\n--- KEY CONTEXT ---\n{key_context}")

        if failing_items:
            items_str = "\n".join(f"{idx}. {item}" for idx, item in enumerate(failing_items, 1))
            parts.append(f"\n--- FAILING ITEMS ({len(failing_items)}) ---\n{items_str}")

        return "\n".join(parts)
