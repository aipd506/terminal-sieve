# terminal-sieve

The intelligent terminal output compressor and diagnostic filter for AI coding agents, Cursor, Claude Desktop, Antigravity, and LLM development environments.

## The Core Problem

When autonomous AI coding agents execute terminal commands, up to 80 percent of their context window budget is consumed by uninformative terminal artifacts:
1. Dynamic progress bars and carriage return rewrites (`\r`, ANSI escape sequences).
2. Thousands of lines of repetitive build steps, file downloads, and polling logs.
3. Giant 500-line stack traces where 95 percent of frames are internal framework files (`node_modules`, `site-packages`, standard library internals).
4. Full test suite dumps printing hundreds of passing tests when only one test failed.

This token bloat leads directly to context window amnesia, prompt cache misses, model hallucinations, and inflated API costs.

## The Solution

`terminal-sieve` intercepts stdout and stderr streams in real-time. It strips ANSI escape animations, collapses repetitive progress output into count markers, extracts the exact root-cause exception and user-codeframe context, and returns a structured diagnostic envelope optimized for LLM comprehension.

### Compression Benchmarks
1. Unit Test Success (100 passing tests): 2,400 tokens compressed to 28 tokens (98.8 percent token reduction).
2. TypeScript Compilation Errors: 1,850 tokens compressed to 145 tokens (92.1 percent token reduction).
3. Python Unhandled Exception Trace: 3,200 tokens compressed to 190 tokens (94.0 percent token reduction).
4. Rust Cargo Build Diagnostic: 4,100 tokens compressed to 180 tokens (95.6 percent token reduction).

## Installation

```bash
pip install terminal-sieve
```

`terminal-sieve` is written in pure Python with zero external runtime dependencies. It runs on any machine with Python 3.8 or higher across Linux, macOS, and Windows.

## Usage Modes

### 1. Wrapper Mode (Recommended)
Wrap any test runner, compiler, or shell command. `terminal-sieve` executes the command, records execution duration, captures exit codes, and prints the compressed diagnostic:

```bash
sieve run pytest
sieve run npm test
sieve run cargo test
sieve run tsc --noEmit
```

### 2. Standard Pipe Mode
Pipe command output directly into `sieve`:

```bash
pytest | sieve
npm test 2>&1 | sieve
cat build.log | sieve
```

### 3. Structured JSON Mode
Ideal for MCP servers, IDE sidecars, and automated agent pipelines:

```bash
sieve --json run pytest
```

Output format:
```json
{
  "status": "FAILED",
  "exit_code": 1,
  "duration": 0.42,
  "raw_chars": 8412,
  "raw_tokens": 2213,
  "compressed_chars": 482,
  "compressed_tokens": 126,
  "compression_ratio": 0.9431,
  "summary": "Python execution failed with ZeroDivisionError: float division by zero",
  "root_cause": "ZeroDivisionError: float division by zero",
  "key_context": "src/math_utils.py:12 in calculate_discount\n    return price * (1.0 - rate)",
  "failing_items": [
    "tests/test_service.py::test_order_processing - ZeroDivisionError"
  ],
  "envelope": "[sieve] Status: FAILED (exit 1) | Duration: 0.42s\n..."
}
```

## Architectural Design

`terminal-sieve` consists of four modular processing stages:
1. ANSI & Stream Normalization: Removes CSI codes, SGR sequences, and collapses carriage-return progress bars.
2. Repetition & Cycle Reducer: Employs token-normalized similarity matching to collapse repeating log statements into count markers.
3. Specialized Language Analyzers:
   1. Python Analyzer: Isolates unhandled exception types, filters internal framework frames, and captures pytest failure summaries.
   2. Node / TypeScript Analyzer: Pinpoints `error TS...` coordinate diagnostics, isolates root runtime `Error:` types, and filters `node_modules` noise.
   3. Rust Analyzer: Detects `error[E...]` compiler codes and source arrows.
   4. Generic Analyzer: High-signal keyword severity ranking for unknown environments.
4. LLM Diagnostic Envelope Generator: Produces a high-density, structured envelope designed for LLM prompts.

## Contributing and Community

`terminal-sieve` is free, open-source software licensed under the MIT License. Contributions, issue reports, and pull requests are welcomed.

### Sovereign Payout and Sponsorship Coordinates
1. Bitcoin Native SegWit: `bc1qaedjdrkrhjya767yvfz676jeyx5an04kfwzczg`
2. Stacks Protocol: `SP3Q5P9MEREY8KQVBRHH4BBVAB4GTKPDYPT80002V`
