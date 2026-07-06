# ADR-060 : Squelette livré sans backend BDD ; la config BDD appartient au backend

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `DB-SKELETON-BACKEND-FREE-001`).
Décision actée ; l'implémentation est portée par des tickets distincts.
Révise la trajectoire d'ADR-054 : le squelette ne pose plus de backend BDD, et la configuration BDD quitte le squelette pour le backend installé.

---

## Date

2026-07-04

---

## Contexte

ADR-054 a rendu le cœur agnostique BDD et a fait de chaque SGBD un opt-in exclusif découvert par entry points.
Sa trajectoire prévoyait toutefois que « le squelette dépend de `forge-mvc` plus un opt-in de backend, et `forge new` doit poser le bon backend » (ADR-054, Conséquences).

C'est ce qui a été mis en œuvre : le squelette pin `forge-mvc-mariadb` dans `skeleton/data/requirements.txt`, et `forge new` installe MariaDB d'office.

Deux problèmes en découlent.

1. **MariaDB est imposé au départ.**
   L'utilisateur ne choisit pas son SGBD ; pour en prendre un autre, il doit désinstaller MariaDB et réinstaller le backend voulu.
   Cela contredit ADR-024 (`forge new` produit un projet nu) et le principe 8 (noyau minimal, briques opt-in) : un backend est une brique, pas un acquis.

2. **La forme MariaDB est câblée dans le squelette lui-même, pas seulement dans le backend.**
   `skeleton/data/config.py` lit `DB_ADMIN_*`, `DB_APP_*`, `DB_NAME`, `DB_CHARSET`, `DB_COLLATION` avec des valeurs par défaut MariaDB (port `3306`, `utf8mb4`, split admin/app).
   `skeleton/data/env/example` est intégralement façonné MariaDB.
   Or ces variables n'ont pas de sens pour tous les backends : SQLite n'a ni hôte, ni port, ni charset, ni comptes, seulement un chemin de fichier.

Le squelette n'est donc pas réellement neutre : même en retirant le pin `forge-mvc-mariadb`, `config.py` continue de présupposer MariaDB.

---

## Décision

**Le squelette généré par `forge new` ne contient aucun backend BDD, et ne porte aucune configuration BDD spécifique à un SGBD.**

### Le squelette ne pin aucun backend

`requirements.txt` du squelette ne déclare que `forge-mvc`.
`forge new` n'installe pas de backend et n'en choisit pas à la place de l'utilisateur.

Installer un backend est la première étape explicite après `forge new`, à la charge de l'utilisateur :

```bash
pip install forge-mvc-sqlite     # ou forge-mvc-mariadb, -postgres, -mssql
```

Un projet fraîchement généré démarre sans base : les premiers paliers tournent déjà sans BDD (`forge run`).
Toute opération BDD (`forge db:init`, migrations, modèles) échoue tant qu'aucun backend n'est installé, avec l'erreur explicite « aucun backend BDD installé » déjà prévue par ADR-054.
Ce n'est pas une régression mais le prix assumé de la neutralité (règle B : révéler avant de corriger).

### La configuration BDD appartient au backend

La lecture des variables de connexion quitte le squelette.
Ce n'est plus `config.py` qui lit `DB_APP_*` / `DB_ADMIN_*` : chaque backend fournit, lit et documente ses propres variables d'environnement, adaptées à sa nature.

- MariaDB, PostgreSQL, SQL Server : hôte, port, comptes de provisioning et applicatif, base.
- SQLite : chemin de fichier, sans serveur ni comptes.

Le cœur continue d'exposer la façade `core.database.db` (ADR-054) ; c'est le backend actif, résolu par entry point, qui porte sa configuration.
`config.py` du squelette ne contient plus de bloc BDD spécifique à un SGBD.

### `env/example` neutre

`env/example` ne contient plus le bloc MariaDB (`DB_ADMIN_*`, `DB_APP_*`, `DB_CHARSET`, `DB_COLLATION`).
Il ne conserve que les variables réellement transverses au cadre (application, serveur, TLS, CSP, plafond d'upload).
La configuration BDD est documentée et fournie par le backend choisi (README et parcours welcome de chaque opt-in de backend).

### Sort de la convention de nommage ADR-034

ADR-034 faisait remplir `DB_NAME` / `DB_APP_LOGIN` / `DB_ADMIN_LOGIN` par `forge new` à partir du nom de projet normalisé.
Comme ces variables quittent le squelette, cette commodité ne peut plus s'appliquer à l'écriture d'`env/example` par `forge new`.

La convention de nommage elle-même reste valable ; son point d'application se déplace vers l'étape de configuration du backend (documentée par les backends à comptes, sans objet pour SQLite).
`forge new` continue de renseigner `APP_NAME`.

---

## Conséquences

Positives :

- Squelette réellement nu et neutre, fidèle à ADR-024 et au principe 8 : l'utilisateur choisit son SGBD.
- Plus de forme MariaDB câblée dans du code utilisateur (`config.py`) ni dans `env/example`.
- Cohérence achevée d'ADR-054 : le cœur est agnostique, et le squelette l'est aussi.
- Chaque backend devient autonome sur sa configuration, ce qui simplifie l'ajout d'un nouveau SGBD.

Coûts et limites :

- Un projet fraîchement généré ne peut pas toucher la BDD tant qu'aucun backend n'est installé ; l'onboarding doit rendre cette étape évidente.
- Refactor du squelette (`config.py`, `env/example`, `requirements.txt`) et des messages de fin de `forge new`.
- ADR-034 perd son point d'application dans `forge new` ; la convention de nommage doit être reprise côté configuration de backend.
- La documentation d'onboarding (README généré, guidance agent ADR-047, parcours welcome) doit présenter le choix et l'installation du backend comme première étape.

---

## Trajectoire

1. **Squelette sans pin** : retirer `forge-mvc-mariadb` de `requirements.txt` ; ne garder que `forge-mvc`.
2. **`config.py` neutre** : retirer le bloc de lecture BDD spécifique MariaDB ; la config de connexion passe au backend actif.
3. **`env/example` neutre** : retirer le bloc BDD ; ne conserver que les variables transverses.
4. **Messages `forge new`** : remplacer les mentions MariaDB par une invitation neutre à installer un backend, puis `forge db:init`.
5. **Onboarding** : README généré, guidance agent (ADR-047) et parcours welcome présentent l'installation d'un backend comme première étape.
6. **Reprise ADR-034** : documenter la convention de nommage `DB_NAME` / `DB_APP_LOGIN` côté backends à comptes.

---

## Alternatives rejetées

**Garder le pin `forge-mvc-mariadb` dans le squelette (état ADR-054).**
Simple et clé en main pour le cas courant, mais impose MariaDB, contredit ADR-024 et laisse la forme MariaDB câblée dans le squelette.

**Neutraliser seulement `env/example` (option « B-léger »).**
Retire le pin et l'env MariaDB, mais laisse `config.py` présupposer MariaDB (port `3306`, `utf8mb4`) : le squelette n'est pas réellement neutre.

**Choix du backend par option de `forge new` (`forge new --db sqlite`).**
Offre le choix mais garde `forge new` responsable de poser un backend et une config, alors que la charte veut que la brique soit installée par l'utilisateur.
Retenu comme commodité éventuelle et ultérieure, pas comme mécanisme de base.

---

## Charte appliquée

Principe 8 (noyau minimal, briques opt-in), principe 3 (refuser la magie cachée), principe 9 (pas d'écriture invisible dans le code utilisateur), ADR-004 (périmètre du cœur), ADR-024 (squelette bootstrap, projet nu), ADR-054 (cœur agnostique BDD et backends opt-in), ADR-052 (stratégie des opt-ins).
