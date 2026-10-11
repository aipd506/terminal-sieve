"""
Base analyzer module for terminal diagnostic extraction.
"""
from typing import List, Optional, Tuple, Dict, Any

class BaseAnalyzer:
    """Abstract base class for language-specific diagnostic analyzers."""

    name: str = "generic"

    def match(self, text: str) -> bool:
        """Determines whether this analyzer should handle the given output."""
        raise NotImplementedError

    def analyze(self, text: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
        """
        Extracts structured diagnostics:
        - root_cause: Direct error or exception statement
        - key_context: Relevant code snippet or location
        - failing_items: List of failing tests, files, or symbols
        - summary: High-level descriptive sentence
        """
        raise NotImplementedError
