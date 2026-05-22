# Matrice de compatibilité Forge

Ce document définit les versions officiellement supportées et testées pour
chaque composant de l'environnement d'exécution Forge.

Il complète :

- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Procédure de release](release.md) — checklist avant chaque tag
- [Politique de dépréciation](deprecation-policy.md) — cycle annonce → retrait

---

## Python

| Version | Statut |
|---|---|
| 3.12 | Supportée — minimum requis, version de développement recommandée |
| 3.13 | Supportée — testée en CI |
| 3.14 | Supportée — testée en CI |
| < 3.12 | Non supportée |

**Version minimum :** Python 3.12 (`requires-python = ">=3.12"` dans `pyproject.toml`).

**Version recommandée pour le développement :** Python 3.12.

**CI :** les trois versions 3.12, 3.13 et 3.14 sont testées en parallèle
via la matrice GitHub Actions (`.github/workflows/tests.yml`).

---

## MariaDB

| Version | Statut |
|---|---|
| 10.11 (LTS Debian stable) | Recommandée |
| 10.6 (LTS) | Compatible |
| 11.x (latest) | Compatible — non testée systématiquement |
| MySQL | Non supporté |
| PostgreSQL | Non supporté |
| SQLite | Non supporté |

**Connecteur Python :** `mariadb==1.1.14` (dépendance runtime fixée).

**Dépendance système requise pour compiler le connecteur :**

```bash
sudo apt install build-essential libmariadb-dev pkg-config
```

**Tests MariaDB :** opt-in via la variable d'environnement `FORGE_E2E_MARIADB=1`.
Les bases de données créées par les tests doivent avoir un nom commençant par
`forge_e2e_`.

```bash
FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py
```

**Note :** les tests unitaires Forge (hors `test_e2e_mariadb.py`) ne nécessitent
pas de MariaDB. Une base de données n'est requise que pour les tests E2E et
le déploiement d'un projet Forge réel.

---

## Node.js et npm

| Composant | Usage | Version |
|---|---|---|
| Node.js | Build CSS Tailwind uniquement | >= 18 recommandé |
| npm | Gestion des dépendances front | Inclus avec Node.js |
| Tailwind CSS | Génération de `static/tailwind.css` | ^4.2.2 |
| @tailwindcss/cli | CLI Tailwind | ^4.2.2 |

**Node.js n'est pas requis pour faire tourner un projet Forge.** Il est
uniquement nécessaire pour régénérer le fichier CSS Tailwind lors du
développement du framework lui-même.

Commande de build CSS :

```bash
npm install
npm run build:css
```

Le fichier généré (`static/tailwind.css`) est versionné dans le dépôt.
Les projets Forge n'ont pas besoin de Node.js pour servir les fichiers statiques.

---

## Système d'exploitation

| OS | Statut |
|---|---|
| Debian 12 (Bookworm) | Recommandé en production |
| Ubuntu 22.04 / 24.04 | Supporté — CI ubuntu-latest |
| macOS | Compatible pour le développement |
| Windows | Non testé, non supporté officiellement |

**CI :** `ubuntu-latest` (GitHub Actions).

---

## Dépendances Python runtime

Ces dépendances sont installées automatiquement avec Forge via `pip` ou `pipx`.

| Paquet | Version requise | Usage |
|---|---|---|
| `mariadb` | ==1.1.14 | Connecteur MariaDB |
| `jinja2` | ==3.1.6 | Moteur de templates |
| `python-dotenv` | ==1.2.2 | Chargement `.env` |
| `Pillow` | >=10.0,<13 | Traitement d'images (module média) |
| `argon2-cffi` | >=25.1,<26 | Hachage de mots de passe (Auth/User) |

**Philosophie :** Forge vise un minimum de dépendances runtime. Les trois
dépendances fondamentales sont `mariadb`, `jinja2` et `python-dotenv`.
`Pillow` n'est utilisée que par le module média ; `argon2-cffi` n'est
utilisée que pour le hachage des mots de passe (Auth/User). Toutes sont
installées par défaut. Les dépendances spécifiques aux modules opt-in
(`pyotp` pour MFA notamment) ne sont installées que via le bon extra
— voir « Dépendances optionnelles » ci-dessous.

---

## Dépendances optionnelles

Les modules opt-in de Forge ont leurs propres dépendances, qui ne sont
pas installées par défaut. Elles sont tirées via les extras du package
`forge-mvc`.

| Extra | Module | Dépendances additionnelles |
|---|---|---|
| `[mfa]` | `forge-mvc-mfa` | `pyotp>=2.9,<3` |
| `[rbac]` | `forge-mvc-rbac` | aucune |
| `[workflow]` | `forge-mvc-workflow` | aucune |
| `[stats]` | `forge-mvc-stats` | aucune |

### Installation

!!! info "Extras PyPI disponibles pour les opt-ins publiés"
    Les modules opt-in ont d'abord été traités en **source-only** avant leur publication progressive sur PyPI.

    `forge-mvc-rbac`, `forge-mvc-workflow` et `forge-mvc-stats` sont publiés sur PyPI et synchronisés avec le core.
    `forge-mvc-mfa` est en statut Alpha depuis `MFA-PYPI-READY-001` — non publié en `{{forge_version}}`, publication prévue dans une prochaine release.
    `forge-mvc-media` est en statut Alpha depuis `MEDIA-PYPI-READY-002` — non publié en `{{forge_version}}`, publication prévue dans une prochaine release.

Pour installer les opt-ins en `{{forge_version}}` :

```bash
# Core + opt-ins publiés depuis PyPI
pip install --pre forge-mvc forge-mvc-rbac forge-mvc-workflow forge-mvc-stats

# forge-mvc-media et forge-mvc-mfa — installer depuis les sources
git clone --branch {{forge_tag}} https://github.com/caucrogeGit/Forge.git
cd Forge && pip install -e . && pip install -r requirements-dev.txt
```

**Note sur MFA** : le module `forge-mvc-mfa` est en statut Alpha
(`Development Status :: 3`) depuis `MFA-PYPI-READY-001`. Le secret TOTP est
chiffré au repos via Fernet (`FORGE_MFA_SECRET_KEY`). Non publié sur PyPI
en `{{forge_version}}` — publication prévue dans une prochaine release.

---

## Dépendances de développement

Ces dépendances ne sont pas incluses dans la wheel Forge. Elles sont requises
pour travailler sur le code source de Forge.

| Paquet | Version minimum | Usage |
|---|---|---|
| `pytest` | >=8.0 | Suite de tests |
| `build` | >=1.0 | Construction de la wheel |
| `twine` | >=5.0 | Publication PyPI |
| `mkdocs` | >=1.6 | Documentation |
| `mkdocs-material` | >=9.7 | Thème documentation |
| `pymdown-extensions` | >=10.0 | Extensions Markdown |
| `pip-audit` | >=2.0 | Audit des dépendances |
| `ruff` | >=0.4 | Linter et formateur Python |

Installation :

```bash
pip install -r requirements-dev.txt
```

---

## Outils de documentation

| Outil | Version | Usage |
|---|---|---|
| MkDocs | >=1.6 | Génération du site de documentation |
| mkdocs-material | >=9.7 | Thème Material Design |
| pymdown-extensions | >=10.0 | Admonitions, superfences, etc. |

Construction de la documentation :

```bash
mkdocs build --strict
mkdocs serve          # mode développement
```

---

## Tests standard (sans MariaDB)

Les tests unitaires Forge tournent sans base de données et sans MariaDB installé.

```bash
pytest
```

Ils couvrent : CLI, générateurs, templates, RBAC, Auth/User, sécurité, CSRF,
sessions, mails, médias, pages publiques, migrations SQL (SQLite en mémoire).

---

## Tests opt-in (avec MariaDB)

Les tests E2E MariaDB nécessitent une instance MariaDB accessible localement.

```bash
FORGE_E2E_MARIADB=1 pytest tests/test_e2e_mariadb.py
```

**Prérequis :**

- MariaDB démarré et accessible sur `127.0.0.1:3306`.
- Utilisateur MariaDB autorisé à créer des bases commençant par `forge_e2e_`.

Ces tests sont lancés manuellement avant les releases. Ils ne font pas partie
de la CI automatique sur push.

---

## Versions non garanties

| Environnement | Raison |
|---|---|
| Python < 3.12 | `match/case`, `tomllib` et typing modernes requis |
| MySQL | API MariaDB distincte, connecteur différent |
| PostgreSQL | Dialecte SQL différent, non supporté |
| Windows | Non testé, chemins et dépendances système différents |
| PyPy | Non testé |

---

## Politique de mise à jour des dépendances

- Les versions fixes (`mariadb==1.1.14`, `jinja2==3.1.6`, `python-dotenv==1.2.2`)
  sont mises à jour délibérément après audit de compatibilité.
- Les versions bornées (`Pillow>=10.0,<13`, `argon2-cffi>=25.1,<26`)
  suivent les nouvelles releases mineures compatibles.
- Les dépendances d'extras (ex. `pyotp>=2.9,<3` pour `[mfa]`) suivent
  la même politique, vérifiée dans le `pyproject.toml` du package opt-in
  correspondant.
- Chaque mise à jour de dépendance fait l'objet d'un commit dédié avec
  justification dans le CHANGELOG.
- Un audit `pip-audit` est recommandé avant chaque release :

```bash
pip-audit
```

---

## Limites connues

| Domaine | Limite |
|---|---|
| MariaDB 11.x | Pas de tests CI systématiques — compatible mais non garanti |
| Python 3.14 | En CI mais version pre-release pendant la série 2.x |
| Node.js | Aucune version minimum formelle — >= 18 recommandé |
| Tests E2E | Pas automatisés en CI — lancés manuellement avant release |

---

## Ce que cette matrice ne couvre pas encore

| Domaine | Ticket futur |
|---|---|
| Guide de migration entre versions majeures | `RELEASE-MIGRATION-GUIDE-001` |
| Politique LTS (Long Term Support) | `RELEASE-LTS-001` |
| Automatisation des tests E2E MariaDB en CI | post-roadmap |
| Compatibilité ARM / Apple Silicon | post-roadmap |

---

## Voir aussi

- [Vue d'ensemble Release et compatibilité](release-and-compatibility.md)
- [Guide de migration](migration-guide.md) — vérifier la compatibilité avant de migrer
- [Politique de release](release-policy.md) — règles MAJOR/MINOR/PATCH
- [Sécurité en production](production-security.md) — checklist de déploiement

---

*Guide défini lors de RELEASE-COMPAT-001 (Phase 8 — Release et compatibilité).*
