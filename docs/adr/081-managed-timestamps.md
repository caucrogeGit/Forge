# ADR-081 : Horodatages gérés par le framework (`make:crud`)

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-13

## Contexte

Retour terrain RéférenCiel 021 (F56). Pour une entité avec `options.timestamps: true`, le CRUD généré traitait `created_at` et `updated_at` comme deux champs ordinaires :

- exposés dans le formulaire (`DateTimeField(required=True)` et champs `datetime-local` dans `form.html`), donc à saisir à la main, ce qui n'a pas de sens ;
- attendus dans l'`INSERT`/`UPDATE` du modèle via `data["created_at"]`, alors que le formulaire ne les fournit pas ;
- déclarés `DATETIME NOT NULL` sans valeur par défaut ni source de valeur.

Sur une application réelle, tous les CRUD portent le défaut : le corriger a demandé une reprise transverse (formulaires, modèles, vues).

Le normaliseur canonique fabrique déjà `created_at`/`updated_at` depuis `options.timestamps` (`_system_datetime_field`), mais sans marquer leur nature : rien ne distingue un horodatage géré d'un `datetime` saisi par l'utilisateur.

## Décision

Un horodatage issu de `options.timestamps` est un **champ géré par le framework**, jamais saisi. La valeur est posée par le **modèle généré en Python**, pas par la base.

### Marqueur `managed`

Le normaliseur pose une clé `managed` sur ces champs :

- `created_at` : `"managed": "timestamp_created"` ;
- `updated_at` : `"managed": "timestamp_updated"`.

`managed` entre au contrat de champ (`ALLOWED_FIELD_KEYS`), avec une valeur validée (`ALLOWED_MANAGED_VALUES`). C'est un marqueur **interne** : les auteurs d'entités ne le posent pas, il naît de `options.timestamps`. La clé générique se prête à d'autres champs gérés plus tard (par exemple `soft_delete`).

### Comportement du générateur CRUD

- **Formulaire** (classe `Form` et `form.html`) : les champs gérés sont exclus, comme un champ auto-généré (slug avec `source`). L'utilisateur ne saisit pas d'horodatage.
- **Modèle** : l'`INSERT` pose `created_at` **et** `updated_at` à `datetime.now(timezone.utc)` ; l'`UPDATE` pose `updated_at` à `datetime.now(timezone.utc)` et **exclut** `created_at` (stable à l'édition, comme le slug). Aucune de ces colonnes n'est lue depuis `data`.
- **Toutes les vues générées** (formulaire, liste, fiche détail) et l'export CSV et le tri : les horodatages gérés sont **exclus**. Ce sont des métadonnées système, consultables en base ; les afficher alourdissait la liste d'en-têtes techniques (`Created at` / `Updated at`) et donnait un rendu de développeur plutôt qu'une UX utilisateur (retour terrain).

### Pas de valeur par défaut SQL

Le DDL reste `DATETIME NOT NULL`, **sans** `DEFAULT CURRENT_TIMESTAMP` ni `ON UPDATE`. Python (le modèle) est la seule autorité sur la valeur, cohérent avec le choix de `forge-mvc-sessions-db` (pas de double horloge entre la base et le code). Une seule façon officielle d'horodater (principe 11).

### La forme de la valeur (complété par `TIMESTAMPS-NAIVE-UTC-001`)

La valeur passée est un `datetime` **naïf, en UTC**, produit par `core.database.timestamps.utc_now()`.

Cet ADR disait que Python fait autorité, sans dire sous quelle forme, et l'omission a coûté deux heures.
Les colonnes sont des `DATETIME` sans fuseau : un `datetime` conscient du fuseau y laisse le pilote décider, et chaque pilote décide autrement.
Mesuré sur serveurs réels, serveur en UTC+2 :

```text
mariadb     aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)
postgres    aware -> 14:14:07  (écart 7200 s)   naïf -> 12:14:07  (0 s)
mssql       aware -> 12:14:07  (écart 0 s)      naïf -> 12:14:07  (0 s)
```

PostgreSQL convertit vers l'heure locale du serveur.
Le piège est que la forme consciente **paraît plus juste**, puisqu'elle porte l'information de fuseau.
Elle l'est en Python, elle ne l'est pas au passage du pilote.

## Conséquences

- `forge make:crud` sur une entité horodatée produit un formulaire sans champ d'horodatage, un modèle qui pose lui-même `created_at`/`updated_at`, et un DDL sans défaut : plus de saisie manuelle, plus de `KeyError` runtime sur `data["created_at"]`.
- Surface : ajout d'une clé `managed` au contrat de champ (additive). Le générateur ajoute l'import `datetime` seulement quand un horodatage géré est présent (pas d'import inutile).
- Le choix « Python seule autorité » est assumé et cohérent avec sessions-db ; il écarte les défauts SQL proposés par le retour terrain.
- `deleted_at` (`options.soft_delete`) n'est pas couvert par cette décision : hors périmètre F56, à traiter séparément si le besoin se confirme (règle B, révéler avant d'élargir).

## Alternatives écartées

- **Défauts SQL (`DEFAULT CURRENT_TIMESTAMP` + `ON UPDATE CURRENT_TIMESTAMP`).**
  Proposée par le retour terrain. Écartée : introduit une double horloge (base et code) et contredit la convention établie pour sessions-db. La portabilité entre backends (ADR-054) est aussi plus simple si Python fournit la valeur.
- **Conserver les horodatages en lecture seule dans la liste et la fiche détail.**
  Retenue au départ, puis écartée sur retour terrain : les colonnes `Created at` / `Updated at` alourdissaient la liste et donnaient un rendu technique. Les horodatages gérés sont désormais absents de toutes les vues générées ; ils restent en base.
- **Étendre `_is_generated` (slug) au lieu d'un marqueur dédié.**
  Écartée : mélange deux notions (valeur calculée depuis une source vs horodatage système) ; un marqueur `managed` distinct est plus lisible et extensible.

## Référence

- Charte : `CHARTE_DOC.md` (principe 3, refuser la magie cachée, le SQL et le code restent visibles ; principe 11, une seule façon officielle).
- [ADR-054](054-database-backend-optins.md) : cœur agnostique BDD (portabilité des valeurs).
- [ADR-017](017-slug-type.md) : champ auto-généré stable à l'édition (patron réutilisé).
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités.
- Retour terrain RéférenCiel 021 (F56).
