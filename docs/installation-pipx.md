# Installation avec pipx

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! info "Publication PyPI à venir"

    Le core `forge-mvc` **sera** disponible sur PyPI dans une prochaine publication.
    Pour **Forge {{forge_version}}** (bêta publique), l'installation recommandée
    est depuis GitHub — voir [Installation depuis GitHub](installation-github.md).

    Les **modules opt-in** (MFA, RBAC, workflow, statistiques) restent en mode
    source-only via GitHub.

`pipx` est la méthode la plus simple pour utiliser Forge comme commande globale.

## Prérequis

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip pipx git openssl
pipx ensurepath
exec $SHELL -l
```

## Installer Forge

```bash
pipx install forge-mvc
forge --version
```

## Créer un projet

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
forge doctor
```

`forge new` clone la référence stable par défaut, prépare l'environnement Python
du projet et réinitialise l'historique Git pour votre application.
