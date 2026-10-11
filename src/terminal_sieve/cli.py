"""
Command-line interface for terminal-sieve.
Supports pipe mode (reading from stdin) and wrapper mode (executing a subprocess command).
"""
import sys
import os
import time
import json
import argparse
import subprocess
from typing import List, Optional
from .engine import SieveEngine
from . import __version__

def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="sieve",
        description="The intelligent terminal output compressor for AI coding agents and LLMs."
    )
    parser.add_argument("--version", action="version", version=f"terminal-sieve {__version__}")
    parser.add_argument("--json", action="store_true", help="Output structured JSON envelope")
    parser.add_argument("--metrics", action="store_true", default=True, help="Display compression token metrics footer")
    parser.add_argument("--no-metrics", action="store_false", dest="metrics", help="Disable metrics footer")
    parser.add_argument("--max-lines", type=int, default=30, help="Maximum context lines to retain (default: 30)")

    subparsers = parser.add_subparsers(dest="subcommand", help="Operational modes")

    # Command wrapper mode
    run_parser = subparsers.add_parser("run", help="Run a command, capture output, and compress diagnostics")
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute")

    args = parser.parse_args(argv)
    engine = SieveEngine(max_lines=args.max_lines)

    if args.subcommand == "run":
        if not args.cmd:
            print("Error: No command specified to run.", file=sys.stderr)
            return 1

        cmd_to_run = args.cmd
        # If passed with leading '--', strip it
        if cmd_to_run and cmd_to_run[0] == "--":
            cmd_to_run = cmd_to_run[1:]

        start_time = time.monotonic()
        try:
            proc = subprocess.run(
                cmd_to_run,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            duration = time.monotonic() - start_time
            raw_output = proc.stdout or ""
            exit_code = proc.returncode
        except Exception as e:
            duration = time.monotonic() - start_time
            raw_output = f"Execution failed: {str(e)}"
            exit_code = 1

        result = engine.compress(raw_output=raw_output, exit_code=exit_code, duration=duration)

    else:
        # Pipe mode: read from standard input
        if sys.stdin.isatty():
            parser.print_help()
            return 0

        raw_output = sys.stdin.read()
        result = engine.compress(raw_output=raw_output)
        exit_code = result.exit_code or 0

    # Output formatting
    if args.json:
        payload = {
            "status": result.status,
            "exit_code": result.exit_code,
            "duration": result.duration,
            "raw_chars": result.raw_chars,
            "raw_tokens": result.raw_tokens,
            "compressed_chars": result.compressed_chars,
            "compressed_tokens": result.compressed_tokens,
            "compression_ratio": round(result.compression_ratio, 4),
            "summary": result.summary,
            "root_cause": result.root_cause,
            "key_context": result.key_context,
            "failing_items": result.failing_items,
            "envelope": result.formatted_envelope
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.formatted_envelope)
        if args.metrics and result.raw_tokens > 0:
            pct = int(result.compression_ratio * 100)
            print(f"[sieve] Metrics: Compressed {pct}% ({result.raw_tokens:,} -> {result.compressed_tokens:,} tokens)")

    return exit_code if exit_code is not None else 0

if __name__ == "__main__":
    sys.exit(main())
