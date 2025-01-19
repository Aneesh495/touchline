"""Command line entry point.

Subcommands are added as subsystems come online. At this stage ``doctor`` and
``build`` work; other subcommands report that they are not yet wired so the
interface never lies about what it can do.
"""

from __future__ import annotations

import argparse
import sys


def _doctor() -> int:
    import platform

    print("Touchline doctor")
    print(f"  python     : {platform.python_version()} ({platform.machine()})")
    print(f"  platform   : {platform.platform()}")
    try:
        import numpy

        print(f"  numpy      : {numpy.__version__}")
    except Exception as exc:  # pragma: no cover
        print(f"  numpy      : missing ({exc})")
    try:
        import polars

        print(f"  polars     : {polars.__version__}")
    except Exception as exc:  # pragma: no cover
        print(f"  polars     : missing ({exc})")
    try:
        import torch

        print(f"  torch      : {torch.__version__} (cuda={torch.cuda.is_available()})")
    except Exception:
        print("  torch      : not installed (install extra 'learn' for neural models)")
    return 0


def _not_wired(name: str) -> int:
    print(f"'{name}' is not wired yet in this build. See docs/BUILD_STATUS.md.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="touchline", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in [
        "doctor",
        "build",
        "data",
        "demo",
        "bench",
        "stress",
        "ingest",
        "coverage",
        "features",
        "train",
        "evaluate",
        "simulate",
        "thesis",
        "acceptance",
        "verify",
        "release",
    ]:
        sp = sub.add_parser(name)
        sp.add_argument("--sample", action="store_true")
        sp.add_argument("--run-id", default=None)
        sp.add_argument("--profile", default="cpu")
        sp.add_argument("--evidence", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return _doctor()
    if args.command == "build":
        import touchline

        print(f"touchline {touchline.__version__}")
        return 0
    return _not_wired(args.command)


if __name__ == "__main__":
    sys.exit(main())
