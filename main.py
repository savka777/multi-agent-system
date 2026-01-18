"""
Convenience entrypoint so you can run:

  uv run python main.py

The actual project code currently lives in `src/main.py`.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    runpy.run_path(str(Path(__file__).parent / "src" / "main.py"), run_name="__main__")


if __name__ == "__main__":
    main()

