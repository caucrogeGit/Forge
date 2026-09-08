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


def mask_sql_literals(sql: str) -> str:
    """Rend `sql` avec les littéraux et commentaires remplacés par des espaces.

    `SQL-MASK-LITERALS-001`. Le découpage d'instructions respectait déjà les
    chaînes et les commentaires ; chercher un motif **dans** une instruction ne
    le faisait pas. Mesuré sur la purge de fixtures :

        INSERT INTO logs (message) VALUES ('INSERT INTO users');

    donnait un plan de purge portant `logs` **et** `users`, alors que
    l'instruction n'écrit que dans `logs`. Un garde-fou d'autorisation ne
    corrige pas un plan erroné : il autorise très correctement la mauvaise
    suppression.

    Le remplacement se fait caractère par caractère, ce qui **préserve les
    positions** : un motif appliqué sur le résultat pointe le même endroit que
    dans la source, et deux jetons voisins ne se collent pas.

    Les apostrophes délimitantes sont conservées, pour qu'une chaîne reste
    reconnaissable comme telle, son contenu seul étant effacé.

    Cette fonction vit à côté de `split_sql_statements` parce qu'elle répond à
    la même question, « où finit le code et où commence le texte », et qu'une
    seconde réponse écrite ailleurs finirait par diverger de celle-ci.
    """
    sortie: list[str] = []
    state = _NORMAL
    index = 0
    length = len(sql)

    while index < length:
        char = sql[index]
        nxt = sql[index + 1] if index + 1 < length else ""

        if state == _NORMAL:
            if char == "'":
                state = _QUOTE
                sortie.append(char)
            elif char == "-" and nxt == "-":
                state = _LINE_COMMENT
                sortie.append("  ")
                index += 2
                continue
            elif char == "/" and nxt == "*":
                state = _BLOCK_COMMENT
                sortie.append("  ")
                index += 2
                continue
            else:
                sortie.append(char)
            index += 1
            continue

        if state == _QUOTE:
            if char == "'":
                if nxt == "'":  # échappement SQL standard, toujours du contenu
                    sortie.append("  ")
                    index += 2
                    continue
                sortie.append(char)
                state = _NORMAL
            else:
                sortie.append("\n" if char == "\n" else " ")
            index += 1
            continue

        if state == _LINE_COMMENT:
            if char == "\n":
                sortie.append("\n")
                state = _NORMAL
            else:
                sortie.append(" ")
            index += 1
            continue

        # _BLOCK_COMMENT
        if char == "*" and nxt == "/":
            sortie.append("  ")
            state = _NORMAL
            index += 2
            continue
        sortie.append("\n" if char == "\n" else " ")
        index += 1

    return "".join(sortie)


def normalize_sql_whitespace(sql: str) -> str:
    """Réduit les blancs du **code** SQL, sans toucher au contenu des chaînes.

    `SQL-NORMALIZE-WHITESPACE-001`. Normaliser une instruction entière par
    `" ".join(sql.split())` sert une intention juste, ne pas faire dépendre une
    empreinte d'un reformatage, mais l'applique aussi à l'intérieur des
    littéraux. Mesuré sur le journal de reprise des migrations :

        INSERT INTO demo (value) VALUES ('a  b')
        INSERT INTO demo (value) VALUES ('a b')

    donnaient la **même** empreinte, alors qu'elles n'écrivent pas la même
    valeur. Une reprise pouvait donc considérer comme déjà exécutée une étape
    dont un littéral avait changé, et un outil de migration doit être
    particulièrement conservateur quand il décide qu'une étape a eu lieu.

    Les commentaires sont traités comme du blanc : le découpeur canonique les
    ôte déjà, et les rencontrer ici ne doit pas produire une empreinte
    différente.
    """
    sortie: list[str] = []
    state = _NORMAL
    index = 0
    length = len(sql)
    blanc_en_attente = False

    def poser_blanc() -> None:
        nonlocal blanc_en_attente
        if blanc_en_attente and sortie:
            sortie.append(" ")
        blanc_en_attente = False

    while index < length:
        char = sql[index]
        nxt = sql[index + 1] if index + 1 < length else ""

        if state == _NORMAL:
            if char == "'":
                poser_blanc()
                state = _QUOTE
                sortie.append(char)
            elif char == "-" and nxt == "-":
                state = _LINE_COMMENT
                blanc_en_attente = True
                index += 2
                continue
            elif char == "/" and nxt == "*":
                state = _BLOCK_COMMENT
                blanc_en_attente = True
                index += 2
                continue
            elif char.isspace():
                blanc_en_attente = True
            else:
                poser_blanc()
                sortie.append(char)
            index += 1
            continue

        if state == _QUOTE:
            sortie.append(char)
            if char == "'":
                if nxt == "'":  # échappement SQL standard
                    sortie.append(nxt)
                    index += 2
                    continue
                state = _NORMAL
            index += 1
            continue

        if state == _LINE_COMMENT:
            if char == "\n":
                state = _NORMAL
            index += 1
            continue

        # _BLOCK_COMMENT
        if char == "*" and nxt == "/":
            state = _NORMAL
            index += 2
            continue
        index += 1

    return "".join(sortie)
