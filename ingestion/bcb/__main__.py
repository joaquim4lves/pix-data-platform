"""``python -m ingestion.bcb``."""

from __future__ import annotations

import sys

from ingestion.bcb.cli import main

if __name__ == "__main__":
    sys.exit(main())
