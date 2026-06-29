# Bilan du niveau intermédiaire

Vous savez faire évoluer le schéma SQL Server et vous connaissez le périmètre Alpha.

## Ce que vous avez appris

- `migration:status` / `migration:make` / `migration:apply` fonctionnent sur SQL Server ;
- ce qui marche (dialecte, paramètres natifs, `db:apply`, migrations, runtime) ;
- ce qui reste (provisioning `db:init`, validation d'intégration, diff incrémental).

## Points clés

- statut Alpha : préparez la base à la main, le reste suit le flux du cœur ;
- les formes gardées remplacent `IF NOT EXISTS` ;
- valider sur un serveur réel fait avancer le backend.

## Après ce niveau

Place au niveau avancé : dialecte et validation.

[Niveau avancé : Le dialecte SQL Server](../avance/mssql-dialect.md)
