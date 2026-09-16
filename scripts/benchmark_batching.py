"""Run a deterministic, mock-only batching benchmark and emit JSON metrics."""

from __future__ import annotations

import argparse
import json

from codex_babeldoc.translation.benchmark import run_benchmark


def main(argv: list[str] | None = None) -> int:
    """Parse benchmark arguments and print JSON metrics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args(argv)
    print(
        json.dumps(run_benchmark(args.items, args.batch_size), ensure_ascii=False, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
