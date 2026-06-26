# ADR-053 : Extraction du déploiement dans un opt-in

## Statut

Proposé, Forge 1.0.0-beta.x (ticket `DEPLOY-EXTRACT-001`).
Décision d'architecture ; relève du mainteneur.

---

## Date

2026-06-26

---

## Contexte

Le déploiement vit aujourd'hui dans le cœur du CLI : `cli/deploy/` fournit les
commandes `forge deploy:init` (génère `wsgi.py`, une configuration Nginx, une
unité systemd, un `README_DEPLOY.md`) et `forge deploy:check`, pour environ 730
lignes.

Trois constats motivent cet ADR :

1. **C'est de l'outillage, pas du runtime.** Aucun code de `core/` ni d'une
   application n'importe `cli.deploy` : c'est un générateur de configuration
   d'exploitation, jamais une brique que l'application appelle à l'exécution.
2. **C'est opinioné.** `deploy:init` suppose Nginx, systemd et Gunicorn. Une
   application déployée en Docker, en Kubernetes ou derrière un autre proxy n'a
   pas besoin de cette opinion, aujourd'hui cuite dans le cœur du CLI.
3. **Ce n'est pas de la génération de code MVC.** La génération du cœur (les
   `make:*`) produit le code applicatif de l'utilisateur (entités, CRUD,
   contrôleurs), ce qui est bien du ressort du cœur (ADR-004). Générer une
   configuration d'infrastructure relève d'une autre catégorie.

Le dossier `deploy/` à la racine du dépôt (sortie régénérable de `deploy:init`)
a par ailleurs été retiré : le dépôt framework ne porte pas d'application
déployée (ADR-044). La question restante est : la génération de déploiement
elle-même doit-elle rester dans le cœur, ou devenir un opt-in ?

---

## Décision

Extraire le déploiement dans un opt-in **`forge-mvc-deploy`** (module
`forge_mvc_deploy`).

Périmètre de l'opt-in :

- les commandes `forge deploy:init` et `forge deploy:check` ;
- les gabarits générés (Nginx, systemd, `wsgi.py`, `README_DEPLOY.md`) ;
- la documentation de déploiement (`docs/deployment/`) migrée en doc embarquée du
  paquet (ADR-038).

Branchement, fidèle au modèle déjà en place pour les opt-ins à CLI (`settings:init`,
`audit:init`, `iot:*`, etc.) : `forge.py` dispatche `deploy:*` vers
`forge_mvc_deploy` par import paresseux, avec un repli explicite « module non
installé, lancer `pip install forge-mvc-deploy` ».

`forge-mvc-deploy` est le **premier opt-in à CLI seule** (pas d'API runtime
importée par l'application). Ce n'est pas sans précédent : `forge-mvc-testing`
est déjà un opt-in dev-only sans API métier. L'outillage de déploiement suit la
même logique : on installe la brique quand on en a besoin.

Justification au regard de la charte :

- **Principe 8 (noyau minimal, briques opt-in)** : le déploiement n'est pas du
  runtime de framework ; il rejoint les capacités déjà extraites (mail, i18n,
  pivot, files, images).
- **ADR-004 (périmètre du cœur)** : le cœur génère du code MVC, pas de la
  configuration d'infrastructure.
- L'opinion Nginx/systemd/Gunicorn devient **opt-in** au lieu d'être imposée par
  le cœur.

---

## Conséquences

- Le cœur du CLI maigrit (730 lignes et leurs gabarits partent dans l'opt-in).
- Le déploiement devient une brique cohérente et autonome : code, gabarits et
  documentation au même endroit (doc embarquée ADR-038).
- L'onboarding gagne une étape : `forge deploy:init` exige d'abord
  `pip install forge-mvc-deploy`. Le repli de `forge.py` guide l'utilisateur.
- Premier opt-in à CLI seule : la dispatch `forge.py` et les garde-fous meta
  (table des opt-ins, classifiers, smoke test, doc embarquée, parcours welcome)
  s'appliquent comme aux autres paquets.
- Les références `deploy/...` de la documentation restent valides : elles
  désignent le dossier généré dans le projet utilisateur, pas le dépôt framework.

---

## Alternatives écartées

- **Laisser le déploiement dans le cœur du CLI.** Contredit le principe 8 et
  l'ADR-004, et impose l'opinion Nginx/systemd/Gunicorn à tous les projets, y
  compris ceux qui déploient autrement.
- **Documenter sans générer (comme les starters, ADR-035).** Les guides
  `docs/deployment/` existent déjà, mais `deploy:check` a besoin de code, et les
  gabarits générés (config adaptée à `upload_max_size`, chemins du projet) ont
  une vraie valeur qu'un copier-coller manuel perd. L'opt-in garde la génération
  utile tout en la rendant optionnelle.
- **Rattacher le déploiement à un opt-in existant** (par exemple
  `forge-mvc-admin`). Mauvais domaine : le déploiement n'a rien à voir avec le
  back-office. Une brique dédiée est plus claire (principe 11).

---

## Référence

- Charte : `CHARTE_DOC.md` (principe 8, noyau minimal ; principe 11, une seule
  façon officielle).
- [ADR-004](004-core-perimeter.md) : périmètre du cœur minimal.
- [ADR-016](016-opt-in-unification.md) : modèle opt-in.
- [ADR-035](035-starters-manual-not-generated.md) : documenter plutôt que
  générer (tension examinée ici).
- [ADR-038](038-optin-docs-embedded-per-package.md) : documentation embarquée par
  paquet.
- [ADR-044](044-framework-only-repo.md) : le dépôt framework ne porte que le
  framework.
- `cli/deploy/` (code actuel), `docs/deployment/` (guides à migrer).
