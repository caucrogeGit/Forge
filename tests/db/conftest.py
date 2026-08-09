"""Point d'entrée des tests d'intégration BDD (marqueur `db`).

Les fixtures `real_db`, `real_pg_db`, `real_mssql_db` et `real_backend_db` ne
sont plus définies ici : elles vivent dans `forge-mvc-testing`, l'infrastructure
de test partagée (ADR-041), et son plugin pytest les expose à toute la suite
(`TESTING-REAL-DB-FIXTURES-001`).

Elles étaient auparavant locales à ce dossier, donc invisibles aux tests des
paquets opt-in sous `packages/*/tests/`, qui avaient chacun réécrit son propre
adaptateur de connexion. Deux façons officielles de monter une base de test
contredisaient le principe 11, et la seconde court-circuitait la vraie couche
d'accès.

Le contrat n'a pas changé : test **sauté** en local sans serveur, en **échec**
en CI sous `FORGE_REQUIRE_DB=1` et ses variantes par backend. Le détail est dans
le module `forge_mvc_testing.real_db`.
"""
from __future__ import annotations
