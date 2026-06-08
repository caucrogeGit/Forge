# Installer Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge s'installe différemment selon votre intention. Choisissez d'abord votre
parcours, puis enchaînez avec le [guide de démarrage](../guide/guide.md).

## Utilisateur du framework ou développeur du core ?

Deux parcours **distincts**, qui ne se mélangent pas :

| | **Utilisateur du framework** | **Développeur du core** |
|---|---|---|
| But | Créer une application **avec** Forge | Modifier Forge lui-même |
| Installation | `pipx install --pip-args="--pre" forge-mvc` | `git clone` du dépôt + `pip install -e .` |
| Point d'entrée | `forge new mon-app` | `cd Forge` (le dépôt cloné) |
| Lancement | `forge run` dans le projet généré | `python -m pytest` + outils de dev |
| Référence | [Installation avec pipx](pipx.md) | [Développement du core](core-dev.md) |

## Choisir son parcours

| Usage | Parcours |
|---|---|
| Windows 11 (poste de travail) | [Windows + WSL — parcours complet](windows-wsl.md) |
| Utilisateur du framework — Linux / macOS | [Installation avec pipx](pipx.md) |
| Préparer une machine Debian vierge | [Installation sur une VM Debian vierge](vm-debian.md) |
| Créer un projet depuis une version stable | [Installation depuis GitHub](github.md) |
| Windows (résumé court historique) | [Installation Windows](windows.md) |
| Contribuer au framework Forge | [Développement du core](core-dev.md) |
| Préparer la base locale | [Préparer MariaDB](mariadb.md) |
| Déploiement encadré | [Production](production.md) |

## Modèle de packages

Depuis `1.0.0-beta.9`, Forge distribue le **core** et **tous les opt-ins officiels**
sur [PyPI](https://pypi.org/project/forge-mvc/) (bêta publique — `--pre` requis).
Les opt-ins restent optionnels : le core Forge ne dépend pas d'eux.
Voir [Politique de release](../release/release-policy.md#publication-pypi).

| Package (monorepo) | Contenu | Statut |
|---|---|---|
| `forge-mvc` | Noyau complet — core, CLI, intégrations | Bêta — publié PyPI |
| `forge-mvc-rbac` | Brique RBAC — contrôle d'accès par rôles | Bêta — publié PyPI |
| `forge-mvc-workflow` | Brique workflow — statuts et transitions | Bêta — publié PyPI |
| `forge-mvc-stats` | Brique statistiques — agrégations | Bêta — publié PyPI |
| `forge-mvc-mfa` | Brique MFA — TOTP, codes de récupération | **Alpha** — publié PyPI depuis `1.0.0-beta.9` |
| `forge-mvc-files` | Brique upload générique (écriture sécurisée, storage, service HTTP Range) | **Alpha** : publié PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-images` | Brique images : traitement d'image (Pillow) + couche médias applicative ; dépend de `forge-mvc-files` | **Alpha** : publié PyPI depuis `1.0.0-beta.13` (API encore bêta, voir [Limites](../deployment/production-limits.md)) |
| `forge-mvc-audio` | Brique audio (upload, sondage, transcodage MP3, lecture HTTP Range) | **Beta** : publié PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-iot` | Brique IoT (subscriber MQTT, stockage `iot_events`, API HTTP) | **Alpha** : publié PyPI depuis `1.0.0-beta.12` |
| `forge-mvc-video` | Brique vidéo (upload, transcodage MP4, lecture HTTP Range) | **Beta** : publié PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-pivot` | Brique pivot : associations `many_to_many` enrichies + `make:pivot-crud` | **Beta** : publié PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-mail` | Brique mail (composition, transports, templates Jinja, CLI `mail:*`) | **Beta** : publié PyPI depuis `1.0.0-beta.13` |
| `forge-mvc-i18n` | Brique i18n (catalogues JSON, `trans()`, locale par défaut et fallback) | **Beta** : extrait du core en `1.0.0-beta.15` (ADR-027), publication PyPI à venir |

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
`requirements-dev.txt` installe ensuite les 12 modules opt-in
(également en éditable) et les outils de développement. Voir
[Installation depuis GitHub](github.md) pour les détails.

## Contrat d'installation des opt-ins

Le core `forge-mvc` et onze opt-ins officiels
(`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
`forge-mvc-files`, `forge-mvc-images`, `forge-mvc-audio`, `forge-mvc-iot`,
`forge-mvc-video`, `forge-mvc-pivot`, `forge-mvc-mail`) sont publiés sur PyPI
(rbac/workflow/stats/mfa depuis `1.0.0-beta.9`, `forge-mvc-iot` depuis
`1.0.0-beta.12`, et les six derniers depuis `1.0.0-beta.13`). Le douzième
opt-in, `forge-mvc-i18n` (extrait du core en `1.0.0-beta.15`, ADR-027), attend
sa première publication PyPI ; en attendant il s'installe en éditable via
`requirements-dev.txt`.

Installation directe d'un opt-in (méthode recommandée, disponible pour tous) :

```bash
pip install --pre forge-mvc-rbac
pip install --pre forge-mvc-workflow
pip install --pre forge-mvc-stats
pip install --pre forge-mvc-mfa
pip install --pre forge-mvc-files
pip install --pre forge-mvc-images
pip install --pre forge-mvc-audio
pip install --pre forge-mvc-iot
pip install --pre forge-mvc-video
pip install --pre forge-mvc-pivot
pip install --pre forge-mvc-mail
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

`forge-mvc[mfa]` et `forge-mvc[images]` ne sont pas définis comme extras du core :
installer `forge-mvc-mfa` ou `forge-mvc-images` directement comme ci-dessus
(tous deux publiés sur PyPI). MFA est publié au statut **Alpha**
(secret TOTP chiffré au repos via Fernet) ; l'API de `forge-mvc-images` reste
bêta, voir [Limites](../deployment/production-limits.md).

Pour installer en mode éditable depuis les sources (contribution Forge) :

```bash
git clone --branch {{forge_tag}} https://github.com/caucrogeGit/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` installe les douze opt-ins en mode éditable
(y compris `forge-mvc-i18n`, pas encore publié sur PyPI).

---

## Version stable

Forge {{forge_version}} crée avec `forge new` un projet nu à partir d'un
squelette embarqué, et y installe Forge depuis le paquet `forge-mvc`.

```bash
forge --version
forge new MonProjet
```

## Après installation

Une fois Forge disponible :

```bash
cd MonProjet
source .venv/bin/activate
forge doctor
```

Le guide suivant couvre la création d'une première entité et d'un CRUD complet.
