# ADR-005 — Packaging hybride monorepo / multi-distributions PyPI

## Statut

Acceptée

---

## Contexte

Forge est actuellement distribué comme un seul package PyPI (`forge-mvc`).
Ce modèle est simple mais crée une tension avec la décision ADR-004 d'extraire
5 modules du `core/`.

Plusieurs stratégies de packaging sont envisageables pour Forge 3.0 :

1. **Mono-package** : tout reste dans `forge-mvc`, les modules extraits
   deviennent des sous-packages optionnels dans la même wheel.
2. **Multi-packages séparés** : chaque module est un dépôt et un package PyPI
   indépendants.
3. **Monorepo hybride** : un seul dépôt git, plusieurs distributions PyPI
   construites depuis ce dépôt.

Le choix impacte directement :

- la complexité de développement et de release ;
- l'expérience développeur à l'installation ;
- la granularité des dépendances pour les projets applicatifs ;
- la gouvernance et la compatibilité entre distributions.

---

## Décision

**Forge 3.0 adopte un monorepo hybride avec plusieurs distributions PyPI.**

Concrètement :

1. **Un seul dépôt git** : `forge-mvc` reste le dépôt de référence. Les
   distributions supplémentaires sont construites depuis ce même dépôt avec
   des `pyproject.toml` dédiés par sous-répertoire ou par configuration.

2. **Distributions PyPI planifiées** :

   | Distribution | Contenu | Dépendances |
   |---|---|---|
   | `forge-mvc` | Noyau (core réduit selon ADR-004) | Python 3.12+, Jinja2, MariaDB, argon2-cffi |
   | `forge-mvc-mfa` | Module MFA (TOTP, recovery codes) | `forge-mvc` + pyotp |
   | `forge-mvc-rbac` | Module RBAC fin | `forge-mvc` |
   | `forge-mvc-workflow` | Module workflow | `forge-mvc` |
   | `forge-mvc-stats` | Module statistiques | `forge-mvc` |
   | `forge-mvc[all]` | Métapackage : noyau + tous les modules | Toutes les distributions |

3. **Un seul cycle de release** : toutes les distributions partagent le même
   numéro de version et sont publiées ensemble à chaque release.

4. **Le ticket `PACKAGING-MULTI-DIST-001`** (ticket #20 de la phase 14.3) crée
   l'infrastructure `pyproject.toml` pour ce modèle. Cette ADR grave la
   décision ; l'infrastructure n'est pas créée ici.

---

## Conséquences

- Les utilisateurs de `forge-mvc` sans modules avancés ne téléchargent plus
  MFA, RBAC, workflow et stats par défaut.
- Les starters qui utilisent MFA ou RBAC devront déclarer explicitement
  `forge-mvc-mfa` ou `forge-mvc-rbac` dans leurs dépendances.
- L'outillage de release doit gérer plusieurs builds depuis le même dépôt.
- La compatibilité entre versions de distributions doit être maintenue :
  `forge-mvc-mfa 3.0.x` doit fonctionner avec `forge-mvc 3.0.x`.

---

## Alternatives considérées

**Mono-package avec extras (`forge-mvc[mfa]`).** Acceptable mais moins propre :
les extras sont des mécanismes pip, pas des packages PyPI indépendants. Rend
l'ajout de dépendances optionnelles moins explicite. Gardé comme option de
repli si le monorepo hybride s'avère trop complexe à outiller.

**Multi-dépôts git séparés.** Abandonné : fragmente le développement, complique
les releases coordonnées et la cohérence de version.
