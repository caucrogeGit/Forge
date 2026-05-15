import sys
from pathlib import Path

_packages_dir = Path(__file__).parent / "packages"
for _pkg in sorted(_packages_dir.iterdir()):
    if _pkg.is_dir():
        sys.path.insert(0, str(_pkg))
