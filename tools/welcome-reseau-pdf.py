#!/usr/bin/env python3
# pyright: strict
"""Génère des PDF A4 des fichiers TÉLÉCHARGEABLES du starter welcome-réseau.

Support temporaire (2TNE CIEL), sans lien avec le framework Forge — à retirer
avec docs/starters-pedagogique/ le 2026-06-28.

Le markdown des fichiers à télécharger (QCM, activité, checklist élève, corrigé
professeur) ne s'ouvre pas correctement côté navigateur : on en produit une copie
PDF lisible/imprimable, posée à côté du .md. Le dossier technique et les index
restent en HTML, rendus par forgemvc.com.

Usage :
    python tools/welcome-reseau-pdf.py            # tous les fichiers téléchargeables
    python tools/welcome-reseau-pdf.py <fichier.md ...>   # ciblé
"""
from __future__ import annotations

from typing import Any, cast

import sys
from pathlib import Path

import markdown
import weasyprint  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

ROOT = Path(__file__).resolve().parent.parent
STARTER = ROOT / "docs" / "starters-pedagogique" / "welcome-reseau"

# Fichiers téléchargeables, par convention : eleve/{qcm,activite,checklist} +
# professeur/{corrige}. Le dossier technique et l'index n'ont PAS de PDF.
DOWNLOADABLE_GLOBS = (
    "palier-*/eleve/qcm-*.md",
    "palier-*/eleve/activite-*.md",
    "palier-*/eleve/checklist-*.md",
    "palier-*/professeur/*-corrige.md",
)

CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: "DejaVu Sans", "Liberation Sans", sans-serif; font-size: 11pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 20pt; color: #b34700; margin: 0 0 0.6em; }
h2 { font-size: 15pt; color: #b34700; margin: 1.1em 0 0.4em;
     border-bottom: 1px solid #e0e0e0; padding-bottom: 0.2em; }
h3 { font-size: 12.5pt; margin: 0.9em 0 0.3em; }
table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
th, td { border: 1px solid #999; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f2f2f2; }
code { background: #f4f4f4; padding: 1px 4px; border-radius: 3px;
       font-family: "DejaVu Sans Mono", monospace; font-size: 10pt; }
pre { background: #f4f4f4; padding: 8px 10px; border-radius: 4px; overflow-wrap: anywhere; }
pre code { background: none; padding: 0; }
ul, ol { margin: 0.3em 0 0.6em 1.4em; }
"""

EXTENSIONS = ["tables", "fenced_code", "sane_lists", "attr_list", "nl2br"]


def md_to_pdf(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=EXTENSIONS)
    html = (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    pdf_path = md_path.with_suffix(".pdf")
    cast("Any", weasyprint).HTML(string=html, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    return pdf_path


def _targets(args: list[str]) -> list[Path]:
    if args:
        return [Path(a).resolve() for a in args]
    found: list[Path] = []
    for pattern in DOWNLOADABLE_GLOBS:
        found.extend(sorted(STARTER.glob(pattern)))
    return found


def main(argv: list[str]) -> int:
    targets = _targets(argv)
    if not targets:
        print("Aucun fichier téléchargeable trouvé.")
        return 1
    for md in targets:
        if not md.exists():
            print(f"[SKIP] introuvable : {md}")
            continue
        pdf = md_to_pdf(md)
        print(f"[OK] {pdf.relative_to(ROOT)} ({pdf.stat().st_size} octets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
