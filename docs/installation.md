# Installation

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge peut s'installer de plusieurs façons selon votre contexte. Choisissez le
chemin le plus simple pour votre usage, puis passez au [guide de démarrage](guide.md).

## Chemins recommandés

| Usage | Méthode |
|---|---|
| Préparer une machine complète | [Installation sur une VM Debian vierge](installation-vm-debian.md) |
| Utiliser Forge comme outil installé | [Installation avec pipx](installation-pipx.md) |
| Créer un projet depuis une version stable | [Installation depuis GitHub](installation-github.md) |
| Contribuer au framework Forge | [Mode développement](installation-developpement.md) |
| Préparer la base locale | [Préparer MariaDB](installation-mariadb.md) |

## Modèle de packages

Forge {{forge_version}} distribue le **core** sur [PyPI](https://pypi.org/project/forge-mvc/) sous `forge-mvc=={{forge_version}}` (bêta publique — `--pre` requis).
Les 4 modules opt-in restent en mode source-only via GitHub.
Voir [Politique de release](release-policy.md#publication-pypi).

| Package (monorepo) | Contenu | Statut |
|---|---|---|
| `forge-mvc` | Noyau complet — core, CLI, intégrations | Bêta |
| `forge-mvc-mfa` | Brique MFA — TOTP, codes de récupération | **Pre-Alpha** (secret en clair) |
| `forge-mvc-rbac` | Brique RBAC — contrôle d'accès par rôles | Beta |
| `forge-mvc-workflow` | Brique workflow — statuts et transitions | Beta |
| `forge-mvc-stats` | Brique statistiques — agrégations | Beta |

Pour installer Forge avec toutes les briques opt-in :

```bash
git clone --branch {{forge_tag}} https://github.com/caucrogeGit/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

`pip install -e .` installe le core en mode éditable.
`requirements-dev.txt` installe ensuite les 4 modules opt-in
(également en éditable) et les outils de développement. Voir
[Installation depuis GitHub](installation-github.md) pour les détails.

## Contrat d'installation des opt-ins

En `1.0.0-beta.4`, seul le core `forge-mvc` est publié sur PyPI.

Les extras `forge-mvc[rbac]`, `forge-mvc[workflow]` et `forge-mvc[stats]`
sont **préparés pour publication** (métadonnées extras configurées —
`VERSION-SYNC-OPTIN-EXTRAS-001`, `OPTIN-PYPI-PUBLISH-PREPARE-001`), mais
la publication effective n'a pas encore eu lieu. Ces extras seront disponibles
sur PyPI à partir de `1.0.0-beta.5`.

Les commandes suivantes **ne fonctionneront qu'après la publication coordonnée**
(`1.0.0-beta.5`) :

```bash
pip install --pre "forge-mvc[rbac]"
pip install --pre "forge-mvc[workflow]"
pip install --pre "forge-mvc[stats]"
pip install --pre "forge-mvc[all]"
```

`forge-mvc[media]` et `forge-mvc[mfa]` **ne sont pas disponibles** :

- **`forge-mvc-media`** : source-only après extraction Phase 11.
- **`forge-mvc-mfa`** : Pre-Alpha — `SEC-MFA-SECRET-ENCRYPTION-001` requis avant
  toute publication PyPI.

Pour installer les opt-ins en `{{forge_version}}`, utiliser le mode source :

```bash
git clone --branch {{forge_tag}} https://github.com/caucrogeGit/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` installe les 4 modules opt-in en mode éditable.

---

## Version stable

Forge {{forge_version}} utilise la référence stable `{{forge_tag}}` par défaut.

```bash
forge --version
forge new MonProjet
```

Pour travailler explicitement depuis la branche de développement :

```bash
forge new MonProjet --ref main
```

## Après installation

Une fois Forge disponible :

```bash
cd MonProjet
source .venv/bin/activate
forge doctor
```

Le guide suivant couvre la création d'une première entité et d'un CRUD complet.
