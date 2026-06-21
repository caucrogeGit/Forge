# ADR-038 : Documentation des opt-ins embarquée par paquet

## Statut

Accepté, Forge 1.0.0-beta.x (ticket `ADR-OPTIN-DOCS-EMBED-001`).

La décision de principe est prise.
Le module pilote `forge-mvc-stats` a prouvé la chaîne de build complète
(ticket `OPTIN-DOCS-EMBED-STATS-001`, commit `b6f18d5` : `mkdocs build --strict`
vert, doc montée sous `/stats/`), sur le modèle séquencé de l'ADR-035.
La convention de slug d'URL ci-dessous est figée avant le déploiement aux
onze autres opt-ins.

---

## Date

2026-06-21

---

## Contexte

Forge est distribué en plusieurs paquets PyPI : un cœur `forge-mvc` et douze
briques opt-in (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
`forge-mvc-stats`, `forge-mvc-files`, `forge-mvc-images`, `forge-mvc-iot`,
`forge-mvc-video`, `forge-mvc-audio`, `forge-mvc-mail`, `forge-mvc-pivot`,
`forge-mvc-i18n`).
Voir l'ADR-005 (packaging hybride monorepo plus multi-distributions) et
l'ADR-004 (périmètre du core minimal).

Aujourd'hui, toute la documentation et tous les parcours welcome des opt-ins
vivent dans le `docs/` unique du cœur.
Chaque paquet dans `packages/` ne porte qu'un `README.md`.
Le rangement actuel est de plus incohérent et brouille la frontière core / opt-in :

- `docs/iot/` et `docs/video/` ont leur propre tronc de premier niveau ;
- mais MFA, RBAC, Mail, Images sont dissous dans `docs/features/`, au même
  niveau que des pages strictement core (`crud.md`, `relations.md`,
  `migrations.md`) ;
- la référence des opt-ins est éclatée dans `docs/reference/` ;
- les parcours sont dans `docs/starters/welcome-*`.

Trois problèmes en découlent :

1. **Frontière core / opt-in invisible (principes 1 et 8).**
   Un lecteur ne peut pas distinguer ce qui est livré par `forge-mvc` de ce qui
   exige un `pip install forge-mvc-xxx`.
   `features/rbac.md` (opt-in) et `features/crud.md` (core) sont indiscernables.
2. **Rangement non uniforme (principe 11).**
   Deux opt-ins ont un tronc dédié, dix autres sont dispersés dans des sections
   core.
   La charte impose une seule façon officielle de ranger chaque chose.
3. **Couplage de distribution.**
   Un utilisateur qui installe seulement `forge-mvc-mfa` depuis PyPI ne reçoit
   qu'un mince `README.md` ; la vraie documentation est ailleurs, dans le dépôt
   du cœur.
   Toute évolution ou suppression d'un opt-in oblige à éditer le `docs/` du core.

---

## Décision

Chaque paquet opt-in possède sa propre documentation, embarquée dans le paquet
sous `packages/<paquet>/docs/`.
Le site MkDocs unique reste la façade publique : il agrège les arbres de
documentation des paquets au moment du build, via un plugin d'agrégation
(famille `mkdocs-monorepo`).

Concrètement :

- Chaque opt-in expose un sous-arbre homogène : présentation, référence et
  parcours welcome, sous `packages/<paquet>/docs/`.
- Le cœur `docs/` ne documente plus que le cœur ; les pages opt-in en sont
  retirées.
- Le `README.md` PyPI de chaque paquet pointe vers la page publiée de sa doc.
- La navigation du site présente un tronc « Opt-ins officiels » qui rassemble
  les sous-arbres agrégés des douze paquets.

Le site reste unique : on ne fragmente pas en douze sites séparés.
Cela préserve la cohérence pédagogique (les parcours renvoient au cœur) et le
choix monorepo de l'ADR-005.
L'agrégation rétablit en revanche la séparation physique et de distribution :
le paquet embarque et versionne sa propre doc.

---

## Convention de slug d'URL (figée)

Le plugin d'agrégation utilise le `site_name` du sous-`mkdocs.yml` comme
**préfixe d'URL** : la doc d'un opt-in est montée sous `/<slug>/`.
Le choix du slug est donc une décision de surface publique, figée ici avant le
déploiement.

Règle : le slug d'un opt-in est **le nom du paquet PyPI privé de son préfixe
`forge-mvc-`**.

| Paquet | Slug | Racine d'URL |
|---|---|---|
| `forge-mvc-stats` | `stats` | `/stats/…` |
| `forge-mvc-workflow` | `workflow` | `/workflow/…` |
| `forge-mvc-mfa` | `mfa` | `/mfa/…` |
| `forge-mvc-rbac` | `rbac` | `/rbac/…` |
| `forge-mvc-files` | `files` | `/files/…` |
| `forge-mvc-images` | `images` | `/images/…` |
| `forge-mvc-iot` | `iot` | `/iot/…` |
| `forge-mvc-video` | `video` | `/video/…` |
| `forge-mvc-audio` | `audio` | `/audio/…` |
| `forge-mvc-mail` | `mail` | `/mail/…` |
| `forge-mvc-pivot` | `pivot` | `/pivot/…` |
| `forge-mvc-i18n` | `i18n` | `/i18n/…` |

Justification :

- court et lisible (`/stats/welcome/installation/` plutôt que
  `/forge-mvc-stats/welcome/installation/`) ;
- sans ambiguïté dans le contexte du site (le slug nomme la brique) ;
- unique : aucun slug n'entre en collision avec un dossier de premier niveau du
  cœur (`reference`, `features`, `guide`, `install`…). Les slugs `iot` et
  `video` reprennent à l'identique les anciens troncs `docs/iot/` et
  `docs/video/`, qui sont migrés dans les paquets : l'URL publique ne change pas
  pour ces deux modules.

Sous-arborescence interne d'un opt-in (figée pour l'homogénéité) :

- `reference.md` : page de référence, montée en `/<slug>/reference/` ;
- `welcome/` : parcours pédagogique, monté en `/<slug>/welcome/…`, en
  conservant la profondeur `welcome/<niveau>/<palier>.md` pour préserver les
  liens relatifs vers le cœur (voir « Liens relatifs » ci-dessous).

Note d'implémentation : l'`!include` doit être déclaré **avec une clé**
(`- Titre: '!include packages/<paquet>/mkdocs.yml'`).
La forme en item nu est ignorée par le merger du plugin (les pages sont
préfixées dans la nav mais leurs fichiers ne sont pas agrégés).

---

## Pré-requis anti-casse : valider la chaîne de build, puis migrer par paliers

Deux risques techniques interdisaient une bascule en bloc ; le pilote `stats`
les a levés.

1. **Compatibilité du plugin d'agrégation.**
   `mkdocs-monorepo-plugin` (déclaré dans `requirements-docs.txt` et
   `requirements-dev.txt`) cohabite avec `mkdocs-material`, le plugin `search`
   (langue `fr`), `glightbox` et les extensions Markdown actives, et passe
   `mkdocs build --strict` (validé par le pilote, 0 avertissement).
2. **Liens relatifs.**
   Les parcours welcome opt-in contiennent environ 361 liens relatifs `../`.
   Le pilote a montré qu'en **conservant la profondeur** d'arborescence
   (`<slug>/welcome/<niveau>/` aussi profond que l'ancien
   `starters/welcome-<m>/<niveau>/`), la quasi-totalité des liens sortants vers
   le cœur restent valides sans réécriture ; seuls les liens entrants (depuis le
   cœur vers la doc migrée) et le lien « vue d'ensemble des starters » sont à
   recâbler.

Ordre d'exécution :

1. **Outiller** (fait) : dépendance de build ajoutée, plugin branché dans
   `mkdocs.yml`.
2. **Piloter** (fait) : `forge-mvc-stats` migré, `mkdocs build --strict` vert.
3. **Généraliser** : un paquet par ticket, en appliquant la convention de slug
   et la sous-arborescence figées ci-dessus.
4. **Nettoyer** les pages opt-in résiduelles dans le `docs/` du cœur et les
   références croisées.

Aucune suppression dans le `docs/` du cœur n'a lieu avant que le sous-arbre
correspondant ne soit servi par l'agrégation.

Dettes à généraliser pendant le déploiement :

- `tests/meta/test_docs_forge_2x_sweep_001.py` ne balaie que `docs/` ; étendre
  le balayage à `packages/*/docs/` pour que les docs migrées restent couvertes.
- Le hub `docs/starters/index.md` pointera de plus en plus dans les arbres
  montés ; à terme, un tronc de navigation « Opt-ins officiels » dédié.

---

## Conséquences

**Positives :**

- Frontière core / opt-in nette, dans la navigation et sur le disque
  (principes 1 et 8).
- Rangement uniforme des douze opt-ins (principe 11).
- Le paquet embarque et versionne sa doc ; le `README.md` PyPI y pointe.
- Le cœur est découplé : ajouter ou retirer un opt-in ne touche plus le
  `docs/` du core.

**Négatives / coûts :**

- Dépendance de build supplémentaire (plugin d'agrégation) et machinerie
  `mkdocs.yml` à maintenir.
- Effort de migration : déplacement des arbres et réécriture d'environ 361
  liens relatifs.
- Risque de compatibilité du plugin avec le thème et les extensions, à lever
  par le pilote.

---

## ADR liés

- **Précise l'ADR-005** (packaging hybride monorepo) : la documentation suit la
  frontière de distribution déjà actée pour le code.
- **Sert les ADR-004 et 016** (périmètre du core minimal, modèle opt-in) en
  rendant la frontière visible dans la documentation.
- **N'affecte pas l'ADR-035** (parcours manuels) : les parcours welcome restent
  manuels ; seul leur emplacement change.

---

## Charte appliquée

- Principe 1 : séparer framework et briques (la doc suit la séparation du code).
- Principe 8 : noyau minimal, briques opt-in (le cœur ne documente que le cœur).
- Principe 11 : une seule façon officielle de ranger la doc d'un opt-in.
- Principe 6 : tester avant d'élargir (pilote obligatoire avant généralisation).
- Règle A : retirer la cause (la doc opt-in logée dans le cœur), pas le symptôme
  (le rangement incohérent actuel).
