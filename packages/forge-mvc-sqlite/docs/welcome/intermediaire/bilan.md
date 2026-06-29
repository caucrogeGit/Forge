# Bilan du niveau intermédiaire

Vous savez faire évoluer et inspecter une base SQLite avec Forge.

## Ce que vous avez appris

- `migration:status` / `migration:make` / `migration:apply` gèrent les évolutions ;
- la table `forge_migrations` trace les migrations appliquées ;
- la base étant un fichier, on l'inspecte avec `PRAGMA` ou un client SQLite.

## Points clés

- les commandes `migration:*` sont celles du cœur, identiques quel que soit le backend ;
- l'introspection SQLite passe par `PRAGMA table_info` ;
- le SQL des migrations reste visible et éditable.

## Après ce niveau

Place au niveau avancé : comprendre le dialecte et choisir SQLite à bon escient.

[Niveau avancé : Le dialecte SQLite](../avance/sqlite-dialect.md)
