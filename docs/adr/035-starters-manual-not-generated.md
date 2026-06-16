# ADR-035 — Modèle pédagogique unique : parcours réalisés à la main, retrait de la génération

## Statut

Accepté — Forge 1.0.0-beta.16 (ticket `ADR-STARTERS-MANUAL-001`).

Supersède l'ADR-023 (`forge starter:build` comme façon canonique de construire un
starter) et clôt le volet `starter:build` laissé ouvert par l'ADR-030.
Généralise à tous les parcours opt-in le modèle déjà retenu pour `welcome-forge`
par les ADR-025 et ADR-028 (tutoriel manuel).

Aucune suppression de code n'est appliquée avant que le pré-requis anti-casse
(migration de la documentation) ne soit terminé : la décision est actée, le
démontage est séquencé après la migration.

---

## Date

2026-06-16

---

## Contexte

Forge propose deux mécanismes pédagogiques contradictoires pour la même
collection de parcours :

- Le parcours de base `welcome-forge` est un **tutoriel manuel** (ADR-025,
  ADR-028) : chaque palier de doc montre le fichier complet à créer (contrôleur,
  vue) et la ligne exacte à ajouter dans `mvc/routes.py`. L'apprenant tape et lit
  le code, le câblage est un geste explicite.
- Les parcours opt-in (`welcome-mail`, `welcome-iot`, `welcome-images`,
  `welcome-files`, `welcome-audio`, `welcome-mfa`, `welcome-rbac`,
  `welcome-workflow`, `welcome-stats`, `welcome-video`) sont **générés** par
  `forge starter:build <id>` (ADR-023) : la commande pose les fichiers et
  **injecte les routes** dans `mvc/routes.py` via des marqueurs
  `# forge-starter:<nom>:start` / `:end`.

Cette dualité pose trois problèmes :

1. **Écriture dans le code utilisateur.** `starter:build` réécrit
   `mvc/routes.py`, ce que la charte protège le plus fortement (principe 9, mode
   §7 « Forge ne réécrit jamais silencieusement un fichier applicatif »).
   L'injection de routes est déjà une source de régressions connue (audit
   beta.14 : « la détection du router corrompt `routes.py` »), et l'ADR-030 a dû
   être ouvert pour tenter de réconcilier ce comportement avec la règle 4.3.
2. **Incohérence pédagogique (principe 11).** Deux façons officielles de suivre
   un parcours selon qu'il est de base ou opt-in. La charte impose une seule
   façon officielle de faire chaque chose.
3. **Coût de maintenance.** Le sous-système de génération représente
   ~4 900 lignes de code, 419 fichiers de données embarqués et ~19 000 lignes de
   tests, pour un framework dont l'identité est « noyau minimal, explicite,
   pédagogique, durable ». Si chaque palier dispose d'une page de documentation,
   le générateur fait largement doublon avec le mode « Forge affiche ».

Sur le fond pédagogique, « l'application tourne sans rien lire » est un
anti-objectif pour un framework d'apprentissage : générer invite à sauter la
lecture, alors que recopier oblige à lire chaque ligne.

---

## Décision

Forge adopte un **modèle pédagogique unique** pour tous les parcours : ils sont
**réalisés à la main par l'apprenant en suivant la documentation**, sur le modèle
de `welcome-forge`. La génération de starters est retirée.

Concrètement :

- La commande `forge starter:build` est supprimée.
- La commande `forge starter:list` et le registre `starter.json` sont supprimés :
  sans génération, le registre n'a plus d'objet. Les parcours se découvrent par
  la navigation de la documentation.
- Le sous-système de génération est retiré : `forge_cli/starters/builder.py`,
  `route_ops.py`, `scaffold.py`, le registre, ainsi que l'arborescence de données
  `forge_cli/starters/data/`.
- L'injection de routes dans `mvc/routes.py` par une commande Forge disparaît
  pour les starters. Le câblage des routes redevient un geste manuel décrit dans
  la documentation.

Chaque palier de documentation devient **autosuffisant** : il indique les
fichiers à créer (contrôleur, vue, et le cas échéant modèle / migration) et la
ligne de route à ajouter dans `mvc/routes.py`, exactement comme `welcome-forge`.

---

## Pré-requis anti-casse : migration de la documentation d'abord

Le code de référence des parcours opt-in n'existe aujourd'hui que dans
`forge_cli/starters/data/` ; il est posé par `build`. **Aucune suppression n'a
lieu avant que la documentation ne soit autosuffisante.** L'ordre est :

1. **Rapatrier** dans les pages de doc le code manquant, depuis `data/` :
   - `welcome-mail` (6 paliers) : aujourd'hui sans aucun code dans la doc, à
     compléter entièrement (contrôleur, vue, route).
   - les 9 autres parcours : le code des contrôleurs et vues est déjà présent,
     mais le **câblage des routes** manque à la quasi-totalité des paliers (il
     était injecté par `build`). Ajouter à chaque palier la section « Route »
     façon `welcome-forge`.
2. **Vérifier** chaque parcours de bout en bout : un lecteur doit pouvoir le
   réaliser à la main sans `starter:build`.
3. **Démonter** seulement ensuite le sous-système de génération et nettoyer les
   tests de génération et les références documentaires (`docs/reference/`,
   `docs/release/`, schémas).

---

## Conséquences

**Positives :**

- Une seule façon officielle de suivre un parcours (principe 11).
- Plus aucune écriture Forge dans `mvc/routes.py` côté starters (principes 3, 9 ;
  ferme le volet `starter:build` de l'ADR-030).
- Réduction majeure de la surface de maintenance (code, données, tests).
- Pédagogie homogène : l'apprenant lit et écrit chaque ligne.

**Négatives / coûts :**

- Effort de migration documentaire (un parcours mail à écrire, ~75 paliers à
  compléter d'une section « Route »).
- Perte du confort « projet qui tourne immédiatement » ; assumé comme cohérent
  avec un framework d'apprentissage.
- `forge starter:list` / `starter:build` disparaissent de la CLI ; les
  références (aide, `docs/reference/cli-commands.md`, `api.md`,
  `stability-contract.md`, schémas) sont à nettoyer.

---

## ADR liés

- **Supersède l'ADR-023** (`starter:build` canonique, `forge new` nu) : le volet
  `starter:build` est annulé ; la partie « `forge new` produit un projet nu »
  reste valable.
- **Clôt le volet `starter:build` de l'ADR-030** : la question de l'injection de
  routes par `starter:build` devient sans objet (la commande disparaît). Le volet
  `make:public-*` de l'ADR-030 reste à traiter séparément.
- **Généralise les ADR-025 et ADR-028** (modèle manuel de `welcome-forge`) à tous
  les parcours.

---

## Charte appliquée

- Principe 3 — refuser la magie cachée (plus d'injection de routes).
- Principe 9 — pas d'écriture invisible dans le code utilisateur (`mvc/routes.py`
  n'est plus réécrit par Forge pour les starters).
- Principe 11 — une seule façon officielle de faire chaque chose (modèle manuel
  unique).
- Règle A — retirer la cause (la génération), pas le symptôme (les bugs
  d'injection de routes).
- Note pré-1.0 — en phase bêta, le retrait se fait sans alias déprécié ni guide
  de migration externe.
