#!/usr/bin/env python3
# pyright: strict
"""tools/reflow_docs.py — reformate des pages Markdown en une phrase par ligne.

La documentation Forge est rendue avec l'extension MkDocs **nl2br** : chaque
retour à la ligne de la source devient un `<br>` au rendu. La convention (voir
`CLAUDE.md`, section « Gestion des phrases ») est donc **une phrase = une ligne
source**, une nouvelle phrase repartant à la ligne. Ce script applique cette
règle à des fichiers existants qui coupent encore les phrases au milieu.

Règles :

- coupe uniquement aux vraies fins de phrase (`.`, `!`, `?`, `»`), jamais après
  `:` ni `;` (ils introduisent une suite dans la même phrase) ;
- rejoint les phrases coupées en plein milieu ;
- préserve les blocs de code ```, les tableaux `|`, les titres `#`, les
  séparateurs `---`, le HTML, les en-têtes d'admonition `!!!`/`???`, les images,
  les lignes vides, les citations `>`, les items de liste et leur continuation,
  le contenu indenté d'admonition ;
- préserve les **espaces insécables** (U+00A0, U+202F) de la typographie
  française : seul l'espace ASCII est normalisé.

Ne modifie jamais un mot : seuls les retours à la ligne bougent.

Usage :

    python tools/reflow_docs.py docs/foo.md docs/bar.md   # reformate en place
    python tools/reflow_docs.py --check docs/foo.md        # signale sans écrire

`--check` retourne 1 si au moins un fichier serait modifié (utile en CI ou en
pre-commit), 0 sinon.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Abréviations dont le point ne termine pas une phrase.
_ABBR: list[str] = [
    "p. ex.", "c.-à-d.", "i.e.", "e.g.", "etc.", "ex.", "cf.", "vs.",
    "M.", "Mme.", "MM.", "al.", "no.", "réf.", "art.", "fig.", "env.",
]

# Sentinelles (zone à usage privé Unicode, absentes des documents).
_DOT = "\uE000"   # point protégé (abréviation, décimal)
_ELL = "\uE001"   # ellipse « ... »
_C0 = "\uE002"    # début d'un span de code masqué
_C1 = "\uE003"    # fin d'un span de code masqué

_LIST = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
_SPLIT = re.compile(r'([.!?»][)"»]*(?:\*\*)?)\s+(?=\S)')
_DECIMAL = re.compile(r"(\d)\.(\d)")
_INLINE_CODE = re.compile(r"`[^`]*`")
_ASCII_WS = re.compile(r"[ \t\r\n\f\v]+")


def resplit(text: str) -> list[str]:
    """Rejoint `text` puis le découpe en phrases (une par élément)."""
    text = _ASCII_WS.sub(" ", text).strip(" \t\r\n\f\v")
    if not text:
        return []

    codes: list[str] = []

    def _mask(match: re.Match[str]) -> str:
        codes.append(match.group(0))
        return _C0 + str(len(codes) - 1) + _C1

    text = _INLINE_CODE.sub(_mask, text)
    for abbr in _ABBR:
        text = text.replace(abbr, abbr.replace(".", _DOT))
    text = _DECIMAL.sub(lambda m: m.group(1) + _DOT + m.group(2), text)
    text = text.replace("...", _ELL)
    text = _SPLIT.sub(lambda m: m.group(1) + "\n", text)
    text = text.replace(_ELL, "...").replace(_DOT, ".")
    for index, code in enumerate(codes):
        text = text.replace(_C0 + str(index) + _C1, code)
    return [line for line in text.split("\n") if line.strip()]


def _verbatim(line: str, in_code: bool) -> bool:
    """Vrai si la ligne ne doit pas être reformatée (structure préservée)."""
    stripped = line.strip()
    if in_code or not stripped:
        return True
    if stripped[0] in "#|<":
        return True
    if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
        return True
    if stripped.startswith(("!!!", "???", "![")):
        return True
    if stripped.count("|") >= 2:
        return True
    return False


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def reflow(src: str) -> str:
    """Retourne `src` reformaté en une phrase par ligne."""
    lines = src.split("\n")
    out: list[str] = []
    in_code = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.lstrip().startswith("```"):
            out.append(line)
            in_code = not in_code
            i += 1
            continue
        if _verbatim(line, in_code):
            out.append(line)
            i += 1
            continue

        stripped = line.lstrip()
        indent = _indent(line)

        # Citation : réécrite en une phrase par ligne, préfixe « > » conservé.
        if stripped.startswith(">"):
            buf: list[str] = []
            while i < n and lines[i].lstrip().startswith(">") and not lines[i].lstrip().startswith("```"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            for sentence in resplit(" ".join(x.strip() for x in buf if x.strip())):
                out.append("> " + sentence)
            continue

        # Item de liste : marqueur + continuation indentée.
        match = _LIST.match(line)
        if match is not None:
            marker_indent, marker, first = match.group(1), match.group(2), match.group(3)
            content_indent = len(marker_indent) + len(marker) + 1
            item: list[str] = [first]
            i += 1
            while i < n:
                nxt = lines[i]
                if not nxt.strip() or nxt.lstrip().startswith("```"):
                    break
                if _verbatim(nxt, in_code) or _LIST.match(nxt) or nxt.lstrip().startswith(">"):
                    break
                if _indent(nxt) < content_indent:
                    break
                item.append(nxt.strip())
                i += 1
            sentences = resplit(" ".join(item))
            if sentences:
                out.append(marker_indent + marker + " " + sentences[0])
                for sentence in sentences[1:]:
                    out.append(" " * content_indent + sentence)
            else:
                out.append(line)
            continue

        # Paragraphe de prose (éventuellement indenté = contenu d'admonition).
        para: list[str] = [stripped]
        i += 1
        while i < n:
            nxt = lines[i]
            if not nxt.strip() or nxt.lstrip().startswith("```"):
                break
            if _verbatim(nxt, in_code) or _LIST.match(nxt) or nxt.lstrip().startswith(">"):
                break
            if _indent(nxt) != indent:
                break
            para.append(nxt.strip())
            i += 1
        for sentence in resplit(" ".join(para)):
            out.append(" " * indent + sentence)

    return "\n".join(out)


def _reflowed(path: Path) -> str:
    new = reflow(path.read_text(encoding="utf-8"))
    return new if new.endswith("\n") else new + "\n"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    paths = [Path(a) for a in args if a != "--check"]
    if not paths:
        print(__doc__)
        return 0

    changed = 0
    for path in paths:
        if not path.is_file():
            print(f"introuvable : {path}", file=sys.stderr)
            continue
        new = _reflowed(path)
        if new == path.read_text(encoding="utf-8"):
            continue
        changed += 1
        if check:
            print(f"à reformater : {path}")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"reformaté : {path}")

    if check and changed:
        print(f"{changed} fichier(s) à reformater (une phrase par ligne).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
