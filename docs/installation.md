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

En `1.0.0-beta.1` à `1.0.0-beta.4`, seul le core `forge-mvc` est publié comme
package PyPI principal. Les modules opt-in existent dans le dépôt comme modules
**source-only** ; ils ne sont pas disponibles via `pip install forge-mvc[...]`
sur PyPI.

Les commandes du type `pip install forge-mvc[mfa]` ou `pip install forge-mvc[rbac]`
**ne fonctionnent pas** en `1.0.0-beta.1` à `1.0.0-beta.4` — ces extras ne sont
pas enregistrés sur PyPI.

À partir de `1.0.0-beta.5`, les opt-ins publiables (`forge-mvc-rbac`,
`forge-mvc-workflow`, `forge-mvc-stats`) seront synchronisés avec la version
du core et disponibles sur PyPI.

**`forge-mvc-mfa` ne sera pas publié sur PyPI en `1.0`** : le module MFA
reste Pre-Alpha tant que le secret TOTP est stocké en clair
(`SEC-MFA-SECRET-ENCRYPTION-001`).

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
