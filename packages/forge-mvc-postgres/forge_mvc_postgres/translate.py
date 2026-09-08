# pyright: strict
"""Traduction des paramètres SQL Forge (« ? ») vers le format psycopg (« %s »).

Forge génère du SQL avec des paramètres positionnels « ? » (compatibles MariaDB
et SQLite). psycopg utilise le format « %s » et interprète « % » comme un
marqueur de format : tout « % » littéral doit donc être doublé en « %% ».

Règles :
- « ? » **dans du code** devient « %s » ;
- « % » devient « %% » partout (psycopg formate la requête entière) ;
- les contextes qui ne sont pas du code sont préservés tels quels, au
  doublement des « % » près.

Ce qui n'est pas du code
------------------------
`POSTGRES-TRANSLATE-CONTEXTES-001`. La traduction ne connaissait que les
littéraux entre apostrophes. Mesuré, elle introduisait des marqueurs là où le
« ? » n'était pas un paramètre :

    SELECT ? /* pourquoi ? */   ->  SELECT %s /* pourquoi %s */
    SELECT $$?$$                ->  SELECT $$%s$$
    SELECT ? -- et ?            ->  SELECT %s -- et %s
    SELECT "col?" FROM t        ->  SELECT "col%s" FROM t

Selon le pilote, cela donne un mauvais comptage des paramètres ou un SQL altéré.
Les requêtes engendrées par Forge, simples, passaient ; du SQL applicatif
parfaitement valide échouait. C'est un défaut de compatibilité pour un framework
qui laisse écrire du SQL (principe 5).

Quatre contextes sont désormais reconnus, tous préservés : le littéral
`'...'` avec `''`, l'identifiant `"..."` avec `""`, le commentaire `-- ...` et
`/* ... */` (imbriqué, comme PostgreSQL l'admet), et le littéral encadré par
dollars `$$...$$` ou `$étiquette$...$étiquette$`.

L'opérateur qui commence par « ? »
----------------------------------
PostgreSQL a des opérateurs contenant « ? » : `?` , `?|` et `?&` sur `jsonb`,
et plusieurs opérateurs géométriques. Les distinguer d'un paramètre demanderait
d'analyser la grammaire, pas seulement le lexique.

Forge tranche par une règle **écrite** plutôt que par une devinette : un « ? »
suivi immédiatement d'un autre caractère d'opérateur (`|`, `&`, `-`, `#`) n'est
pas un paramètre, un paramètre étant toujours suivi d'un séparateur. Et `??`
vaut un « ? » littéral, échappement que psycopg emploie déjà dans le même but.

Reste le `?` isolé de `jsonb`, indiscernable d'un paramètre : il s'écrit `??`.
"""
from __future__ import annotations

#: Caractères qui, collés à un « ? », en font un opérateur PostgreSQL.
_SUITE_D_OPERATEUR = "|&-#"


def translate_placeholders(sql: str) -> str:
    """Rend `sql` avec ses paramètres « ? » traduits en « %s »."""
    out: list[str] = []
    i = 0
    n = len(sql)
    profondeur_bloc = 0

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""

        # -- Commentaire de bloc, imbricable ---------------------------------
        if profondeur_bloc:
            if ch == "/" and nxt == "*":
                profondeur_bloc += 1
                out.append("/*")
                i += 2
                continue
            if ch == "*" and nxt == "/":
                profondeur_bloc -= 1
                out.append("*/")
                i += 2
                continue
            out.append("%%" if ch == "%" else ch)
            i += 1
            continue

        # -- Littéral chaîne -------------------------------------------------
        if ch == "'":
            i = _copier_jusqu_a(sql, i, out, "'")
            continue

        # -- Identifiant cité ------------------------------------------------
        if ch == '"':
            i = _copier_jusqu_a(sql, i, out, '"')
            continue

        # -- Commentaire de ligne --------------------------------------------
        if ch == "-" and nxt == "-":
            fin = sql.find("\n", i)
            fin = n if fin == -1 else fin
            out.append(sql[i:fin].replace("%", "%%"))
            i = fin
            continue

        # -- Commentaire de bloc ---------------------------------------------
        if ch == "/" and nxt == "*":
            profondeur_bloc = 1
            out.append("/*")
            i += 2
            continue

        # -- Littéral encadré par dollars ------------------------------------
        marque = _marque_dollar(sql, i)
        if marque is not None:
            fin = sql.find(marque, i + len(marque))
            fin = n if fin == -1 else fin + len(marque)
            out.append(sql[i:fin].replace("%", "%%"))
            i = fin
            continue

        # -- Code --------------------------------------------------------------
        if ch == "?":
            if nxt == "?":  # échappement : un « ? » littéral
                out.append("?")
                i += 2
                continue
            # `nxt` vaut "" en fin de chaîne, et `"" in "|&-#"` est vrai :
            # sans le premier test, un « ? » final passerait pour un opérateur.
            if nxt and nxt in _SUITE_D_OPERATEUR:
                out.append("?")
                i += 1
                continue
            out.append("%s")
            i += 1
            continue
        out.append("%%" if ch == "%" else ch)
        i += 1

    return "".join(out)


def _copier_jusqu_a(sql: str, debut: int, out: "list[str]", delimiteur: str) -> int:
    """Copie un littéral ou un identifiant cité, et rend l'index de sa fin.

    Le délimiteur doublé (`''` ou `""`) est un caractère du contenu, pas une
    fin. Un délimiteur jamais refermé fait copier jusqu'au bout plutôt que
    lever : ce module traduit, il ne valide pas, et un SQL invalide doit être
    refusé par le serveur avec son message à lui.
    """
    n = len(sql)
    out.append(delimiteur)
    i = debut + 1
    while i < n:
        ch = sql[i]
        if ch == delimiteur:
            if i + 1 < n and sql[i + 1] == delimiteur:
                out.append(delimiteur * 2)
                i += 2
                continue
            out.append(delimiteur)
            return i + 1
        out.append("%%" if ch == "%" else ch)
        i += 1
    return i


def _marque_dollar(sql: str, debut: int) -> "str | None":
    """Rend `$$` ou `$étiquette$` si une telle marque commence ici, sinon `None`.

    L'étiquette suit les règles d'un identifiant PostgreSQL : elle ne commence
    pas par un chiffre. Sans cela, `$1$` d'un paramètre numéroté serait pris
    pour l'ouverture d'un littéral.
    """
    if sql[debut] != "$":
        return None
    i = debut + 1
    n = len(sql)
    while i < n and (sql[i].isalnum() or sql[i] == "_"):
        i += 1
    if i >= n or sql[i] != "$":
        return None
    etiquette = sql[debut + 1:i]
    if etiquette[:1].isdigit():
        return None
    return sql[debut:i + 1]
