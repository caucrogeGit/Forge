# Installation Forge sur Windows 11 + WSL Ubuntu

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Guide complet d'installation de Forge sur un poste Windows 11 via
**WSL2 + Ubuntu 24.04 + VS Code Remote WSL**. À la fin de cette page,
l'utilisateur dispose d'un projet Forge fonctionnel, lancé par
`forge run`, avec MariaDB opérationnel et le starter
[Bonjour Forge](../guide/bonjour-forge.md) répondant sur
`https://localhost:8000/welcome`.

!!! tip "Public visé"
    Développeur Windows 11 qui souhaite utiliser Forge **comme un
    framework Python installé** (parcours `pipx`). Ce guide ne couvre
    pas la contribution au cœur Forge — pour cela, voir
    [Mode développement](core-dev.md).

---

## 1. Vue d'ensemble — Windows + WSL + VS Code

Forge est conçu pour Linux et macOS. Sur Windows, la voie officielle
est **WSL2** (Windows Subsystem for Linux), qui exécute une vraie
distribution Linux à l'intérieur de Windows, sans virtualisation
lourde. VS Code se connecte ensuite à WSL via l'extension Remote WSL
pour éditer les fichiers Linux comme s'ils étaient locaux.

```text
Windows 11
└─ WSL2 (hyperviseur léger)
   └─ Ubuntu 24.04 (système de fichiers Linux ext4)
      ├─ Python 3.12+, pipx, forge-mvc
      ├─ MariaDB (compte admin Forge dédié : forge_admin@localhost)
      └─ ~/Projets/<MonProjet>/   ← le projet Forge vit ICI
```

!!! warning "Important — où placer le projet"
    Le projet Forge **doit être créé dans le système de fichiers
    Linux WSL** (par exemple `~/Projets/MonProjet`), **pas** dans
    `/mnt/c/...` ni `C:\Users\...`. Travailler depuis `/mnt/c/` ralentit
    massivement Forge (10× à 100× plus lent), casse les permissions
    Unix et provoque des incohérences MariaDB et Git.

VS Code Remote WSL gère la traversée automatiquement : vous éditez
depuis Windows mais les fichiers vivent côté Linux.

---

## 2. Prérequis

- Windows 11 (ou Windows 10 version 2004+) — admin sur le poste
- 8 Go de RAM minimum (16 Go recommandé pour MariaDB + VS Code)
- Connexion réseau (clone Git, `apt`, `pip`, `npm`)
- VS Code installé sous Windows

---

## 3. Étape 1 — Installer WSL2 + Ubuntu 24.04

Dans un terminal **PowerShell en mode administrateur** :

```powershell
wsl --install -d Ubuntu-24.04
```

Cette commande :

- active la fonctionnalité WSL2 ;
- installe le noyau Linux et le runtime WSL ;
- télécharge la distribution Ubuntu 24.04 ;
- demande un redémarrage si nécessaire.

Au premier lancement d'Ubuntu, créer l'utilisateur Linux (nom +
mot de passe). C'est cet utilisateur qui sera propriétaire de
`~/Projets/MonProjet`.

Vérifier la version :

```bash
lsb_release -a
# Description: Ubuntu 24.04.x LTS
```

Référence officielle Microsoft :
[Installer WSL2](https://learn.microsoft.com/fr-fr/windows/wsl/install).

---

## 4. Étape 2 — Mettre Ubuntu à jour et installer les dépendances Linux

Dans le terminal Ubuntu :

```bash
sudo apt update && sudo apt upgrade -y

# Outils de base (Python 3.12, build tools, Git, curl)
sudo apt install -y \
    python3 python3-venv python3-pip \
    build-essential pkg-config \
    git curl ca-certificates \
    pipx
```

Forge requiert **Python 3.12+** (ADR-006). Vérifier :

```bash
python3 --version
# Python 3.12.x
```

Ubuntu 24.04 LTS fournit Python 3.12 par défaut.

---

## 5. Étape 3 — Connecter VS Code à WSL

1. Sous Windows, installer VS Code (si pas déjà fait).
2. Installer l'extension **WSL** (`ms-vscode-remote.remote-wsl`) depuis
   le Marketplace.
3. Dans le terminal Ubuntu, lancer :

```bash
code .
```

VS Code détecte automatiquement WSL et installe le serveur distant.
Vous éditez ensuite les fichiers Linux depuis l'interface Windows,
sans copie ni synchronisation.

Pour ouvrir directement un projet existant :

```bash
cd ~/Projets/MonProjet
code .
```

---

## 6. Étape 4 — Installer Node.js 20

Forge utilise Tailwind CSS via npm. Node.js 20 LTS est la version
recommandée. Installer via NodeSource :

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Vérifications
node --version    # v20.x
npm --version     # 10.x
```

Node.js est requis uniquement pour recompiler le CSS Tailwind ; le
serveur Python Forge fonctionne sans Node si `static/tailwind.css`
existe déjà.

---

## 7. Étape 5 — Installer Forge via pipx

`pipx` installe Forge dans un environnement Python isolé, distinct
du système et de chaque projet. C'est le parcours recommandé pour
**l'utilisateur du framework**.

```bash
# Préparer le PATH pipx (~/.local/bin) — une fois par compte.
pipx ensurepath
source ~/.bashrc

# Installer Forge depuis PyPI (bêta publique — --pre requis).
pipx install --pip-args="--pre" forge-mvc
```

!!! warning "Le bon nom de paquet est `forge-mvc`"
    Le paquet à installer s'appelle **`forge-mvc`**. **Ne pas
    installer le paquet `forge`** (qui est un projet différent,
    sans rapport).

Vérifier :

```bash
forge --version
# Forge {{forge_version}}
```

Si la commande `forge` n'est pas trouvée :

- vérifier que `~/.local/bin` est bien dans `PATH` (`echo $PATH`) ;
- relancer `source ~/.bashrc` ou ouvrir un nouveau terminal ;
- au besoin, exécuter à nouveau `pipx ensurepath`.

Pour les opt-ins (RBAC, workflow, stats, MFA, media) :

```bash
pipx inject forge-mvc --pip-args="--pre" forge-mvc-rbac
pipx inject forge-mvc --pip-args="--pre" forge-mvc-workflow
# …
```

Voir [Installation — vue d'ensemble](index.md) pour les
détails.

!!! tip "Mettre à jour Forge plus tard"
    Si vous avez créé votre projet avec une beta précédente, lancez
    `forge update --check` pour voir la version installée et la
    commande pip à exécuter. `forge update --pre` met à jour Forge
    dans l'environnement courant (`.venv`) — pour une install pipx,
    la commande affichera le bon `pipx upgrade forge-mvc` à lancer.
    Voir [`forge update`](../reference/cli-commands.md#forge-update).

---

## 8. Étape 6 — Configurer Git

Forge appelle `git` lors de `forge new` (clone du squelette puis
commit initial). Configurer une identité minimale :

```bash
git config --global user.name "Prénom Nom"
git config --global user.email "vous@example.com"
git config --global init.defaultBranch main
```

Sans ces réglages, `forge new` créera quand même le projet, mais le
commit initial échouera avec un message d'erreur Git explicite.

---

## 9. Étape 7 — Installer MariaDB

```bash
sudo apt install -y mariadb-server
sudo service mariadb start

# Configuration interactive — définir le mot de passe root,
# refuser les utilisateurs anonymes, désactiver la connexion
# root distante, supprimer la base test.
sudo mysql_secure_installation
```

Vérifier que le service est démarré :

```bash
sudo service mariadb status
# active (running)
```

WSL ne démarre pas les services automatiquement au boot. Penser à
relancer `sudo service mariadb start` après un redémarrage de WSL
(ou utiliser `systemd` via `/etc/wsl.conf` si vous activez ce mode).

Détails complets : [Préparer MariaDB](mariadb.md).

!!! warning "Ne pas utiliser `root` MariaDB comme compte admin Forge"
    Sous Ubuntu 24.04 / WSL, le compte `root` MariaDB est généralement
    accessible uniquement via `sudo mariadb` (socket Unix, plugin
    `unix_socket`). Le configurer dans `env/dev` avec
    `DB_ADMIN_LOGIN=root` et un mot de passe vide ne fonctionne pas de
    façon fiable, et exposer le mot de passe `root` dans un fichier
    `env/dev` est une mauvaise pratique. Ce guide crée un compte
    **`forge_admin@localhost`** dédié, avec un mot de passe aléatoire
    stocké uniquement dans `env/dev` du projet (jamais commité).

---

## 10. Étape 8 — Créer un projet Forge

!!! warning "À faire dans le HOME Linux, pas dans `/mnt/c`"
    Toujours créer le projet sous votre HOME Linux WSL —
    typiquement `~/Projets/` — pour éviter les ralentissements et les
    problèmes de permissions/Git/MariaDB liés au montage `/mnt/c`.

Pour suivre la progression pédagogique de la documentation Forge,
ce guide cible explicitement le starter [Bonjour Forge](../guide/bonjour-forge.md).
Créer un nouveau projet avec ce starter pré-appliqué :

```bash
mkdir -p ~/Projets
cd ~/Projets

forge new forge-test-wsl --starter welcome
cd forge-test-wsl
source .venv/bin/activate
```

`forge new` clone le squelette, prépare l'environnement virtuel
Python `.venv`, installe les dépendances Python, génère les
certificats SSL HTTPS de développement, compile le CSS Tailwind si
Node.js est présent, applique le starter `welcome` (alias
`bonjour-forge`) et initialise un dépôt Git propre.

!!! note "Sans `--starter welcome`"
    `forge new MonProjet` sans option produit un squelette minimal
    avec la route `/` (HomeController) et `/login` — pas de
    `/welcome`. Si vous omettez le starter, n'exécutez pas les tests
    `/welcome` plus bas ; testez `/` à la place.

---

## 11. Étape 9 — Créer le compte `forge_admin` et lancer `forge db:init`

Ce guide ne réutilise **pas** le compte `root` MariaDB. À la place,
Forge utilise un compte d'administration dédié **`forge_admin@localhost`**
créé avec un mot de passe aléatoire, stocké uniquement dans `env/dev`
du projet.

### a) Générer les mots de passe et mettre à jour `env/dev`

Depuis le projet, lancer ce petit script Python (utilise le module
standard `secrets`, aucune dépendance externe) :

```bash
cd ~/Projets/forge-test-wsl
source .venv/bin/activate

python - <<'PY'
from pathlib import Path
import secrets
import string
import re

path = Path("env/dev")
text = path.read_text(encoding="utf-8")

alphabet = string.ascii_letters + string.digits
admin_pwd = ''.join(secrets.choice(alphabet) for _ in range(24))
app_pwd = ''.join(secrets.choice(alphabet) for _ in range(24))

def set_var(content, name, value):
    pattern = re.compile(rf"^{name}=.*$", re.MULTILINE)
    if not pattern.search(content):
        raise SystemExit(f"ERREUR : variable absente dans env/dev : {name}")
    return pattern.sub(f"{name}={value}", content, count=1)

text = set_var(text, "DB_ADMIN_LOGIN", "forge_admin")
text = set_var(text, "DB_ADMIN_PWD", admin_pwd)
text = set_var(text, "DB_APP_PWD", app_pwd)

path.write_text(text, encoding="utf-8")
print("env/dev mis à jour.")
PY
```

À l'issue de ce script, `env/dev` contient :

| Variable | Valeur |
|---|---|
| `DB_ADMIN_LOGIN` | `forge_admin` |
| `DB_ADMIN_PWD` | mot de passe aléatoire 24 caractères |
| `DB_APP_PWD` | mot de passe aléatoire 24 caractères |
| `DB_APP_LOGIN` | déjà rempli par `forge new` (ex. `forge_test_wsl_app`) |
| `DB_NAME` | déjà rempli par `forge new` (ex. `forge_test_wsl`) |

!!! warning "Ne jamais commiter `env/dev`"
    Le fichier `env/dev` contient des **secrets en clair**
    (mots de passe MariaDB). Le `.gitignore` fourni par `forge new` le
    couvre déjà. Vérifier avec `git status` : `env/dev` ne doit pas
    apparaître dans les fichiers suivis. Ne pas pousser de secrets sur
    GitHub, même sur un dépôt privé de test.

### b) Créer `forge_admin@localhost` dans MariaDB

Récupérer le mot de passe admin depuis `env/dev` puis créer le compte
côté MariaDB via `sudo mariadb` (socket root, pas besoin de mot de
passe système) :

```bash
DB_ADMIN_PWD="$(grep '^DB_ADMIN_PWD=' env/dev | cut -d= -f2-)"

sudo mariadb <<SQL
CREATE USER IF NOT EXISTS 'forge_admin'@'localhost' IDENTIFIED BY '${DB_ADMIN_PWD}';
ALTER USER 'forge_admin'@'localhost' IDENTIFIED BY '${DB_ADMIN_PWD}';
GRANT CREATE, ALTER, DROP, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE,
      CREATE USER, RELOAD, PROCESS, FILE, SHOW DATABASES
      ON *.* TO 'forge_admin'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL
```

Le bloc fait délibérément les deux opérations :

- `CREATE USER IF NOT EXISTS` crée le compte s'il n'existe pas — et **ne
  change pas son mot de passe** s'il existe déjà ;
- `ALTER USER ... IDENTIFIED BY` réinitialise le mot de passe pour
  qu'il corresponde à `DB_ADMIN_PWD` dans `env/dev`.

C'est ce double ordre qui rend le tutoriel **rejouable** : si vous
relancez le script de génération de mot de passe, le compte
`forge_admin` existant sera mis à jour, pas recréé.

Vérifier que le compte fonctionne :

```bash
mariadb -u forge_admin -p"${DB_ADMIN_PWD}" -e "SELECT USER(), CURRENT_USER(), VERSION();"
# +--------------------------+--------------------------+----------------+
# | USER()                   | CURRENT_USER()           | VERSION()      |
# +--------------------------+--------------------------+----------------+
# | forge_admin@localhost    | forge_admin@localhost    | 10.x ou 11.x   |
# +--------------------------+--------------------------+----------------+
```

### c) Lancer `forge db:init`

```bash
forge db:init
```

`forge db:init` se connecte à MariaDB avec `forge_admin@localhost`,
crée la base de données, l'utilisateur applicatif (login
`DB_APP_LOGIN`, mot de passe `DB_APP_PWD`), applique les fichiers SQL
des entités et prépare la table `forge_migrations`. La sortie doit
indiquer **OK** pour chaque étape.

---

## 12. Étape 10 — `forge doctor`

Diagnostic complet de l'environnement et de la cohérence projet :

```bash
forge doctor
```

À ce stade, toutes les sections doivent renvoyer **OK** (ou
`info`/`warn` non bloquants). Si une section retourne `fail`,
corriger avant de lancer l'application.

---

## 13. Étape 11 — Lancer l'application avec `forge run`

```bash
forge run
```

`forge run` est la **commande officielle de lancement en
développement** depuis la phase post-beta.10 :

- lit `APP_ENV` (défaut `dev`) ;
- démarre le serveur de développement Forge ;
- active l'**autoreload** : redémarre le serveur dès qu'un fichier
  applicatif change (`mvc/**/*.{py,html,json,sql}`, `core/**/*.py`,
  `app.py`, `config.py`, `env/dev`).

L'application démarre sur `https://localhost:8000` (HTTPS de
développement, certificat auto-signé — accepter l'exception dans le
navigateur au premier accès).

!!! note "`python app.py` reste possible (bas niveau)"
    Le lancement direct `python app.py` existe encore comme commande
    bas niveau, sans autoreload ni diagnostic. Ce n'est pas le
    parcours recommandé en développement : utilisez `forge run`. Pour
    désactiver uniquement l'autoreload, préférez `forge run --no-reload`.

En production, `forge run` refuse explicitement de démarrer le
serveur intégré et affiche la stratégie WSGI à suivre. Voir
[Déploiement WSGI minimal](../wsgi-deployment.md).

---

## 14. Étape 12 — Vérifier les routes

Depuis Windows, ouvrir le navigateur sur :

| URL | Réponse attendue |
|---|---|
| `https://localhost:8000/welcome` | Texte brut : `Bonjour Forge` |
| `https://localhost:8000/welcome/greet` | Texte brut : `Bonjour Forge` |
| `https://localhost:8000/welcome/greet?name=Roger` | Texte brut : `Bonjour Roger` |
| `https://localhost:8000/` | Page d'accueil par défaut du squelette (HomeController) |

Si une route renvoie 404, vérifier que le starter `welcome` a bien
été appliqué : `cat mvc/routes.py | grep welcome`. Détails dans
[Bonjour Forge — starter](../starters/welcome/index.md).

---

## 15. Problèmes fréquents

### `forge: command not found`

- Le PATH de pipx (`~/.local/bin`) n'est pas dans `$PATH`.
- Solution : `pipx ensurepath && source ~/.bashrc`.

### `forge new` échoue avec « Please tell me who you are »

- Git n'a pas d'identité globale.
- Solution : configurer `git config --global user.name/user.email` (§ 8).

### MariaDB n'est pas actif

- `forge db:init` ou `forge doctor` signale qu'aucune connexion
  MariaDB n'aboutit.
- Solution : `sudo service mariadb start`, puis `sudo service mariadb status`
  doit indiquer `active (running)`.

### MariaDB inaccessible après redémarrage WSL

- WSL ne démarre pas les services au boot par défaut.
- Solution : `sudo service mariadb start` à la session, ou activer
  systemd via `/etc/wsl.conf`.

### `forge db:init` affiche « Connexion MariaDB admin impossible »

- `DB_ADMIN_LOGIN` ou `DB_ADMIN_PWD` ne correspondent pas à un
  compte MariaDB existant et utilisable.
- Solution : rejouer l'étape `b)` de la section 11 — vérifier que
  `forge_admin@localhost` existe et que son mot de passe correspond à
  `env/dev`. La commande de vérification de référence :
  `mariadb -u forge_admin -p"$(grep '^DB_ADMIN_PWD=' env/dev | cut -d= -f2-)" -e "SELECT USER();"`.

### `Access denied for user 'forge_admin'@'localhost'`

- Le compte `forge_admin` existe déjà dans MariaDB mais avec un mot
  de passe différent de celui inscrit dans `env/dev` (par exemple
  parce que le script de génération a été relancé après une première
  création).
- Solution : refaire l'**`ALTER USER`** de l'étape `b)`.
  `CREATE USER IF NOT EXISTS` à lui seul **ne change pas** le mot de
  passe d'un compte existant — seul `ALTER USER ... IDENTIFIED BY`
  le synchronise avec `env/dev`. C'est pourquoi la section 11 lance
  les deux ordres SQL à la suite.

### Ne pas commiter les secrets DB

- Le fichier `env/dev` contient `DB_ADMIN_PWD` et `DB_APP_PWD` en
  clair.
- Vérification : `git status` ne doit jamais lister `env/dev`. Si
  c'est le cas, ajouter explicitement `env/dev` à `.gitignore` et
  retirer le fichier de l'index : `git rm --cached env/dev`. Ne
  jamais pousser de secrets sur GitHub, même sur un dépôt privé.

### Le projet est extrêmement lent (rendu, tests, `forge run`)

- Le projet est probablement sous `/mnt/c/...`.
- Solution : déplacer le projet sous `~/Projets/...` (système de
  fichiers Linux WSL ext4 natif).

### `npm install` échoue

- Node.js absent ou trop ancien.
- Solution : réinstaller Node.js 20 LTS via NodeSource (§ 6).

### Le navigateur refuse le certificat HTTPS

- Certificat auto-signé de développement.
- Solution : accepter l'exception dans le navigateur, ou recréer les
  certificats avec `forge cert:dev` si la commande est disponible.

### `pipx install forge-mvc` ne trouve rien

- La bêta publique exige le flag `--pre`.
- Solution : `pipx install --pip-args="--pre" forge-mvc`.

---

## 16. Validation finale

À la fin du parcours, l'état attendu :

| Élément | Statut |
|---|---|
| WSL Ubuntu 24.04 | OK |
| VS Code Remote WSL | OK |
| Python 3.12 + `.venv` projet | OK |
| Node.js 20 LTS | OK |
| Forge CLI (`pipx install forge-mvc`) | OK |
| MariaDB démarré et accessible | OK |
| Projet sous `~/Projets/forge-test-wsl` (FS Linux) | OK |
| Compte `forge_admin@localhost` actif | OK |
| `forge db:init` | OK |
| `forge doctor` | OK |
| `forge run` actif (autoreload) | OK |
| Routes `/welcome`, `/welcome/greet` | OK |

> **Forge est installé. Le projet répond. Vous pouvez maintenant
> créer votre application.**

---

## 17. Aller plus loin

| Étape suivante | Ressource |
|---|---|
| Comprendre le parcours Bonjour Forge | [Bonjour Forge](../guide/bonjour-forge.md) |
| Démarrer un vrai projet | [Démarrer avec Forge](../guide/getting-started.md) |
| Première application complète | [Application complète](../guide/app-complete-tutorial.md) |
| Catalogue des starters | [Vue d'ensemble des starters](../starters/index.md) |
| Référence HTTP | [Convention HTTP inspectable](../reference/http.md) |
| Toutes les commandes CLI | [Commandes CLI](../reference/cli-commands.md) |

---

## Voir aussi

- [Installation — vue d'ensemble](index.md)
- [Installation avec pipx](pipx.md)
- [Installation Windows (page courte historique)](windows.md)
- [Préparer MariaDB](mariadb.md)
- [Roadmap Forge](../roadmap/forge-roadmap.md) — ticket `INSTALL-WSL-DOCS-001`
