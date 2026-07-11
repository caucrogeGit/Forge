# Bilan : niveau intermédiaire (Fixtures)

Récapitulatif du **niveau intermédiaire** de la progression *Fixtures*.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Repartir d'un état propre](fixtures-purge.md) | Vider les tables ciblées avec `fixtures:purge`, ordre inverse pour les clés étrangères. |
| 2 : [Cadrer par environnement](fixtures-env.md) | Viser la base de `APP_ENV`, production protégée par `--force`. |
| 3 : [Générer plutôt qu'écrire à la main](fixtures-generate.md) | Échafauder une factory (`fixtures:make-factory`) et générer le `.sql` (`fixtures:generate`, `--rows`/`--seed`). |

Vous maîtrisez la boucle rejouable charger / purger, le cadrage par environnement et la génération.

## Et ensuite

Place au niveau **avancé** : la factory comme surface de code, puis la frontière avec la migration de seed et la nature d'opt-in CLI-only.

[Niveau avancé : la factory comme code](../avance/fixtures-factory.md)
