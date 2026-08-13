# pyright: strict
"""Instant canonique des horodatages gérés (ADR-081, `TIMESTAMPS-NAIVE-UTC-001`).

L'ADR-081 a tranché que l'autorité sur les horodatages est **Python**, jamais le
moteur. Il n'avait pas dit sous quelle **forme** la valeur devait être passée,
et cette omission a coûté deux heures.

## Ce que mesure ce module

Les colonnes d'horodatage de Forge sont des `DATETIME` **sans fuseau**. Passer
un `datetime` conscient du fuseau y laisse donc le pilote décider de la
conversion, et chaque pilote décide autrement. Mesuré sur serveurs réels, avec
un serveur en UTC+2 :

    mariadb     aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)
    postgres    aware -> 14:14:07  (écart 7200 s)   naïf -> 12:14:07  (0 s)
    mssql       aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)

PostgreSQL convertit vers l'heure locale du serveur, les deux autres non. Une
base pouvait donc porter deux référentiels horaires selon le backend, sans que
rien ne le signale : la valeur est plausible, seulement fausse de deux heures.

## La règle

**Un `datetime` naïf, en UTC.** C'est ce que rend `utc_now()`, et c'est la seule
façon officielle de produire un horodatage géré (principe 11).

Écrire `datetime.now(timezone.utc)` directement est le piège : la forme paraît
plus juste que sa version naïve, puisqu'elle porte l'information de fuseau. Elle
l'est en Python, elle ne l'est pas au passage du pilote.
"""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["utc_now"]


def utc_now() -> datetime:
    """Instant présent en UTC, **sans fuseau attaché**.

    À employer pour toute colonne d'horodatage géré : `created_at`,
    `updated_at`, `deleted_at`, et leurs équivalents dans les opt-ins.

    Le `replace(tzinfo=None)` n'est pas une perte d'information : la valeur
    reste de l'UTC, et c'est la convention de toutes les colonnes de Forge.
    L'attacher ferait décider le pilote, ce qui donne un résultat différent
    selon le backend.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
