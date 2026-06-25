# pyright: strict
from __future__ import annotations

from pathlib import Path

from cli.public.public_list import MakePublicShowResult, show_main


def main(args: list[str], *, root: Path | None = None) -> MakePublicShowResult:
    return show_main(args, root=root)
