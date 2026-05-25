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

Depuis `1.0.0-beta.9`, Forge distribue le **core** et **tous les opt-ins officiels**
sur [PyPI](https://pypi.org/project/forge-mvc/) (bêta publique — `--pre` requis).
Les opt-ins restent optionnels : le core Forge ne dépend pas d'eux.
Voir [Politique de release](release-policy.md#publication-pypi).

| Package (monorepo) | Contenu | Statut |
|---|---|---|
| `forge-mvc` | Noyau complet — core, CLI, intégrations | Bêta — publié PyPI |
| `forge-mvc-rbac` | Brique RBAC — contrôle d'accès par rôles | Bêta — publié PyPI |
| `forge-mvc-workflow` | Brique workflow — statuts et transitions | Bêta — publié PyPI |
| `forge-mvc-stats` | Brique statistiques — agrégations | Bêta — publié PyPI |
| `forge-mvc-mfa` | Brique MFA — TOTP, codes de récupération | **Alpha** — publié PyPI depuis `1.0.0-beta.9` |
| `forge-mvc-media` | Brique media — helpers applicatifs upload | **Alpha** — publié PyPI depuis `1.0.0-beta.9` (API encore bêta, voir [Limites](production-limits.md)) |

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

Depuis `1.0.0-beta.9`, le core `forge-mvc` et les cinq opt-ins officiels
(`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
`forge-mvc-media`) sont publiés sur PyPI.

Installation directe d'un opt-in (méthode recommandée — disponible pour tous) :

```bash
pip install --pre forge-mvc-rbac
pip install --pre forge-mvc-workflow
pip install --pre forge-mvc-stats
pip install --pre forge-mvc-mfa
pip install --pre forge-mvc-media
```

Le core fournit également les extras `forge-mvc[rbac]`, `forge-mvc[workflow]`,
`forge-mvc[stats]` et `forge-mvc[all]` (raccourcis vers les opt-ins
correspondants) :

```bash
pip install --pre "forge-mvc[rbac]"
pip install --pre "forge-mvc[workflow]"
pip install --pre "forge-mvc[stats]"
pip install --pre "forge-mvc[all]"
```

`forge-mvc[mfa]` et `forge-mvc[media]` ne sont pas définis comme extras du core —
installer `forge-mvc-mfa` ou `forge-mvc-media` directement comme ci-dessus. MFA
est officiellement publié au statut **Alpha** (secret TOTP chiffré au repos via
Fernet) ; l'API de `forge-mvc-media` reste bêta — voir
[Limites](production-limits.md).

Pour installer en mode éditable depuis les sources (contribution Forge) :

```bash
git clone --branch {{forge_tag}} https://github.com/caucrogeGit/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` installe les cinq opt-ins en mode éditable.

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
