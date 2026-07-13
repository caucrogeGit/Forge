# pyright: strict
"""core/database/sql_script.py — Découpage canonique d'un script SQL (ADR-079).

Découpe un script multi-instructions en instructions individuelles sur les ``;``,
en respectant les **littéraux** (`'...'` avec échappement `''`) et les
**commentaires** (`-- ligne`, `/* bloc */`) : un ``;`` à l'intérieur d'une chaîne
ou d'un commentaire n'est pas un séparateur. Les commentaires sont retirés des
instructions produites (remplacés par une espace, pour ne pas coller deux tokens).

Source unique consommée par `migration:apply` / `db:apply` (forge-mvc-entities) et
`fixtures:load` (forge-mvc-fixtures) : une seule façon officielle (principe 11),
fiabilisée après les retours terrain 012 (apostrophe) et 021 (commentaire).
"""
from __future__ import annotations

_NORMAL = "normal"
_QUOTE = "quote"
_LINE_COMMENT = "line_comment"
_BLOCK_COMMENT = "block_comment"


def split_sql_statements(sql: str) -> list[str]:
    """Découpe ``sql`` en instructions, sur les ``;`` de premier niveau.

    Respecte les chaînes ``'...'`` (échappement ``''``), les commentaires de ligne
    ``-- ...`` et de bloc ``/* ... */``. Les commentaires sont retirés ; les
    instructions vides (ou uniquement commentaire/espace) sont ignorées.
    """
    statements: list[str] = []
    current: list[str] = []
    has_content = False
    state = _NORMAL
    index = 0
    length = len(sql)

    while index < length:
        char = sql[index]
        nxt = sql[index + 1] if index + 1 < length else ""

        if state == _NORMAL:
            if char == "'":
                state = _QUOTE
                current.append(char)
                has_content = True
            elif char == "-" and nxt == "-":
                state = _LINE_COMMENT
                index += 2
                continue
            elif char == "/" and nxt == "*":
                state = _BLOCK_COMMENT
                index += 2
                continue
            elif char == ";":
                if has_content:
                    statement = "".join(current).strip()
                    if statement:
                        statements.append(statement)
                current = []
                has_content = False
            else:
                if not char.isspace():
                    has_content = True
                current.append(char)
            index += 1
            continue

        if state == _QUOTE:
            current.append(char)
            if char == "'":
                if nxt == "'":  # échappement SQL standard
                    current.append(nxt)
                    index += 2
                    continue
                state = _NORMAL
            index += 1
            continue

        if state == _LINE_COMMENT:
            if char == "\n":
                current.append("\n")  # séparateur de tokens conservé
                state = _NORMAL
            index += 1
            continue

        # _BLOCK_COMMENT
        if char == "*" and nxt == "/":
            current.append(" ")  # séparateur de tokens
            state = _NORMAL
            index += 2
            continue
        index += 1

    if has_content:
        statement = "".join(current).strip()
        if statement:
            statements.append(statement)
    return statements
