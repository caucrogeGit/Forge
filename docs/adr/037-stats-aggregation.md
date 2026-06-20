# ADR-037 — Agrégation par comptage dans `forge-mvc-stats`

## Statut

Accepté — Forge 1.0.0-beta.17 (ticket `STATS-AGGREGATION-001`).

---

## Date

2026-06-20

---

## Contexte

`forge-mvc-stats` se présentait comme un module d'« agrégats statistiques
(compteurs, fenêtres temporelles) », mais son code ne fournissait qu'un
**journal d'événements** : insertion ligne à ligne (`track_event`) et lecture
filtrée paginée (`list_stats_events`). Aucune agrégation (`COUNT`, `GROUP BY`)
n'existait. L'écart entre la promesse affichée et l'API livrée contrevenait au
principe 10 (une API publique est un contrat de complétude).

Deux issues étaient possibles : renommer le périmètre pour coller au code, ou
livrer l'agrégation promise. Le mainteneur a tranché pour **livrer
l'agrégation**, le module devant tenir son nom.

---

## Décision

`forge-mvc-stats` expose une API d'agrégation par **comptage**, dans le même
style que la consultation existante : SQL visible, exécuteur injecté par
l'application (le module n'ouvre jamais de connexion), validation par défaut.

- `get_stats_counts_sql(group_by, name=None, category=None, since=None)` produit
  un `SELECT <colonne> AS bucket, COUNT(*) AS total ... GROUP BY <colonne>`.
- `prepare_stats_counts_params(...)` produit le tuple de paramètres `?`.
- `count_stats_events(fetch_all, group_by, ...)` exécute et normalise en
  `[{"bucket": ..., "total": int}, ...]`.

**Sécurité (principe 5/7).** La dimension de regroupement `group_by` n'est
**jamais** interpolée depuis une chaîne libre : elle est résolue via une **liste
blanche fermée** (`{"name", "category"}`) vers la colonne SQL réelle. Toute autre
valeur lève `StatsAggregateError`. Les filtres (`name`, `category`, `since`) sont
des paramètres liés `?`, jamais concaténés. La surface d'injection par nom de
colonne ou de valeur est donc nulle.

**Fenêtre temporelle.** Le filtre `since` (timestamp ISO, paramètre lié sur
`created_at >= ?`) couvre le besoin « compter depuis une date ». Un découpage en
buckets temporels (par jour/heure) n'est pas livré ici ; il pourra faire l'objet
d'une extension ultérieure si le besoin se confirme.

---

## Conséquences

- Le module tient enfin son périmètre annoncé : la description (`catalog.py`) et
  la doc de référence parlent désormais de « journal d'événements **et** agrégats
  par comptage » sans sur-promesse.
- L'API publique gagne cinq symboles (`StatsAggregateError`,
  `get_stats_counts_sql`, `prepare_stats_counts_params`,
  `normalize_stats_count_row`, `count_stats_events`), tous typés `pyright strict`.
- Aucune dépendance nouvelle ; aucun accès base automatique ; SQL visible.

---

## Alternatives écartées

- **Renommer le périmètre en « journal d'événements »** : honnête et moins
  coûteux, mais le mainteneur a préféré que le module nommé « stats » fournisse
  réellement de l'agrégation.
- **Agrégation par buckets temporels d'emblée** (jour/heure) : reportée — la
  liste blanche de `group_by` se limite pour l'instant aux dimensions
  catégorielles `name`/`category`, plus le filtre `since`.
