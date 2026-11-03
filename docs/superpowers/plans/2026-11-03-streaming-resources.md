# Streaming and resource bounds implementation plan

Goal: complete roadmap v0.5.0 without changing exact comparison semantics.

Architecture: a context-managed bounded binary reader feeds TextIOWrapper with
newline="" and row iterators for CSV/TSV/JSONL. JSON arrays and XLSX retain
their existing bounded adapters. The comparator consumes each iterator once and
enforces a diagnostic budget. A benchmark records elapsed time and tracemalloc
peak separately from full-process RSS, which it does not measure.

Ruling: reject reports exceeding resource limits with an operational error,
never return a partial passing report. Keep complete reports below the limits.
Ruling: retain buffered JSON arrays and bounded XLSX in this milestone because
replacing their parsers would add compatibility risk; document the boundary.

Review focus: stale stat/growing files; CR/LF/CRLF across decoding buffers;
generator closure on exceptions; header/empty/blank/row-limit behavior; JSONL
global column inference; hostile ZIP metadata; request framing; full-report
memory and browser rendering.

1. Write/run failing tests in tests/test_resources.py for streaming peak memory,
   CRLF/buffer boundaries, row/byte limits, diagnostic budgets, numeric tokens
   and duplicate XLSX entries. Add real concurrent/framing HTTP tests.
2. Implement rowcanary/streaming.py open_rows context manager; reuse existing
   adapters for buffered formats. Refactor core.check_file into one-pass
   comparison, preserving all existing issue codes/order and default controls.
3. Bound diagnostic count/text, numeric JSON fields, XLSX duplicate entries,
   listen backlog and initial browser rendering. Keep all downloads complete.
4. Add tools/benchmark.py and record deterministic generated-file measurements;
   run focused tests, all tests and an independent review. Fix important findings.
5. Update limits/docs/changelog/PROGRESS; full release gates, trail check,
   commit/push, all hosted jobs, publish and verify v0.5.0 independently.
