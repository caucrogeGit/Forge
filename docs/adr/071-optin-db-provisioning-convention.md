# ADR-071 : convention unique de provisioning des opt-ins adossés à la base

## Statut

Proposée (2026-07-10).

## Contexte

Plusieurs opt-ins Forge livrent leur propre schéma de table (le paquet embarque
le DDL, une commande `<opt-in>:init` le dépose dans le projet, puis une commande
d'application crée la table). Deux conventions concurrentes coexistent aujourd'hui,
alors qu'elles répondent au même besoin.

**Convention A, migrations versionnées** (`mvc/migrations/` + `forge migration:apply`) :
la commande `init` copie une migration embarquée (`forge_mvc_<paquet>/migrations/`)
vers `mvc/migrations/`, sans exécution SQL ni connexion base ; l'application se fait
ensuite par `forge migration:apply`, qui trace la migration dans `forge_migrations`.
Suivie par **7 opt-ins** : `audit`, `images`, `iot`, `jobs`, `notifications`,
`settings`, `video`.

**Convention B, schéma de modèle déclaratif** (`mvc/models/sql/` + `forge db:apply`) :
la commande `init` copie un fichier `.sql` vers `mvc/models/sql/`, appliqué par
`forge db:apply` (réapplication idempotente, sans table de suivi). Suivie par le
**socle auth du cœur** (`forge auth:init` : `users`, `auth_tokens`,
`auth_audit_log`, etc.) et par le nouvel opt-in **`forge-mvc-sessions-db`**
(`forge sessions:init`, retour terrain 016 F34).

Ce double standard a deux coûts :

- **incohérence de découverte** : deux verbes d'application (`db:apply` contre
  `migration:apply`), deux dossiers cibles, pour une même action « provisionner la
  table d'un opt-in » ; le porteur doit se souvenir, opt-in par opt-in, quelle
  convention s'applique ;
- **ambiguïté de sens** : `mvc/models/sql/` décrit le **modèle de données de
  l'application**, tandis qu'une table d'infrastructure livrée figée par un paquet
  (`forge_sessions`, `forge_jobs`, ...) n'est pas un modèle que l'application
  possède ou étend. Les ranger au même endroit brouille la frontière.

Le retour terrain 016 (F34) a rendu l'écart visible : `sessions:init` a été calqué
sur `images:init` mais a divergé sur la cible (`models/sql` + `db:apply` au lieu de
`migrations/` + `migration:apply`), au motif que « sessions est un schéma de modèle
comme auth ». Cette assimilation est contestable : `users` est bien du modèle
applicatif (l'auteur l'étend de colonnes de profil), alors que `forge_sessions` est
de la pure plomberie de framework que l'application ne modélise jamais.

## Décision

**Le provisioning d'un opt-in adossé à la base passe par la convention A :
migration versionnée dans `mvc/migrations/`, appliquée par `forge migration:apply`.**

La convention B (`mvc/models/sql/` + `forge db:apply`) reste réservée au **modèle
de données applicatif** : les tables que l'application possède et étend, dont le
**socle auth** (`forge auth:init`). Ce n'est pas un provisioning d'opt-in au sens
de cet ADR, mais l'amorçage du modèle du projet.

Critère de tri, pour un schéma livré par un paquet :

- **table d'infrastructure**, figée par le paquet, jamais modélisée ni étendue par
  l'application (sessions, jobs, notifications, audit, événements IoT, réglages,
  médias, transcodages) → **migration** (`mvc/migrations/` + `migration:apply`) ;
- **table du modèle applicatif**, que l'auteur possède et fait évoluer (socle
  `users` et ses tables auth) → **schéma de modèle** (`mvc/models/sql/` +
  `db:apply`).

### Réalignement de `forge-mvc-sessions-db`

`forge-mvc-sessions-db` est le seul opt-in du côté « migration » de la frontière à
suivre encore la convention B. Il est réaligné sur la convention A dans un ticket
dédié :

- le DDL `forge_sessions` est livré comme migration embarquée
  (`forge_mvc_sessions_db/migrations/`) plutôt que comme `sql/*.sql` ;
- `forge sessions:init` copie la migration vers `mvc/migrations/` et suggère
  `forge migration:apply` (au lieu de `mvc/models/sql/` + `db:apply`) ;
- le docstring du store et la notice de l'opt-in citent la nouvelle cible.

La rupture est interne et assumée en phase bêta (ADR-009), sans alias de
compatibilité : le contrat fonctionnel du store (`SessionStore`, colonne `version`
de concurrence optimiste, horodatage UTC) est inchangé ; seule la mécanique de
dépôt du schéma bouge.

## Conséquences

- Une seule façon officielle de provisionner un opt-in adossé à la base
  (principe 11) : « la commande `<opt-in>:init` dépose une migration, `forge
  migration:apply` l'applique ».
- La frontière `mvc/models/sql/` (modèle applicatif) contre `mvc/migrations/`
  (deltas de schéma, dont ceux des opt-ins) devient nette et explicable.
- Les migrations d'opt-ins sont tracées dans `forge_migrations`, ce qui permet à un
  paquet de livrer un delta ultérieur à une version future sans réappliquer ni
  écraser le schéma existant.
- Tout **nouvel** opt-in adossé à la base suit d'emblée la convention A ; le patron
  de référence pour écrire sa commande `init` est `images:init` / `audit:init`,
  plus `sessions:init`.
- `forge auth:init` n'est pas touché : le socle auth reste du modèle applicatif
  (`models/sql` + `db:apply`), documenté comme tel.
- Coût du réalignement : un ticket sur `forge-mvc-sessions-db` (migration embarquée,
  `sessions:init` repointée, tests et notice mis à jour). Aucun autre opt-in n'est
  concerné, les 7 autres suivant déjà la convention retenue.

## Charte appliquée

- Principe 11 (une seule façon officielle de faire chaque chose) : suppression du
  double standard de provisioning.
- Principe 8 (noyau minimal, briques opt-in) : la convention vaut pour les opt-ins ;
  le cœur ne gagne aucune mécanique.
- Principe 3 (refuser la magie cachée) et §7 (Forge affiche) : `init` prépare des
  fichiers sans exécuter de SQL ni se connecter ; l'application reste une commande
  explicite (`migration:apply`).
- Règle A (retirer la cause, pas le symptôme) : on unifie la convention plutôt que
  de documenter au cas par cas quel opt-in suit laquelle.
- Relations : prolonge le retour terrain 016 (F34), s'appuie sur la séparation des
  comptes DDL/DML d'ADR-033 et sur `db:init` d'ADR-067, s'inscrit dans le cœur
  agnostique BDD d'ADR-054.
