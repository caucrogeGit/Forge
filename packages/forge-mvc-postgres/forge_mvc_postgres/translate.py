# pyright: strict
"""Traduction des paramètres SQL Forge (« ? ») vers le format psycopg (« %s »).

Forge génère du SQL avec des paramètres positionnels « ? » (compatibles MariaDB
et SQLite). psycopg utilise le format « %s » et interprète « % » comme un
marqueur de format : tout « % » littéral doit donc être doublé en « %% ».

Règles :
- « ? » hors d'un littéral chaîne devient « %s » ;
- « % » devient « %% » partout (psycopg formate la requête entière) ;
- les littéraux chaîne (entre apostrophes, avec '' comme apostrophe échappée)
  sont préservés, sauf le doublement des « % ».
"""
from __future__ import annotations


def translate_placeholders(sql: str) -> str:
    out: list[str] = []
    in_string = False
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if in_string:
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("''")
                    i += 2
                    continue
                in_string = False
                out.append(ch)
            elif ch == "%":
                out.append("%%")
            else:
                out.append(ch)
            i += 1
        else:
            if ch == "'":
                in_string = True
                out.append(ch)
            elif ch == "?":
                out.append("%s")
            elif ch == "%":
                out.append("%%")
            else:
                out.append(ch)
            i += 1
    return "".join(out)
