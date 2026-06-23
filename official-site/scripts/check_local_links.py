#!/usr/bin/env python3
"""Vérification locale des liens internes d'un site statique.

Parcourt récursivement les fichiers HTML d'un dossier (par défaut ``dist/``),
extrait les attributs ``href`` et ``src``, et vérifie que chaque cible locale
résolue existe sur le système de fichiers.

- Ignore les URL ``http://``, ``https://``, ``mailto:``, ``tel:``, ``data:``,
  ``javascript:``, ``#ancre``.
- Tolère les liens "dossier" (``/docs/``) en cherchant ``index.html``.
- Tolère les fragments (``#section``).
- Retourne le code de sortie 0 si tout est OK, 1 si au moins un lien casse.
"""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript", "ftp"}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value and name in {"href", "src"}:
                self.urls.append(value)


def extract_links(html_path: Path) -> list[str]:
    parser = LinkExtractor()
    try:
        parser.feed(html_path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        print(f"warn: échec parsing {html_path}: {exc}", file=sys.stderr)
        return []
    return parser.urls


def resolve_target(root: Path, html_path: Path, url: str) -> Path | None:
    """Retourne le chemin filesystem ciblé par ``url`` depuis ``html_path``.

    Retourne ``None`` si l'URL doit être ignorée.
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES:
        return None
    raw_path = unquote(parsed.path)
    if not raw_path:
        # URL purement ancre : "#xyz"
        return None
    if raw_path.startswith("/"):
        target = root / raw_path.lstrip("/")
    else:
        target = (html_path.parent / raw_path).resolve()
    # URL "dossier" → résoudre vers index.html.
    if raw_path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vérifie les liens internes d'un site statique."
    )
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=Path("dist"),
        help="Racine du site statique (défaut: dist).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="N'affiche pas le résumé par fichier.",
    )
    args = parser.parse_args()
    root: Path = args.root.resolve()

    if not root.is_dir():
        print(f"erreur: racine introuvable: {root}", file=sys.stderr)
        return 2

    html_files = sorted(root.rglob("*.html"))
    if not html_files:
        print(f"erreur: aucun .html sous {root}", file=sys.stderr)
        return 2

    total_links = 0
    total_external = 0
    broken: list[tuple[Path, str, Path]] = []
    checked_targets: set[Path] = set()

    for html in html_files:
        urls = extract_links(html)
        for url in urls:
            total_links += 1
            target = resolve_target(root, html, url)
            if target is None:
                total_external += 1
                continue
            # Vérifie que la cible est sous root (sinon : lien hors site).
            try:
                target.relative_to(root)
            except ValueError:
                broken.append((html, url, target))
                continue
            checked_targets.add(target)
            if not target.exists():
                broken.append((html, url, target))

    print(f"Racine          : {root}")
    print(f"Fichiers HTML   : {len(html_files)}")
    print(f"Liens analysés  : {total_links}")
    print(f"Liens externes  : {total_external}")
    print(f"Liens locaux    : {total_links - total_external}")
    print(f"Cibles uniques  : {len(checked_targets)}")
    print(f"Liens cassés    : {len(broken)}")

    if broken:
        print()
        print("Détail des liens cassés :")
        for html, url, target in broken:
            html_rel = html.relative_to(root)
            try:
                target_rel = target.relative_to(root)
                target_disp = str(target_rel)
            except ValueError:
                target_disp = f"(hors site) {target}"
            print(f"  {html_rel}: '{url}' → {target_disp}")
        return 1

    print()
    print("OK — aucun lien local cassé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
