# Installation avec pipx

[Accueil](index.html){ .md-button } <button class="md-button" onclick="window.history.back()">← Retour</button>

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
