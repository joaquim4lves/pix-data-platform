"""Run the dbt CLI as ``python -m transform.dbt_main``.

dbt Core 1.12 has no ``dbt/__main__.py``, and the console script is not
guaranteed to be on ``PATH``. This module is the entrypoint ``make`` and
the transform CLI use.
"""

from __future__ import annotations

from dbt.cli.main import cli


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
