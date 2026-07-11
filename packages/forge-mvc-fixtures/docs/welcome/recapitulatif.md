# Aide-mémoire de la progression Fixtures

Récapitulatif des paliers de la progression *Fixtures* et des commandes de l'opt-in `forge-mvc-fixtures` (ADR-074).

!!! note "Opt-in à SQL visible"
    `forge-mvc-fixtures` est un opt-in CLI-only, à installer explicitement (`pip install --pre forge-mvc-fixtures`).
    Les fixtures sont des fichiers `.sql` relus, chargés dans la base de l'environnement actif ; le SQL est affiché avant d'être exécuté.

## Niveau débutant : charger

| # | Palier | Ce qu'on apprend | Commande-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour les fixtures](debutant/fixtures-welcome.md) | Ce qu'est une fixture, où elle vit | `mvc/fixtures/*.sql` |
| 2 | [Charger une première fixture](debutant/fixtures-load.md) | Afficher puis charger | `fixtures:load`, `--run` |

## Niveau intermédiaire : rejouer, cadrer, générer

| # | Palier | Ce qu'on apprend | Commande-clé |
|---|--------|------------------|---------|
| 1 | [Repartir d'un état propre](intermediaire/fixtures-purge.md) | Vider les tables ciblées | `fixtures:purge`, `--run` |
| 2 | [Cadrer par environnement](intermediaire/fixtures-env.md) | Viser `APP_ENV`, prod protégée | `--force` |
| 3 | [Générer plutôt qu'écrire à la main](intermediaire/fixtures-generate.md) | Échafauder et générer | `fixtures:make-factory`, `fixtures:generate` |

## Niveau avancé : coder et situer

| # | Palier | Ce qu'on apprend | Notion-clé |
|---|--------|------------------|---------|
| 1 | [La factory comme code](avance/fixtures-factory.md) | Coder sa génération | `rows()`, `self.faker`, `--seed` |
| 2 | [Fixtures ou migration de seed](avance/fixtures-vs-seed.md) | Choisir la bonne voie | Frontière (principe 11) |
| 3 | [Un opt-in CLI-only](avance/fixtures-optin.md) | Profil opt-in, indépendance du cœur | CLI-only |

## Mémo des commandes

| Commande | Effet |
|---|---|
| `forge fixtures:load` | Affiche le SQL des fixtures (aucun effet). |
| `forge fixtures:load --run` | Charge les fixtures dans la base de l'environnement actif. |
| `forge fixtures:purge` | Affiche les `DELETE` dérivés des fixtures. |
| `forge fixtures:purge --run` | Vide les tables ciblées. |
| `... --run --force` | Autorise l'exécution en `APP_ENV=prod`. |
| `forge fixtures:make-factory <entity>` | Échafaude une factory depuis le contrat d'entité. |
| `forge fixtures:generate <entity> --rows N --seed S` | Exécute la factory, écrit `mvc/fixtures/<table>.sql`. |

## Règle d'or

Données permanentes de production : migration de seed (`migration:apply`).
Données de démo ou de test rejouables : fixtures (`fixtures:load` / `fixtures:purge`).
