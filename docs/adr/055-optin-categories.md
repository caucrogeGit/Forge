# ADR-055 : Classification des opt-ins par destination

## Statut

Proposé, Forge 1.0.0-rc (ticket `ADR-OPTIN-CATEGORIES-001`).
Décision de gouvernance et de présentation des opt-ins ; relève du mainteneur.

---

## Date

2026-06-29

---

## Contexte

Le nombre d'opt-ins officiels s'étend (une vingtaine de paquets `forge-mvc-*`).
La liste à plat devient difficile à parcourir, que ce soit sur PyPI, dans la commande `opt-in:list` ou dans la documentation.

Le catalogue canonique existe déjà : `cli/optins/catalog.py`, `OFFICIAL_OPTINS: dict[str, OptIn]`, source de vérité unique de la famille `opt-in:*` (ADR-016).
Chaque `OptIn` porte `name`, `package_dist`, `package_import`, `kind` et `summary`.

Le champ `kind` (`route` / `library` / `crosscutting`) décrit *comment* la brique se branche : c'est une classification **technique**.
Il ne dit rien de *à quoi sert* la brique : il manque un axe **fonctionnel**, la « destination ».

Deux fausses pistes ont été écartées pour atteindre ce regroupement.

Renommer les paquets par domaine (par exemple `forge-mvc-db-mariadb`) heurte deux règles.
Le nom d'un paquet PyPI est de l'API publique : renommer un paquet déjà publié serait une rupture (charte, règle C).
Et l'API publique est en anglais (ADR-003), ce qui exclut un préfixe comme `bdd`.

Réutiliser le champ `kind` mélangerait deux axes distincts (technique et fonctionnel) et appauvrirait les deux.

Le catalogue est par ailleurs incomplet : il décrit moins d'entrées qu'il n'existe de paquets, plusieurs opt-ins récents n'y figurent pas.

---

## Décision

### Un axe « destination » ajouté au catalogue, sans renommage

On ajoute un champ `category` à `OptIn`, distinct de `kind`.
`category` exprime la **destination fonctionnelle** ; `kind` reste la forme d'intégration technique.
Aucun paquet n'est renommé : les noms de distribution PyPI restent le contrat public, en anglais (ADR-003).

L'identifiant de catégorie est un slug anglais (cohérent avec ADR-003) ; son libellé d'affichage est en français, côté CLI et documentation.

### Liste canonique des catégories

| Slug | Libellé d'affichage | Opt-ins |
|---|---|---|
| `database` | Bases de données | `mariadb`, `sqlite`, `postgres`, `mssql` |
| `media` | Médias et fichiers | `files`, `images`, `video`, `audio` |
| `security` | Sécurité et accès | `mfa`, `rbac`, `audit` |
| `communication` | Communication | `mail`, `notifications`, `iot` |
| `data` | Données et modélisation | `pivot`, `stats`, `workflow`, `import-export` |
| `i18n` | Internationalisation | `i18n` |
| `content` | Contenu | `qrcode` |
| `configuration` | Configuration | `settings` |
| `operations` | Exploitation et outillage | `deploy`, `admin`, `testing`, `jobs` |

Cette liste est la **taxonomie unique** : la même alimente `opt-in:list` (sortie groupée) et la navigation du site (sections par destination).
Une seule taxonomie, deux surfaces.

### Règle pour tout nouvel opt-in

Tout nouvel opt-in officiel **déclare sa catégorie** dans le catalogue, parmi la liste canonique ci-dessus.
L'ajout d'une catégorie hors liste passe par une mise à jour de cet ADR.

### Cas des backends de base de données

Les backends BDD (`mariadb`, `sqlite`, `postgres`, `mssql`) suivent un modèle **exclusif** (ADR-054) : on en installe **un seul** par projet, découvert par l'entry point `forge_mvc.db_backend`.
Ils ne s'« enable » pas comme les autres opt-ins et ne figurent pas dans `OFFICIAL_OPTINS`.
Ils sont présentés dans une **section dédiée « Bases de données »** (lecture seule, sémantique « choisis-en un »), distincte des opt-ins composables, et restent pilotés par la famille `db:*`.

### Périmètre

Cet ADR fige la taxonomie et la règle de déclaration.
La mise en œuvre (champ `category`, complétion des entrées manquantes du catalogue, `opt-in:list` groupé, réorganisation de la navigation du site) relève de tickets distincts.

---

## Conséquences

Le catalogue gagne un axe fonctionnel et sera complété pour couvrir tous les paquets existants.
`opt-in:list` regroupe les briques par destination, plus lisible à mesure que la liste grandit.
La navigation du site reprend la même taxonomie, sans dépendre des noms de paquets.
Aucun nom de paquet n'est touché : pas de rupture de contrat public, pas de churn d'imports.
Un garde-fou de test pourra vérifier que chaque opt-in du catalogue déclare une catégorie de la liste canonique.

---

## Alternatives écartées

**Renommer les paquets par domaine (`forge-mvc-db-*`, `forge-mvc-media-*`...).**
Rupture du contrat public pour les paquets déjà publiés (charte, règle C), préfixe français exclu par l'ADR-003, et churn massif (noms PyPI, namespaces importables, imports de tests, entry points, classifiers, documentation) pour un gain surtout cosmétique.

**Réutiliser le champ `kind`.**
Mélange un axe technique (intégration) et un axe fonctionnel (destination), au détriment de la clarté des deux.

**Ne rien faire.**
La liste à plat continue de se dégrader à mesure que le nombre d'opt-ins augmente.

---

## Charte appliquée

- Principe 8 (noyau minimal, briques opt-in raisonnées) : la classification rend l'offre d'opt-ins lisible sans l'alourdir.
- Principe 11 (une seule façon officielle) : une **taxonomie unique** alimente le CLI et la documentation.
- Principe 3 (refus de la magie cachée) : la catégorie est déclarée explicitement dans le catalogue, pas inférée.
- Règle C (pas de rupture d'API publique hors release majeure) : on classe sans renommer les paquets.
- ADR-003 (API publique en anglais) : slugs de catégorie en anglais.

---

## Référence

- [ADR-016](016-opt-in-unification.md) : unification du modèle opt-in (cycle, verbes).
- [ADR-052](052-optin-strategy.md) : stratégie et critères d'admission des opt-ins.
- [ADR-054](054-database-backend-optins.md) : backends BDD exclusifs, découverts par entry points.
- [ADR-038](038-optin-docs-embedded-per-package.md) : doc des opt-ins embarquée par paquet, agrégée au site.
- `cli/optins/catalog.py` : catalogue canonique `OFFICIAL_OPTINS`.
