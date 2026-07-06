# ADR-064 : `forge db:config` amorce les variables d'environnement du backend ; le contrat backend porte `env_template`

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `DB-CONFIG-ENV-SCAFFOLD-001`).
Décision actée ; l'implémentation accompagne cet ADR.
Étend le contrat `DatabaseBackend` d'ADR-054 et complète ADR-060 (la configuration de connexion appartient au backend).

---

## Date

2026-07-06

---

## Contexte

Installer un backend BDD se fait par `pip install forge-mvc-<sgbd>`.
Mais `pip` ne peut pas configurer le projet : il installe dans le `.venv`, ne connaît ni la racine du projet ni ses fichiers `env/`, et un wheel n'exécute aucun code à l'installation (packaging moderne, PEP 517).
La configuration de connexion doit donc passer par une commande `forge`, qui, elle, s'exécute dans le projet.

Or aujourd'hui, aucune commande ne remplit ce rôle.
Le squelette est livré sans backend (ADR-060) : `env/example` ne contient qu'un commentaire renvoyant à la documentation du backend, sans aucune clé.
Le développeur doit donc lire la documentation du backend et saisir à la main les bonnes clés (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_*`, `DB_ADMIN_*`…), sans filet : `forge doctor` ne signale même pas ces clés comme manquantes (il n'exige que les clés transverses du cadre).

Ce retour terrain (installation du backend MariaDB dans une application réelle) révèle un trou d'UX : le backend est installé, mais rien n'aide à configurer son environnement.

---

## Décision

### 1. Le contrat backend déclare ses variables d'environnement

Le contrat `DatabaseBackend` (core) porte un attribut `env_template` : la liste ordonnée des variables d'environnement que le backend lit, chacune avec une valeur d'exemple ou un placeholder vide.
Chaque backend la fournit selon ses besoins :

- SQLite : `DB_NAME` (chemin du fichier) ;
- MariaDB : `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`, `DB_APP_PWD`, `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD` ;
- PostgreSQL : `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`, `DB_APP_PWD` ;
- SQL Server : les mêmes, plus `DB_ODBC_DRIVER`.

### 2. `forge db:config` amorce les fichiers d'environnement

Une nouvelle commande `forge db:config` :

- résout le backend installé (par entry point, ADR-054 ; erreur explicite si aucun) ;
- écrit les clés **manquantes** de son `env_template` dans les **trois** fichiers d'environnement du projet, `env/example`, `env/dev` et `env/prod`, groupées sous un en-tête `# Base de données (forge-mvc-<name>)` ;
- procède en **write-if-missing** par fichier et par clé : elle n'écrase jamais une valeur déjà renseignée, et n'ajoute que ce qui manque ;
- **annonce** précisément ce qu'elle a ajouté et liste les clés restant à renseigner ;
- est **idempotente** : relancée quand tout est présent, elle indique que la configuration est complète.

`db:config` n'écrit **jamais de secret** : elle ne pose que des placeholders (valeurs d'exemple pour l'hôte et le port, vides pour les noms, comptes et mots de passe).
C'est ce qui rend légitime l'écriture dans `env/example`, versionné : le gabarit documente les clés attendues sans exposer aucune valeur sensible.
Le développeur renseigne ensuite les valeurs réelles dans `env/dev` et `env/prod` (ignorés par Git).

### 3. `db:init` reste focalisé sur le provisioning

`db:init` ne change pas : il provisionne la base et les comptes (`DB_ADMIN_*`).
La séparation des responsabilités est nette : `db:config` prépare la configuration, `db:init` provisionne, `db:apply` crée les tables.
Aucune commande ne s'exécute « à moitié ».

Le cycle d'ajout d'un backend :

```bash
pip install --pre forge-mvc-mariadb
forge db:config     # écrit DB_* dans env/example, env/dev, env/prod (annoncé)
#   … renseigner les valeurs dans env/dev et env/prod …
forge db:init       # provisionne base et comptes
forge db:apply      # crée les tables
```

### 4. Cohérence avec ADR-060

`db:config` peut écrire `env/example` parce que le backend est **désormais choisi** : ce n'est pas `forge new` qui pré-câble un backend, mais une action explicite du développeur après son choix.
ADR-060 reste vrai : le squelette produit par `forge new` demeure sans backend.

---

## Conséquences

- Le développeur n'a plus à connaître ni saisir les noms de clés : `forge db:config` les pose dans tous les environnements, en une commande explicite et annoncée.
- `env/example` documente enfin les clés du backend choisi (sans secret), ce qui aide toute personne clonant le dépôt.
- L'écriture est explicite et annoncée : elle respecte la charte n°9 (pas d'écriture **invisible**) et n'a rien de la « magie » d'un `pip install` qui modifierait le projet.
- Le contrat `DatabaseBackend` s'enrichit d'un attribut ; les quatre backends doivent le fournir (garde-fou de conformité).
- `doctor` peut, à terme, s'appuyer sur `env_template` pour signaler les clés manquantes (hors périmètre de ce ticket).

### Alternatives écartées

- **`pip install` modifie les `env`** : techniquement impossible (pip ne connaît pas le projet, un wheel n'exécute pas de code) et ce serait précisément l'écriture invisible que la charte interdit.
- **`db:init` en deux temps** (amorcer puis, au second appel, provisionner) : une même commande « s'arrête à moitié », ce qui brouille sa responsabilité (charte n°2). Un verbe dédié est plus clair.
- **`env/dev` seulement** : laisserait `env/example` (le gabarit versionné) et `env/prod` désynchronisés des clés réelles du projet.
- **Afficher seulement (sans écrire)** : plus conservateur, mais le développeur devrait encore recopier les clés à la main.

---

## Charte appliquée

- **Principe 2 (une responsabilité par ticket/commande)** : `db:config` configure, `db:init` provisionne.
- **Principe 3 (refuser la magie cachée)** : l'écriture est déclenchée explicitement et annoncée, jamais au détour d'un `pip install`.
- **Principe 9 (pas d'écriture invisible dans le code utilisateur)** : `db:config` annonce chaque ajout ; elle n'écrase jamais une valeur existante et n'écrit aucun secret.
- **Principe 11 (une seule façon officielle)** : une commande unique et documentée pour amorcer la configuration d'un backend.

Lié à ADR-054 (contrat de backend), ADR-060 (la config de connexion appartient au backend), ADR-033 (comptes `DB_ADMIN_*` / `DB_APP_*`).
