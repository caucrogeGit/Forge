# Installation sur une VM Debian vierge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page prépare une machine Debian minimale pour utiliser Forge. Une fois cette étape terminée, continuez avec le [guide de démarrage](guide.md).

## 1. Mettre à jour Debian

```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Installer les dépendances système

```bash
sudo apt install -y \
  git \
  curl \
  ca-certificates \
  build-essential \
  pkg-config \
  python3 \
  python3-venv \
  python3-pip \
  pipx \
  mariadb-server \
  mariadb-client \
  libmariadb-dev \
  openssl
```

## 3. Node.js / npm — optionnel

`forge new` utilise npm automatiquement s'il est présent pour installer les dépendances front et compiler le CSS Tailwind. S'il est absent, le projet est créé normalement et un avertissement est affiché — vous pourrez relancer `npm install && npm run build:css` plus tard.

```bash
sudo apt install -y nodejs npm
```

Vérifier :

```bash
node --version
npm --version
```

## 4. Activer pipx dans le PATH

```bash
pipx ensurepath
exec $SHELL -l
```

Vérifier que les outils sont disponibles :

```bash
python3 --version
git --version
pipx --version
mariadb --version
mariadb_config --version
openssl version
node --version   # optionnel
```

Si une commande obligatoire échoue, la machine n'est pas encore prête.

## 5. Démarrer MariaDB

```bash
sudo systemctl enable --now mariadb
sudo systemctl status mariadb
```

## 6. Vérifier l'accès administrateur MariaDB

Sur certaines installations Debian, le compte `root` MariaDB peut être configuré avec l'authentification système `unix_socket`. Dans ce cas, `mariadb -u root -p` peut échouer alors que `sudo mariadb` fonctionne.

Dans cette procédure Forge, on suppose que le compte `root` MariaDB est configuré avec un mot de passe.

```bash
mariadb -u root -p
```

Entrer le mot de passe `root` MariaDB lorsqu'il est demandé. Une invite `MariaDB [(none)]>` confirme l'accès. Saisir `exit` pour quitter.

!!! note "Recommandation"
    Pour un environnement pédagogique simple, l'utilisation du compte `root` MariaDB avec mot de passe est acceptable.

    Pour un environnement plus sécurisé, créer un compte dédié, par exemple `forge_admin`, et l'utiliser dans `DB_ADMIN_LOGIN` / `DB_ADMIN_PWD`.

## 7. Installer Forge avec pipx

```bash
pipx install forge-mvc
forge --version
```

Si `forge` n'est pas trouvé après l'installation :

```bash
pipx ensurepath
exec $SHELL -l
forge --version
```

## Étape suivante

Créer le premier projet avec le [guide de démarrage](guide.md).
