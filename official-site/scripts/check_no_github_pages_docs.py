#!/usr/bin/env python3
"""Garde-fou : le site officiel ``forgemvc.com`` ne doit pas référencer
``caucrogegit.github.io/Forge`` pour sa navigation interne.

Règle de contrat public (OFFICIAL-SITE-LOCAL-DOCS-LINKS-001) :

    Le site officiel forgemvc.com ne doit pas utiliser GitHub Pages pour
    sa documentation interne. Les liens internes de documentation doivent
    cibler ``/docs/forge/...`` ou ``https://forgemvc.com/docs/forge/...``.

Le script échoue (exit 1) dès qu'il trouve un lien actif (attribut HTML
``href``/``src`` ou lien Markdown ``](...)``) vers ``caucrogegit.github.io/Forge``
dans le périmètre surveillé.

Les mentions purement textuelles (tableaux d'audits, exemples en code
inline backquotés, journaux historiques) restent autorisées via la liste
d'exclusions ci-dessous.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Périmètre surveillé : la landing et la documentation publiée.
SCAN_TARGETS: tuple[Path, ...] = (
    ROOT / "public",
    ROOT / "landing",
    ROOT / "docs",
    ROOT / "dist",
    ROOT / "site",
)

# Fichiers/dossiers explicitement archivés ou historiques :
# les URL ``caucrogegit.github.io/Forge`` y apparaissent comme références
# d'incidents passés, pas comme navigation interne.
EXCLUDED_PATHS: tuple[str, ...] = (
    # Archives de la landing pré-migration (lecture seule).
    "sources/forge-landing/",
    # Audits Forge-official-site : tracent justement la migration depuis
    # GitHub Pages — ces URL y sont citées comme état antérieur.
    "docs/audits/",
    # Audits historiques de Forge core importés : trace de tickets clos.
    "docs/forge/history/",
    # Cache MkDocs.
    "site/search/",
)

# Extensions auditées.
SCANNED_EXTENSIONS: frozenset[str] = frozenset({".html", ".md"})

# Patterns de liens "actifs" (pas du texte inline ni du code).
#
# - HTML : ``href="…"`` / ``href='…'`` / ``src="…"`` / ``src='…'``
# - Markdown : ``](…)`` (lien inline)
#
# On capture l'URL à vérifier et on rejette uniquement celles ciblant
# ``caucrogegit.github.io/Forge``.
HTML_LINK_RE = re.compile(
    r"""(?P<attr>href|src)\s*=\s*['"](?P<url>[^'"]*caucrogegit\.github\.io/Forge[^'"]*)['"]""",
    re.IGNORECASE,
)
MD_LINK_RE = re.compile(
    r"""\]\((?P<url>[^)\s]*caucrogegit\.github\.io/Forge[^)\s]*)\)""",
)


def is_excluded(path: Path) -> bool:
    rel = path.resolve().relative_to(ROOT).as_posix()
    return any(rel.startswith(prefix) for prefix in EXCLUDED_PATHS)


def iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for target in SCAN_TARGETS:
        if not target.exists():
            continue
        for p in target.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in SCANNED_EXTENSIONS:
                continue
            if is_excluded(p):
                continue
            files.append(p)
    return sorted(files)


def find_violations(path: Path) -> list[tuple[int, str, str]]:
    """Retourne ``[(lineno, type, url), ...]`` pour les liens actifs interdits."""
    text = path.read_text(encoding="utf-8", errors="replace")
    hits: list[tuple[int, str, str]] = []
    for match in HTML_LINK_RE.finditer(text):
        url = match.group("url")
        lineno = text.count("\n", 0, match.start()) + 1
        hits.append((lineno, f"html:{match.group('attr')}", url))
    if path.suffix.lower() == ".md":
        for match in MD_LINK_RE.finditer(text):
            url = match.group("url")
            lineno = text.count("\n", 0, match.start()) + 1
            hits.append((lineno, "md:link", url))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Échoue si la landing ou la documentation du site officiel "
            "référence caucrogegit.github.io/Forge dans un lien actif."
        )
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="N'affiche pas la liste des fichiers scannés.",
    )
    args = parser.parse_args()

    files = iter_scanned_files()
    if not args.quiet:
        print(f"Périmètre : {len(files)} fichier(s) HTML/MD audités.")
        print("Exclusions :")
        for ex in EXCLUDED_PATHS:
            print(f"  - {ex}")
        print()

    violations: list[tuple[Path, int, str, str]] = []
    for path in files:
        for lineno, kind, url in find_violations(path):
            violations.append((path, lineno, kind, url))

    if violations:
        print("ERREUR : liens internes vers caucrogegit.github.io/Forge détectés :")
        for path, lineno, kind, url in violations:
            rel = path.resolve().relative_to(ROOT).as_posix()
            print(f"  {rel}:{lineno} [{kind}] {url}")
        print()
        print(
            "Règle : le site officiel forgemvc.com doit cibler /docs/forge/... "
            "(ou https://forgemvc.com/docs/forge/...) pour sa documentation interne."
        )
        return 1

    print("OK — aucun lien interne actif vers caucrogegit.github.io/Forge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
