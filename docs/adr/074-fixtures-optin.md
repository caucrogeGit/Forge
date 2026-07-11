# ADR-074 : Opt-in fixtures, données de démo et de test rejouables

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-11

## Contexte

Une application pédagogique ou une démo a besoin d'un jeu de données de départ : référentiels, comptes de démonstration, données d'exemple sur lesquelles travailler.
Les utilisateurs (et un banc d'essai comme RéférenCiel) réclament une façon officielle de peupler la base.

Forge n'offre aujourd'hui aucun outil dédié.
Le mot « fixtures » ne désigne dans le dépôt que les fixtures de test de `forge-mvc-testing` (`fake_request`, nettoyages autouse), sans rapport avec des données applicatives.
La question d'un `forge db:seed` a déjà été posée puis classée « hors périmètre » du cœur (audit `consolidation-starter-001.md`, ticket `STARTER-SEED-001` jamais réalisé).

Le mécanisme le plus proche est la migration de seed : un fichier `mvc/migrations/AAAAMMJJHHMMSS_seed_x.sql` écrit à la main, appliqué par `forge migration:apply` (ADR-071).
Ce mécanisme convient aux **données de référence permanentes**, mais pas au besoin réel des fixtures :

- une migration s'applique **une seule fois** (registre `forge_migrations` par empreinte) ; on ne peut pas la rejouer pour repartir d'un état propre ;
- une migration s'applique **dans tous les environnements** ; elle ne sait pas peupler `dev` ou `test` sans toucher `prod` ;
- les migrations sont l'historique du schéma ; y verser des données de démo mélange deux responsabilités.

Le besoin de fixtures est donc distinct : des données **rejouables** (charger, purger, recharger) et **cadrées par environnement**, à la manière de `loaddata`/`fixtures:load --purge` des frameworks voisins.
Ce besoin n'est pas du runtime de framework ; c'est de l'outillage de développement.
Il relève donc d'une brique opt-in (principe 8), pas du cœur.

## Décision

Créer un opt-in officiel `forge-mvc-fixtures`, à **ligne de commande seule** (aucun composant runtime), sur le modèle de `forge-mvc-deploy` (ADR-053).

### Frontière avec la migration de seed (principe 11)

Une seule façon officielle par besoin :

- **données de référence permanentes** (ce qui doit exister partout, y compris en production) : migration de seed écrite à la main, appliquée par `forge migration:apply`.
  Statu quo, inchangé.
- **données de démonstration ou de test, rejouables et cadrées par environnement** : opt-in fixtures.

L'opt-in ne rejoue ni ne remplace les migrations ; il ne gère pas le schéma.
Il peuple et vide des tables déjà provisionnées.

### Franchissement des deux filtres d'admission (ADR-052)

- **Filtre A, runtime.** L'opt-in n'a pas de composant WSGI ; il agit hors requête, adossé au backend BDD, piloté par des commandes explicites, sans broker ni dépendance lourde.
  Il franchit le filtre au titre du mécanisme hors requête « de style Forge ».
- **Filtre B, charte.** Câblage explicite (commandes invoquées à la main, aucune auto-découverte) ; périmètre borné (charger et purger, pas de génération magique) ; **SQL visible** (principe 5) ; frontière nette avec la migration de seed (principe 11) ; contrat de complétude des commandes.

### Forme des fixtures et SQL visible

Les fixtures sont des fichiers **SQL relus** vivant dans le projet utilisateur (par exemple sous `mvc/fixtures/`), pas un format JSON ou YAML qui masquerait les écritures.
La commande de chargement **affiche** le SQL qu'elle exécute, à la manière de `forge db:init` (charte §7) : on voit ce qui va être écrit avant que ce soit écrit.

### Cadrage par environnement et protection de la production

Le chargement vise la base de l'environnement actif (celui que lit la configuration).
La production est protégée par défaut : charger ou purger des fixtures en production exige un geste explicite supplémentaire.

### Commandes (contrat, détaillé en tickets)

- `fixtures:load` : charge un jeu de fixtures dans la base de l'environnement actif, après affichage du SQL.
- `fixtures:purge` : vide les tables ciblées pour repartir d'un état propre.

Les commandes suivent le contrat CLI des opt-ins (ADR-072 : interception de `--help`, amorçage de la configuration) et le registre de dispatch (ADR-059).

### Classification (ADR-055)

Catégorie `operations` (exploitation et outillage), aux côtés de `deploy`, `testing` et `jobs` : outillage de développement à CLI seule.

## Mise en œuvre (phasage)

La mise en œuvre relève de tickets distincts, dans l'ordre :

1. Scaffold du paquet `packages/forge-mvc-fixtures/` (`pyproject.toml`, entry points commandes ADR-059, `py.typed`, smoke test ADR-040).
2. `fixtures:load` sur des fichiers `.sql` cadrés par environnement, avec affichage du SQL et protection de la production.
3. `fixtures:purge`.
4. Doc embarquée du paquet (ADR-038) : `reference.md` et parcours welcome.
5. Entrée au catalogue des opt-ins (catégorie `operations`, ADR-055) et garde-fous meta associés.

## Conséquences

- Un vingt-septième paquet officiel entre dans le monorepo, cohérent et autonome (code, commandes, doc, welcome au même endroit).
- La frontière migration de seed contre fixtures est actée : le référentiel permanent reste une migration ; la démo et le test rejouables deviennent des fixtures.
- L'onboarding gagne une étape : `forge fixtures:load` exige d'abord `pip install forge-mvc-fixtures`.
- Le SQL des fixtures reste visible et versionné dans le projet utilisateur.
- L'opt-in ne remplace pas les migrations de seed ; les deux coexistent avec des rôles disjoints.
- Deuxième opt-in à CLI seule après `deploy` : la dispatch `forge.py` et les garde-fous meta (table des opt-ins, classifiers, smoke test, doc embarquée, parcours welcome) s'appliquent comme aux autres paquets.

## Alternatives écartées

- **Une commande `forge db:seed` dans le cœur.**
  Rejetée : le cœur reste minimal (principe 8) et ne porte pas d'outillage de données ; la question avait déjà été classée hors périmètre (`STARTER-SEED-001`).
- **Tout faire en migration de seed.**
  Rejetée : une migration s'applique une seule fois et dans tous les environnements ; elle ne sait ni rejouer un état propre ni cadrer par environnement, qui sont le cœur du besoin de fixtures.
- **Rattacher les fixtures à `forge-mvc-entities`.**
  Rejetée : le moteur d'entités gère la modélisation, la génération et les migrations ; y ajouter le chargement de données de démo mélange les responsabilités et alourdit un paquet déjà large (ADR-070).
- **Un format de fixtures JSON ou YAML chargé par un mappeur.**
  Rejetée : il masquerait les écritures et contredirait le SQL visible (principe 5) ; on charge des fichiers `.sql` relus.

## Référence

- Charte : `CHARTE_DOC.md` (principe 3, pas de magie ; principe 5, SQL visible ; principe 8, noyau minimal ; principe 10, contrat de complétude ; principe 11, une seule façon officielle).
- [ADR-052](052-optin-strategy.md) : les deux filtres d'admission des opt-ins.
- [ADR-053](053-deploy-extraction.md) : premier opt-in à CLI seule (modèle suivi ici).
- [ADR-055](055-optin-categories.md) : classification des opt-ins par catégorie.
- [ADR-059](059-cli-command-dispatch-registry.md) : registre de dispatch des commandes CLI.
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités et migrations (frontière examinée ici).
- [ADR-071](071-optin-db-provisioning-convention.md) : convention de provisioning des opt-ins BDD.
- [ADR-072](072-optin-cli-command-contract.md) : contrat des commandes CLI d'opt-in.
- [ADR-038](038-optin-docs-embedded-per-package.md) : documentation embarquée par paquet.
- [ADR-040](040-per-package-test-surface.md) : surface de test par paquet opt-in.
- Audit `docs/history/audits/consolidation-starter-001.md` : question `forge db:seed` classée hors périmètre du cœur.
