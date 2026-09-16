#!/usr/bin/env python3
# pyright: strict
"""tools/reflow_docs.py : reformate des pages Markdown en une phrase par ligne.

La documentation Forge est rendue avec l'extension MkDocs **nl2br** : chaque
retour à la ligne de la source devient un `<br>` au rendu. La convention (voir
`CLAUDE.md`, section « Gestion des phrases ») est donc **une phrase = une ligne
source**, une nouvelle phrase repartant à la ligne. Ce script applique cette
règle à des fichiers existants qui coupent encore les phrases au milieu.

Règles :

- coupe uniquement aux vraies fins de phrase (`.`, `!`, `?`, éventuellement
  suivis d'un fermant), jamais après `:` ni `;`, ni après un guillemet fermant
  seul, qui clôt une citation le plus souvent au milieu de la phrase ;
- rejoint les phrases coupées en plein milieu ;
- dans le doute, ne coupe pas : une coupure fautive se voit au rendu, deux
  phrases laissées sur une ligne ne se voient pas. D'où trois refus : devant ce
  qui ne commence pas une phrase (minuscule, ponctuation, tiret), après un numéro
  en tête de phrase, et quand la ligne créée ouvrirait une structure Markdown
  (liste, titre, citation) ;
- préserve ce dont la structure du document dépend : blocs de code (``` et ~~~,
  imbriqués compris), blocs HTML bruts (`<style>`, `<script>`, `<pre>`,
  `<textarea>`), blocs `$$`, tableaux, titres, séparateurs, en-têtes
  d'admonition et d'onglet, images, attributs `{ }`, listes de définitions et
  leurs termes, définitions d'abréviation, de note et de lien, marqueurs de
  liste sans contenu ;
- reformate le contenu d'une citation comme une page, préfixe « > » et
  indentation conservés : paragraphes et blocs de code y restent distincts ;
- ouvre une nouvelle ligne à chaque champ d'un bloc de champs (`**Date** :` suivi
  de `**Ticket** :`), sans l'empêcher de reprendre sa propre valeur coupée ;
- préserve les **espaces insécables** (U+00A0, U+202F) de la typographie
  française : seul l'espace ASCII est normalisé.

Ne modifie jamais un mot : seuls les retours à la ligne bougent.
Ce n'est pas une garantie suffisante, et c'est ce qui avait masqué les défauts
corrigés par `TOOLS-REFLOW-DOCS-FIABILITE-001` : coller deux phrases ou couper
au milieu d'une citation ne change aucun caractère non plus.

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
# « etc. » n'y figure pas : en fin de phrase il absorbe le point final, et suivi
# d'une majuscule il termine donc presque toujours la phrase.
_ABBR: tuple[str, ...] = (
    "p. ex.", "c.-à-d.", "i.e.", "e.g.", "ex.", "cf.", "Cf.", "vs.",
    "M.", "Mme.", "MM.", "al.", "no.", "réf.", "art.", "fig.", "env.",
)
# Reconnues comme mots entiers seulement : « al. » ne doit pas capter « local. ».
_ABBR_RE = re.compile(
    r"(?<![\w.-])(?:"
    + "|".join(re.escape(abbr) for abbr in sorted(_ABBR, key=len, reverse=True))
    + ")"
)

# Sentinelles (zone à usage privé Unicode, absentes des documents).
_DOT = "\uE000"   # point protégé (abréviation, décimal)
_ELL = "\uE001"   # ellipse « ... »
_C0 = "\uE002"    # début d'un span de code masqué
_C1 = "\uE003"    # fin d'un span de code masqué

_LIST = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
# Fin de phrase : `.`, `!` ou `?`, suivi de fermants éventuels (parenthèse,
# guillemet droit, emphase, guillemet français précédé ou non d'une insécable).
_END = re.compile(r"[.!?](?:[)\"*_]|[\u00a0\u202f]?»)*")
_DECIMAL = re.compile(r"(\d)\.(\d)")
_INLINE_CODE = re.compile(r"`[^`]*`")
_ASCII_WS = re.compile(r"[ \t\r\n\f\v]+")
# Numérotation en tête de phrase (« 3. », « **3. ») : pas une fin de phrase.
_TRAILING_NUMBER = re.compile(r"(?:\*\*|__|\*|_)?\d+\Z")
_ENDS_SENTENCE = re.compile(r"[.!?](?:[)\"*_]|[\u00a0\u202f]?»)*\Z")
# Débuts de ligne qui ouvriraient une structure si une coupure les y plaçait.
_BLOCK_START = re.compile(r"#{1,6}\s|>|[-*+]\s|\d+[.)]\s|!!!|\?\?\?|===|:\s|<|\|")

_FENCE_OPEN = re.compile(r"[ \t]*(`{3,}|~{3,})[^`]*")
_FENCE_CLOSE = re.compile(r"[ \t]*(`{3,}|~{3,})[ \t]*")
_RAW_HTML = re.compile(r"[ \t]*<(script|pre|style|textarea)(?=[\s>]|\Z)", re.IGNORECASE)
_RULE = re.compile(r"-{3,}|\*{3,}|_{3,}")
# Marqueur de liste sans contenu (« 1. » seul) : joint à la ligne suivante, il
# ouvrirait une liste imbriquée.
_EMPTY_ITEM = re.compile(r"(?:[-*+]|\d+[.)])")
# Indentation libre : dans une admonition, le contenu est lu une fois désindenté.
_DEFINITION = re.compile(r"[ \t]*:[ \t]+\S.*")
_LINK_DEFINITION = re.compile(r"[ \t]*\[[^\]]+\]:[ \t]+\S.*")
_FIELD = re.compile(
    r"[ \t]*\*\*[^*]{1,40}?(?:\*\*[ \t\u00a0\u202f]*:|[ \t\u00a0\u202f]*:\*\*)"
    r"(?:[ \t\u00a0\u202f].*)?"
)
_STRUCTURAL_STARTS: tuple[str, ...] = (
    "#", "|", "<", "!!!", "???", "![", "*[", "[^", "===", "{", "$$",
)


def _starts_sentence(text: str) -> bool:
    """Vrai si `text` peut commencer une phrase.

    Liste positive : une minuscule, « ; », « , » ou un tiret ne commencent pas une
    phrase, et une question en incise (« (voir ?) ou ») ne doit pas être coupée.
    """
    first = text[0]
    return first.isupper() or first.isdigit() or first in "«(\"*_" + _C0


def _numbering(head: str) -> bool:
    """Vrai si `head` finit par un numéro placé en tête de phrase."""
    number = _TRAILING_NUMBER.search(head)
    if number is None:
        return False
    before = head[:number.start()].rstrip(" ")
    return not before or _ENDS_SENTENCE.search(before) is not None


def resplit(text: str) -> list[str]:
    """Rejoint `text` puis le découpe en phrases (une par élément)."""
    text = _ASCII_WS.sub(" ", text).strip(" \t\r\n\f\v")
    if not text:
        return []

    codes: list[str] = []

    def _mask(match: re.Match[str]) -> str:
        codes.append(match.group(0))
        return _C0 + str(len(codes) - 1) + _C1

    def _restore(sentence: str) -> str:
        sentence = sentence.replace(_ELL, "...").replace(_DOT, ".")
        for index, code in enumerate(codes):
            sentence = sentence.replace(_C0 + str(index) + _C1, code)
        return sentence

    text = _INLINE_CODE.sub(_mask, text)
    text = _ABBR_RE.sub(lambda m: m.group(0).replace(".", _DOT), text)
    text = _DECIMAL.sub(lambda m: m.group(1) + _DOT + m.group(2), text)
    text = text.replace("...", _ELL)

    sentences: list[str] = []
    start = 0
    for match in _END.finditer(text):
        rest = text[match.end():]
        following = rest.lstrip(" ")
        if not following or following == rest:
            continue
        if not _starts_sentence(following):
            continue
        if _BLOCK_START.match(following):
            continue
        if _numbering(text[:match.start()]):
            continue
        sentences.append(text[start:match.end()])
        start = match.end() + (len(rest) - len(following))
    sentences.append(text[start:])
    return [_restore(sentence) for sentence in sentences if sentence.strip()]


def _structural(line: str) -> bool:
    """Vrai si la ligne porte à elle seule une structure Markdown."""
    stripped = line.strip()
    if stripped.startswith(_STRUCTURAL_STARTS):
        return True
    if _RULE.fullmatch(stripped) or _EMPTY_ITEM.fullmatch(stripped):
        return True
    if _DEFINITION.fullmatch(line) or _LINK_DEFINITION.fullmatch(line):
        return True
    return stripped.count("|") >= 2


def _frozen(lines: list[str]) -> list[bool]:
    """Marque les lignes à laisser telles quelles : la structure en dépend."""
    frozen = [False] * len(lines)
    fence: str | None = None
    raw_tag: str | None = None
    math = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if fence is not None:
            frozen[index] = True
            close = _FENCE_CLOSE.fullmatch(line)
            if close is not None:
                marker = close.group(1)
                if marker[0] == fence[0] and len(marker) >= len(fence):
                    fence = None
            continue
        if raw_tag is not None:
            frozen[index] = True
            if f"</{raw_tag}" in line.lower():
                raw_tag = None
            continue
        if math:
            frozen[index] = True
            if stripped.endswith("$$"):
                math = False
            continue
        opening = _FENCE_OPEN.fullmatch(line)
        if opening is not None:
            frozen[index] = True
            fence = opening.group(1)
            continue
        raw = _RAW_HTML.match(line)
        if raw is not None:
            frozen[index] = True
            tag = raw.group(1).lower()
            if f"</{tag}" not in line.lower():
                raw_tag = tag
            continue
        if stripped == "$$":
            frozen[index] = True
            math = True
            continue
        if stripped:
            frozen[index] = _structural(line)

    # Deuxième passe : le terme d'une définition dépend de la ligne qui le suit.
    for index, line in enumerate(lines[:-1]):
        if not frozen[index] and line.strip() and _DEFINITION.fullmatch(lines[index + 1]):
            frozen[index] = True
    return frozen


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def reflow(src: str) -> str:
    """Retourne `src` reformaté en une phrase par ligne."""
    lines = src.split("\n")
    frozen = _frozen(lines)
    # Une ligne de champ ouvre toujours un bloc : `**Date** :` puis `**Ticket** :`
    # restent sur deux lignes, et la valeur coupée d'un champ se rejoint.
    field = [_FIELD.fullmatch(line) is not None for line in lines]
    out: list[str] = []
    i = 0
    n = len(lines)

    def _stops(j: int) -> bool:
        """Vrai si la ligne `j` ne peut pas prolonger le bloc en cours."""
        nxt = lines[j]
        return (
            frozen[j]
            or field[j]
            or not nxt.strip()
            or _LIST.fullmatch(nxt) is not None
            or nxt.lstrip().startswith(">")
        )

    while i < n:
        line = lines[i]
        if frozen[i] or not line.strip():
            out.append(line)
            i += 1
            continue

        stripped = line.lstrip()
        indent = _indent(line)

        # Citation : son contenu est une page à part entière (paragraphes, code,
        # listes). Préfixe retiré, contenu reformaté par les mêmes règles, préfixe
        # remis à la même indentation, pour rester dans l'admonition qui la porte.
        if stripped.startswith(">"):
            inner: list[str] = []
            while (
                i < n
                and not frozen[i]
                and _indent(lines[i]) == indent
                and lines[i].lstrip().startswith(">")
            ):
                content = lines[i].lstrip()[1:]
                inner.append(content[1:] if content.startswith(" ") else content)
                i += 1
            for quoted in reflow("\n".join(inner)).split("\n"):
                out.append(" " * indent + ("> " + quoted if quoted.strip() else ">"))
            continue

        # Item de liste : marqueur + continuation indentée.
        match = _LIST.fullmatch(line)
        if match is not None:
            marker_indent, marker, first = match.group(1), match.group(2), match.group(3)
            content_indent = len(marker_indent) + len(marker) + 1
            item: list[str] = [first]
            i += 1
            while i < n and not _stops(i) and _indent(lines[i]) >= content_indent:
                item.append(lines[i].strip())
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
        while i < n and not _stops(i) and _indent(lines[i]) == indent:
            para.append(lines[i].strip())
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
