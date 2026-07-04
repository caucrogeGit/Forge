# Installer Forge sur Linux et créer un projet

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page décrit le parcours complet pour préparer un poste Linux puis créer un nouveau projet Forge.

Elle vise Debian, Ubuntu, Linux Mint et les distributions compatibles avec `apt`.
Pour les autres distributions, le principe reste le même, seuls les noms de paquets système changent.

---

## Objectif

Aller d'un poste Linux propre à un projet Forge qui démarre en développement avec le backend MariaDB.

!!! note "Forge est agnostique en base de données"
    Le cœur de Forge ne dépend d'aucun SGBD (ADR-054).
    La base est fournie par un **backend opt-in** que vous choisissez et installez : `forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres` ou `forge-mvc-mssql`.
    Ce guide utilise **MariaDB**, un serveur robuste et courant.
    Pour un démarrage sans aucun serveur à installer, le backend `forge-mvc-sqlite` (une base dans un simple fichier) est une alternative plus légère : installez `forge-mvc-sqlite` au lieu de `forge-mvc-mariadb` et sautez toutes les étapes propres à MariaDB.

À la fin de ce parcours, vous disposez :

* des outils système nécessaires ;
* de Forge installé avec `pipx` ;
* de Git configuré sur le poste ;
* de Node.js 24 installé pour la compilation du CSS ;
* de MariaDB installé et démarré ;
* d'un nouveau projet Forge créé ;
* du backend `forge-mvc-mariadb` installé dans le projet ;
* d'un dépôt Git local versionné et poussé sur GitHub ;
* d'`env/dev` configuré et cohérent avec MariaDB ;
* de la base initialisée et des migrations appliquées ;
* du serveur de développement lancé.

---

## Vue d'ensemble

Cette page est organisée en deux parties.

La première prépare le poste Linux.
Elle se fait une seule fois sur une machine neuve.

La seconde crée et configure un projet Forge.
Elle se refait pour chaque nouveau projet.

Si Forge, Git, `pipx`, Node.js 24 et MariaDB sont déjà installés sur votre poste, vous pouvez aller directement à la partie **Créer et configurer un projet Forge**.

---

## Ce que cette page installe

| Partie | Domaine | À refaire ? |
|---|---|---|
| Préparer le poste Linux | système, `pipx`, Forge, Git global, Node.js 24, MariaDB Server | une fois par machine |
| Créer et configurer un projet Forge | `forge new`, backend `forge-mvc-mariadb`, `env/dev`, Git local, GitHub, base MariaDB, migrations, `forge run` | à chaque nouveau projet |

Les pages [Préparer MariaDB](mariadb.md) et [Comptes MariaDB d'un projet](mariadb-comptes.md) restent des références pour approfondir ou dépanner.
Vous n'avez pas besoin d'y aller pour terminer une installation standard.

---

## Prérequis

* Un poste Linux à jour, avec un accès `sudo`.
* Une connexion réseau.
* Un compte GitHub si vous souhaitez héberger le dépôt distant.

## Mode de lecture

Chaque étape du parcours est placée dans un bloc dépliable.

Ouvrez les étapes dans l'ordre lors d'une première installation.
Pour une vérification ou un dépannage, ouvrez seulement le chapitre concerné.

Les blocs internes indiquent :

* l'objectif de l'étape ;
* les points d'attention ;
* la validation attendue ;
* les erreurs courantes quand elles existent.

---

## Partie 1 - Préparer le poste Linux

Cette partie prépare la machine.
Elle se fait une seule fois sur un poste neuf, ou lorsqu'un outil système manque.

??? info "1. Mettre à jour le système"
    **Objectif :** Mettre à jour les paquets du système avant d'installer Forge et ses dépendances.

    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

    ---

    !!! success "Validation attendue"
        `sudo apt update` et `sudo apt upgrade -y` se terminent sans erreur bloquante.

??? info "2. Installer les paquets nécessaires"
    **Objectif :** Installer les outils système nécessaires à Python, Git, pipx, au connecteur MariaDB et à la compilation du CSS (Node.js).

    !!! note "Paquets propres au backend MariaDB"
        `libmariadb-dev`, `pkg-config`, `build-essential` et `python3-dev` ne servent qu'à compiler le connecteur Python du backend **MariaDB**.
        Si vous utilisez le backend `forge-mvc-sqlite`, aucun de ces paquets n'est nécessaire : SQLite est fourni par la bibliothèque standard de Python.

    !!! warning "Attention"
        Pour le backend MariaDB, le paquet `libmariadb-dev` est important : sans lui, l'installation du connecteur Python `mariadb` peut échouer.

    ```bash
    sudo apt install -y \
      python3 \
      python3-venv \
      python3-pip \
      pipx \
      git \
      curl \
      openssl \
      build-essential \
      python3-dev \
      libmariadb-dev \
      pkg-config
    ```

    Le paquet `libmariadb-dev` fournit `mariadb_config`, requis par le connecteur Python `mariadb`.
    Vérifiez sa présence :

    ```bash
    mariadb_config --version
    ```

    Si cette commande échoue, l'installation de Forge peut échouer avec une erreur du type `mariadb_config not found`.

    **Node.js 24 (compilation du CSS)**

    Le squelette Forge compile ses styles avec Tailwind CSS via npm.
    À la création du projet, `forge new` lance `npm install` puis `npm run build:css`.
    Le squelette exige **Node.js 24.17.0 ou plus récent** (`.nvmrc` et `engines` du `package.json`, avec `engine-strict`).

    Le paquet `nodejs` d'`apt` est souvent trop ancien.
    Installez Node.js 24 depuis le dépôt officiel NodeSource :

    ```bash
    curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
    sudo apt install -y nodejs
    ```

    Vérifiez la version installée :

    ```bash
    node --version
    npm --version
    ```

    `node --version` doit afficher une version `v24.x` ou plus récente.

    !!! note "Alternative : nvm"
        Si vous préférez gérer plusieurs versions de Node par utilisateur, installez [nvm](https://github.com/nvm-sh/nvm), puis, dans le dossier du projet, `nvm install` lira le fichier `.nvmrc` (24.17.0) et posera la bonne version automatiquement.

    ---

    !!! success "Validation attendue"
        `mariadb_config --version` répond et `node --version` affiche une version `v24.x` ou plus récente.

??? info "3. Activer pipx"
    **Objectif :** Rendre la commande `pipx` disponible dans le terminal courant.

    `pipx` installe la commande `forge` dans un environnement isolé du Python système.

    ```bash
    pipx ensurepath
    exec $SHELL -l
    ```

    Vérifiez que `pipx` répond :

    ```bash
    pipx --version
    ```

    ---

    !!! success "Validation attendue"
        `pipx --version` affiche une version.

??? info "4. Installer Forge"
    **Objectif :** Installer la commande `forge` depuis PyPI et vérifier qu'elle répond.

    !!! warning "Attention"
        Forge est installé avec `--pre` parce que la version affichée par cette documentation est une version bêta.

    Forge est publié sur PyPI sous la version :

    ```text
    {{forge_version}}
    ```

    Comme il s'agit d'une version bêta, l'option `--pre` est transmise à `pip` :

    ```bash
    pipx install --pip-args="--pre" forge-mvc
    ```

    Vérifiez l'installation :

    ```bash
    forge --version
    ```

    Pour mettre à jour Forge plus tard :

    ```bash
    pipx upgrade --pip-args="--pre" forge-mvc
    ```

    ---

    !!! success "Validation attendue"
        `forge --version` affiche la version de Forge installée.

??? info "5. Configurer Git sur le poste"
    **Objectif :** Configurer l'identité Git globale du poste avant la création des commits.

    !!! warning "Attention"
        `forge new` peut créer un commit initial. Si Git n'a pas d'identité configurée, ce commit peut échouer.

    Cette configuration identifie l'auteur des commits sur la machine.
    Elle est globale et ne concerne pas encore un projet précis.

    `forge new` crée un commit initial : Git doit donc connaître votre identité, sinon ce commit échoue.

    ```bash
    git config --global user.name "Votre Nom"
    git config --global user.email "votre.email@example.com"
    git config --global init.defaultBranch main
    ```

    Vérifiez :

    ```bash
    git config --global --list
    ```

    ---

    !!! success "Validation attendue"
        `git config --global --list` affiche au moins `user.name`, `user.email` et `init.defaultBranch=main`.

??? info "6. Installer et démarrer MariaDB"
    **Objectif :** Installer MariaDB Server sur le poste et démarrer le service.

    MariaDB Server appartient à la préparation du poste.
    Il n'a pas besoin d'être réinstallé à chaque projet.

    ```bash
    sudo apt install -y \
      mariadb-server \
      mariadb-client
    ```

    Démarrez MariaDB et activez-le au démarrage de la machine :

    ```bash
    sudo systemctl enable --now mariadb
    ```

    Vérifiez que le service est actif :

    ```bash
    systemctl status mariadb --no-pager
    ```

    ---

    !!! success "Validation attendue"
        `systemctl status mariadb --no-pager` indique que le service MariaDB est actif.

??? info "7. Vérifier l'accès administrateur MariaDB local"
    **Objectif :** Vérifier que l'administration locale MariaDB fonctionne avec `sudo mariadb`.

    Sur Debian, Ubuntu et leurs dérivées, l'administration locale se fait souvent avec le compte système `root`, via `sudo`.

    ```bash
    sudo mariadb
    ```

    Vous devez obtenir une invite :

    ```text
    MariaDB [(none)]>
    ```

    Quittez ensuite la console :

    ```sql
    exit;
    ```

    Le compte `root` MariaDB sert uniquement à l'administration locale via `sudo mariadb`.
    Il ne sert pas à faire tourner l'application.

    ---

    !!! success "Validation attendue"
        La console `MariaDB [(none)]>` s'ouvre avec `sudo mariadb`.

??? info "8. Vérifier que le poste est prêt"
    **Objectif :** Contrôler que le poste Linux est prêt pour créer un projet Forge.

    Sur le poste, ces commandes doivent répondre :

    ```bash
    forge --version
    pipx --version
    git --version
    node --version
    npm --version
    mariadb_config --version
    systemctl status mariadb --no-pager
    ```

    Si ces commandes fonctionnent, le poste est prêt pour créer des projets Forge.

    ---

    !!! success "Validation attendue"
        Les commandes `forge`, `pipx`, `git`, `node`, `npm`, `mariadb_config` et `systemctl status mariadb` répondent.

## Partie 2 - Créer et configurer un projet Forge

Cette partie se refait pour chaque nouveau projet Forge.

Elle part du principe que le poste Linux est déjà prêt : Forge, Git, `pipx`, Node.js 24 et MariaDB sont installés.

??? info "1. Créer un nouveau projet Forge et installer son backend BDD"
    **Objectif :** Créer un nouveau projet Forge, entrer dans son environnement Python et y installer le backend base de données.

    Choisissez un nom de projet.
    Remplacez `NOM_PROJET` par votre nom réel, par exemple `boutique`, `blog`, `welcome-forge` ou `gestion-stock`.

    ```bash
    forge new NOM_PROJET
    cd NOM_PROJET
    ```

    `forge new` prépare un projet complet : squelette, environnement Python, certificat de développement, puis un dépôt Git avec un commit initial.
    Le projet créé est **agnostique en base de données** : il ne contient aucun backend tant que vous n'en installez pas un.

    Activez l'environnement Python du projet :

    ```bash
    source .venv/bin/activate
    ```

    Installez ensuite le backend base de données dans l'environnement du projet.
    Ce guide utilise MariaDB :

    ```bash
    pip install --pre forge-mvc-mariadb
    ```

    !!! note "Autre backend"
        Pour une base sans serveur, installez `forge-mvc-sqlite` à la place, et sautez les étapes propres à MariaDB (installation du serveur, création de la base et des comptes).
        Les backends `forge-mvc-postgres` et `forge-mvc-mssql` existent aussi ; consultez la documentation du backend choisi pour ses variables d'environnement.

    ---

    !!! success "Validation attendue"
        Le dossier du projet existe, l'environnement `.venv` est activable, le terminal se trouve dans le projet et `pip show forge-mvc-mariadb` affiche le backend installé.

??? info "2. Lire le fichier env/dev généré"
    **Objectif :** Lire le fichier `env/dev` généré et comprendre qu'il ne contient pas encore de configuration base de données.

    `forge new` a généré le fichier de configuration de développement :

    ```text
    env/dev
    ```

    Comme le squelette est agnostique en base de données (ADR-060), `env/dev` ne contient **aucune variable `DB_*`** juste après la création.
    Il porte le nom applicatif, le module de routes, le serveur, l'upload et les certificats.

    Exemple générique, juste après la création :

    ```env
    APP_NAME=NOM_PROJET
    APP_ROUTES_MODULE=mvc.routes

    # Base de données : aucune variable ici au départ.
    # Le backend installé (ici forge-mvc-mariadb) lit sa configuration dans
    # l'environnement. Vous ajoutez le bloc DB_* à l'étape « Compléter env/dev ».

    UPLOAD_MAX_SIZE=5242880

    APP_HOST=127.0.0.1
    APP_PORT=8000
    ```

    C'est vous qui ajoutez ensuite les variables de connexion attendues par le backend MariaDB (`DB_ADMIN_*`, `DB_APP_*`, `DB_NAME`).
    Vous choisissez donc librement le nom de la base et des comptes ; retenez ces valeurs, elles devront être identiques dans `env/dev` et dans les commandes MariaDB.

    ---

    !!! success "Validation attendue"
        `env/dev` existe et contient au moins `APP_NAME` et `APP_ROUTES_MODULE`, sans bloc `DB_*`.

??? info "3. Vérifier le dépôt Git local du projet"
    **Objectif :** Vérifier que le projet possède un dépôt Git local et un premier commit.

    !!! warning "Attention"
        Ne recréez pas un commit initial si Forge l'a déjà créé.

    `forge new` initialise en général le dépôt Git et crée un premier commit.
    Vérifiez d'abord l'état :

    ```bash
    git status
    git log --oneline -5
    ```

    Selon la version de Forge et le starter utilisé, le dépôt Git peut déjà être initialisé.
    Vérifiez d'abord avec `git status`.

    Si aucun dépôt n'est initialisé, ou si aucun commit n'a été créé, faites-le vous-même :

    ```bash
    git init
    git add .
    git commit -m "Initialisation du projet Forge"
    ```

    Ne refaites pas de commit initial si Forge en a déjà créé un.

    ---

    !!! success "Validation attendue"
        `git status` fonctionne et `git log --oneline -5` montre au moins un commit.

??? info "4. Publier le projet sur GitHub"
    **Objectif :** Publier le dépôt Git local du projet sur GitHub sans quitter la procédure principale.

    !!! warning "Attention"
        Le dépôt GitHub doit être vide au moment du premier push. Un README, un `.gitignore` ou une licence créés sur GitHub peuvent provoquer une divergence d'historique.

    Cette étape associe le dépôt Git local du projet Forge à un dépôt GitHub distant.

    Elle permet de sauvegarder le code du projet, de le partager entre plusieurs machines et de préparer un travail collaboratif.

    À la fin de cette étape :

    * le dépôt Git local est relié à GitHub ;
    * la branche principale s'appelle `main` ;
    * le premier push vers GitHub est effectué ;
    * les prochains envois pourront se faire avec un simple `git push`.

    ??? note "4.1 Vérifier que le dépôt Git local est prêt"
        Cette étape suppose que le dépôt Git local a déjà été préparé à l'étape précédente.

        Avant de publier le projet sur GitHub, vérifiez que vous êtes bien dans le dossier du projet Forge :

        ```bash
        pwd
        git status
        git log --oneline -5
        ```

        Le résultat attendu est :

        * `git status` ne doit pas indiquer que le dossier est hors d'un dépôt Git ;
        * le dépôt doit contenir au moins un commit ;
        * le dossier de travail doit être propre, ou ne contenir que des modifications que vous souhaitez envoyer.

        Si Git indique que le dossier n'est pas encore un dépôt, revenez à l'étape précédente pour initialiser le dépôt local avant de continuer.

        Cette étape ne recrée pas le dépôt Git local. Elle vérifie simplement qu'il est prêt à être relié à GitHub.

    ??? note "4.2 Choisir le protocole GitHub"
        GitHub peut être utilisé avec deux protocoles.

        | Protocole | Forme de l'URL | Usage recommandé |
        |---|---|---|
        | SSH | `git@github.com:UTILISATEUR/DEPOT.git` | recommandé pour un poste de développement |
        | HTTPS | `https://github.com/UTILISATEUR/DEPOT.git` | possible, mais nécessite un jeton d'accès personnel |

        Pour un poste de développement, le protocole SSH est recommandé.

        La suite de cette procédure utilise donc SSH comme chemin principal.

        Si vous choisissez HTTPS, utilisez l'URL HTTPS du dépôt à la place de l'URL SSH. GitHub ne s'authentifie pas avec le mot de passe du compte pour les opérations Git en HTTPS. Il faut utiliser un jeton d'accès personnel lorsque Git demande le mot de passe.

    ??? note "4.3 Vérifier l'authentification SSH GitHub"
        Avant de pousser le projet, GitHub doit reconnaître la machine depuis laquelle vous travaillez.

        Vérifiez si une clé SSH existe déjà :

        ```bash
        ls -la ~/.ssh/
        ```

        Si vous voyez déjà les fichiers suivants, une clé existe probablement :

        ```text
        id_ed25519
        id_ed25519.pub
        ```

        Si ces fichiers n'existent pas, créez une clé SSH :

        ```bash
        ssh-keygen -t ed25519 -C "votre.email@example.com"
        ```

        Validez les questions avec `Entrée` pour accepter les valeurs par défaut.

        Affichez ensuite la clé publique :

        ```bash
        cat ~/.ssh/id_ed25519.pub
        ```

        Copiez toute la ligne affichée.

        Dans GitHub :

        1. ouvrez **Settings** ;
        2. allez dans **SSH and GPG keys** ;
        3. cliquez sur **New SSH key** ;
        4. collez la clé publique ;
        5. validez avec **Add SSH key**.

        Vérifiez ensuite que GitHub reconnaît la machine :

        ```bash
        ssh -T git@github.com
        ```

        La réponse attendue ressemble à ceci :

        ```text
        Hi VOTRE_PSEUDO! You've successfully authenticated.
        ```

        Important : la clé SSH doit être celle de la machine qui lance `git push`.

        Si vous travaillez depuis une VM, un serveur distant, WSL ou un conteneur, c'est la clé de cet environnement qui doit être ajoutée à GitHub.

    ??? note "4.4 Créer le dépôt GitHub vide"
        Sur GitHub, créez un nouveau dépôt.

        Choisissez le nom du dépôt, par exemple :

        ```text
        mon-projet-forge
        ```

        Pendant la création du dépôt, ne cochez pas :

        * README ;
        * `.gitignore` ;
        * licence.

        Le dépôt GitHub doit être vide.

        Si GitHub crée un README ou une licence, il crée aussi un commit distant. Ce commit peut bloquer le premier push car l'historique distant et l'historique local ne sont pas les mêmes.

        Après création du dépôt, copiez l'URL SSH :

        ```text
        git@github.com:UTILISATEUR/NOM_DU_DEPOT.git
        ```

    ??? note "4.5 Associer le dépôt local au dépôt GitHub"
        Vérifiez d'abord si un remote existe déjà :

        ```bash
        git remote -v
        ```

        Si aucun remote n'apparaît, ajoutez le dépôt GitHub :

        ```bash
        git remote add origin git@github.com:UTILISATEUR/NOM_DU_DEPOT.git
        ```

        Remplacez :

        * `UTILISATEUR` par votre nom d'utilisateur GitHub ;
        * `NOM_DU_DEPOT` par le nom réel du dépôt GitHub.

        Si un remote `origin` existe déjà, ne le recréez pas.

        Vérifiez plutôt son URL :

        ```bash
        git remote -v
        ```

        Si l'URL est incorrecte, remplacez-la :

        ```bash
        git remote set-url origin git@github.com:UTILISATEUR/NOM_DU_DEPOT.git
        ```

    ??? note "4.6 Pousser le projet vers GitHub"
        Assurez-vous que la branche principale s'appelle `main` :

        ```bash
        git branch -M main
        ```

        Effectuez ensuite le premier push :

        ```bash
        git push -u origin main
        ```

        L'option `-u` lie la branche locale `main` à la branche distante `main`.

        Elle est nécessaire au premier push.

        Après cela, les prochains envois pourront se faire avec :

        ```bash
        git push
        ```

    ??? note "4.7 Variante avec GitHub CLI"
        Cette variante est optionnelle.

        Elle suppose que GitHub CLI est installé et déjà authentifié avec `gh auth login`.

        Pour créer un dépôt privé et pousser le projet :

        ```bash
        gh repo create NOM_DU_DEPOT --private --source=. --remote=origin --push
        ```

        Pour créer un dépôt public :

        ```bash
        gh repo create NOM_DU_DEPOT --public --source=. --remote=origin --push
        ```

        Si vous utilisez cette variante, vous pouvez passer les étapes manuelles de création du dépôt GitHub et d'ajout du remote.

    ??? failure "4.8 Résoudre les erreurs courantes du premier push"
        ??? note "Cas particulier : vous avez choisi HTTPS au lieu de SSH"
            Si vous avez choisi HTTPS, l'URL du dépôt ressemble à ceci :

            ```text
            https://github.com/UTILISATEUR/NOM_DU_DEPOT.git
            ```

            Dans ce cas, le remote doit être configuré avec l'URL HTTPS :

            ```bash
            git remote set-url origin https://github.com/UTILISATEUR/NOM_DU_DEPOT.git
            ```

            Au moment du push, Git peut demander :

            ```text
            Username:
            Password:
            ```

            Pour `Username`, indiquez votre nom d'utilisateur GitHub.

            Pour `Password`, n'indiquez pas le mot de passe du compte GitHub. Utilisez un jeton d'accès personnel GitHub.

            Si l'authentification échoue, vérifiez :

            * que le jeton n'est pas expiré ;
            * que le jeton a les droits nécessaires sur le dépôt ;
            * que le remote utilise bien une URL HTTPS ;
            * qu'un ancien identifiant GitHub n'est pas encore stocké dans le gestionnaire d'identifiants du système.

            Pour un poste de développement régulier, SSH reste plus simple à maintenir.

        ??? failure "Erreur : la branche n'a pas de branche distante liée"
            Message possible :

            ```text
            fatal: The current branch main has no upstream branch
            ```

            Cause : vous avez lancé `git push` au lieu du premier push complet.

            Correction :

            ```bash
            git push -u origin main
            ```

        ??? failure "Erreur : GitHub refuse la clé SSH"
            Message possible :

            ```text
            git@github.com: Permission denied (publickey)
            ```

            Cause : GitHub ne reconnaît pas la clé SSH de cette machine.

            Vérifiez d'abord l'authentification :

            ```bash
            ssh -T git@github.com
            ```

            Si le test échoue, reprenez l'étape 4.3.

            Si le test réussit mais que le push échoue encore, chargez la clé dans l'agent SSH :

            ```bash
            eval "$(ssh-agent -s)"
            ssh-add ~/.ssh/id_ed25519
            git push -u origin main
            ```

        ??? failure "Erreur : le dépôt distant contient déjà un commit"
            Message possible :

            ```text
            ! [rejected] main -> main
            fetch first
            non-fast-forward
            ```

            Cause probable : un README, un `.gitignore` ou une licence a été ajouté sur GitHub lors de la création du dépôt.

            Correction :

            ```bash
            git pull origin main --allow-unrelated-histories --no-rebase
            git push -u origin main
            ```

            L'option `--allow-unrelated-histories` permet de fusionner deux historiques qui ont démarré séparément.

            L'option `--no-rebase` choisit une fusion simple.

            Si Git ouvre un éditeur pour le message de fusion :

            * dans nano : `Ctrl+O`, puis `Entrée`, puis `Ctrl+X` ;
            * dans vim : `:wq`, puis `Entrée`.

            Pour éviter que Git redemande la stratégie de fusion plus tard :

            ```bash
            git config --global pull.rebase false
            ```

        ??? failure "Erreur : le remote origin existe déjà"
            Message possible :

            ```text
            error: remote origin already exists.
            ```

            Cause : un remote `origin` est déjà configuré.

            Vérifiez son URL :

            ```bash
            git remote -v
            ```

            Si elle est correcte, continuez directement avec le push :

            ```bash
            git push -u origin main
            ```

            Si elle est incorrecte, remplacez-la :

            ```bash
            git remote set-url origin git@github.com:UTILISATEUR/NOM_DU_DEPOT.git
            git push -u origin main
            ```

    ??? note "4.9 Vérifier que le projet est bien publié"
        Après le push, vérifiez l'état Git :

        ```bash
        git status
        git remote -v
        git branch -vv
        ```

        Vous devez voir que :

        * le dépôt local est propre ;
        * `origin` pointe vers GitHub ;
        * la branche `main` suit `origin/main`.

        Vous pouvez aussi ouvrir le dépôt GitHub dans le navigateur et vérifier que les fichiers du projet Forge sont présents.

        Le projet est maintenant publié sur GitHub.

        ---

    !!! success "Validation attendue"
        Le dépôt local est relié à GitHub, `origin` pointe vers le bon dépôt et `main` suit `origin/main`.

??? info "5. Ajouter la configuration MariaDB à env/dev"
    **Objectif :** Ajouter à `env/dev` le bloc de configuration du backend MariaDB, avant de créer la base et les comptes.

    !!! warning "Attention"
        `env/dev` contient des secrets de développement. Il ne doit pas être publié tel quel si votre projet le considère comme local.

    Cette étape appartient au projet.
    Elle se refait pour chaque nouveau projet Forge, car chaque projet possède sa propre base et son propre compte applicatif.

    Comme le squelette est agnostique en base de données, `env/dev` ne contient pas encore ces variables : c'est le backend MariaDB installé à l'étape 1 qui les lit dans l'environnement.
    Vous les ajoutez donc ici.

    Ouvrez le fichier `env/dev` :

    ```bash
    nano env/dev
    ```

    Ajoutez le bloc de variables MariaDB suivant :

    ```env
    DB_ADMIN_HOST=localhost
    DB_ADMIN_PORT=3306
    DB_ADMIN_LOGIN=forge_admin
    DB_ADMIN_PWD=mot_de_passe_admin_local

    DB_NAME=NOM_BASE
    DB_CHARSET=utf8mb4
    DB_COLLATION=utf8mb4_unicode_ci

    DB_APP_HOST=localhost
    DB_APP_PORT=3306
    DB_APP_LOGIN=NOM_UTILISATEUR_APP
    DB_APP_PWD=mot_de_passe_app_local
    DB_POOL_SIZE=5
    ```

    Remplacez :

    * `NOM_BASE` par le nom réel de la base du projet ;
    * `NOM_UTILISATEUR_APP` par le nom réel du compte applicatif ;
    * `mot_de_passe_admin_local` par le mot de passe local du compte `forge_admin` ;
    * `mot_de_passe_app_local` par le mot de passe local du compte applicatif.

    Le nom de la base et le nom du compte applicatif peuvent reprendre le nom du projet, à condition de rester cohérents dans toute la procédure.

    À partir de maintenant, les valeurs de `env/dev` sont la référence.
    L'étape suivante crée la base et les comptes MariaDB à partir de ces valeurs.

    ---

    !!! success "Validation attendue"
        `env/dev` contient les valeurs définitives de `DB_NAME`, `DB_ADMIN_LOGIN`, `DB_ADMIN_PWD`, `DB_APP_LOGIN` et `DB_APP_PWD`.

??? info "6. Créer la base et les comptes MariaDB du projet"
    **Objectif :** Créer dans MariaDB la base et les comptes déclarés dans `env/dev`.

    !!! warning "Attention"
        Les valeurs utilisées dans MariaDB doivent correspondre exactement aux valeurs renseignées dans `env/dev`.

    Forge sépare trois niveaux d'accès :

    ```text
    root                -> administration locale du serveur, avec sudo
    forge_admin         -> préparation de la base et application des migrations
    DB_APP_LOGIN        -> accès applicatif au runtime, en lecture/écriture
    ```

    `forge db:init` se connecte avec le compte indiqué dans `DB_ADMIN_LOGIN`.
    Ce compte doit déjà exister : Forge ne le crée pas.
    Le compte recommandé est `forge_admin`.

    Relisez d'abord les valeurs du projet :

    ```bash
    grep -E '^(DB_NAME|DB_ADMIN_LOGIN|DB_APP_LOGIN)=' env/dev
    ```

    Ouvrez ensuite une console MariaDB administrateur :

    ```bash
    sudo mariadb
    ```

    Exécutez les commandes SQL suivantes en remplaçant les valeurs par celles de `env/dev` :

    ```sql
    CREATE DATABASE IF NOT EXISTS `NOM_BASE`
      CHARACTER SET utf8mb4
      COLLATE utf8mb4_unicode_ci;

    CREATE USER IF NOT EXISTS 'forge_admin'@'localhost'
      IDENTIFIED BY 'mot_de_passe_admin_local';

    CREATE USER IF NOT EXISTS 'NOM_UTILISATEUR_APP'@'localhost'
      IDENTIFIED BY 'mot_de_passe_app_local';

    GRANT CREATE USER ON *.* TO 'forge_admin'@'localhost';

    GRANT CREATE, ALTER, DROP, INDEX, REFERENCES,
          SELECT, INSERT, UPDATE, DELETE
    ON `NOM_BASE`.* TO 'forge_admin'@'localhost'
    WITH GRANT OPTION;

    GRANT SELECT, INSERT, UPDATE, DELETE
    ON `NOM_BASE`.* TO 'NOM_UTILISATEUR_APP'@'localhost';
    ```

    Quittez ensuite la console :

    ```sql
    exit;
    ```

    Précisions :

    * `NOM_BASE` doit reprendre exactement la valeur de `DB_NAME` ;
    * `NOM_UTILISATEUR_APP` doit reprendre exactement la valeur de `DB_APP_LOGIN` ;
    * `mot_de_passe_admin_local` doit reprendre exactement la valeur de `DB_ADMIN_PWD` ;
    * `mot_de_passe_app_local` doit reprendre exactement la valeur de `DB_APP_PWD` ;
    * si `DB_NAME` contient un tiret, les backticks sont indispensables : `` `mon-projet` `` ;
    * si `DB_APP_LOGIN` contient un tiret, gardez les quotes SQL : `'mon-projet'@'localhost'` ;
    * le compte admin n'a pas besoin du privilège `RELOAD` : `forge db:init` n'émet pas de `FLUSH PRIVILEGES`, car `CREATE USER` et `GRANT` prennent effet immédiatement en MariaDB.

    ---

    !!! success "Validation attendue"
        La base, le compte `forge_admin` et le compte applicatif existent dans MariaDB, avec les mêmes valeurs que celles déclarées dans `env/dev`.

??? info "7. Vérifier le projet avec forge doctor"
    **Objectif :** Diagnostiquer le projet avec `forge doctor` avant l'initialisation de la base.

    ```bash
    forge doctor
    ```

    Cette commande diagnostique le projet et signale les points à corriger avant l'initialisation.

    ---

    !!! success "Validation attendue"
        `forge doctor` ne signale plus de blocage avant l'initialisation de la base.

??? info "8. Initialiser la base avec forge db:init"
    **Objectif :** Initialiser la base Forge et préparer la table technique des migrations.

    !!! warning "Attention"
        Sur Debian, Ubuntu et dérivées, le compte `root` MariaDB utilise souvent `unix_socket`. Le compte recommandé pour Forge reste `forge_admin`.

    ```bash
    forge db:init
    ```

    Cette commande prépare la base du projet et crée la table technique `forge_migrations`, qui mémorise les migrations déjà appliquées.

    Si la commande s'arrête sur un message du type :

    ```text
    Aucun backend BDD installé. Le cœur de Forge est agnostique BDD (ADR-054) :
    installez un opt-in de backend, par exemple pip install forge-mvc-mariadb.
    ```

    C'est que le backend n'a pas été installé dans l'environnement du projet.
    Reprenez l'étape 1 et lancez `pip install --pre forge-mvc-mariadb` avec le `.venv` du projet activé.

    Si la commande s'arrête plutôt sur :

    ```text
    Connexion d'administration impossible. Vérifiez DB_ADMIN_* dans env/dev.
    ```

    Forge n'a pas pu se connecter avec le compte indiqué dans `DB_ADMIN_LOGIN`.
    À vérifier :

    * le compte existe dans MariaDB ;
    * le mot de passe correspond à `DB_ADMIN_PWD` ;
    * `DB_ADMIN_HOST` est correct, généralement `localhost` ;
    * `DB_ADMIN_PORT` est correct, généralement `3306` ;
    * le compte a été créé avec le même hôte que celui utilisé par Forge ;
    * `DB_ADMIN_PWD` n'est pas resté vide dans `env/dev`.

    Sur Debian, Ubuntu et leurs dérivées, le compte `root` MariaDB utilise souvent l'authentification `unix_socket`, ce qui peut échouer en connexion TCP.
    Le parcours recommandé reste donc de créer un compte `forge_admin`.

    ---

    !!! success "Validation attendue"
        `forge db:init` se termine sans erreur et la table technique des migrations est prête.

??? info "9. Lancer le serveur de développement"
    Objectif : démarrer le serveur Forge en mode développement et ouvrir le projet dans le navigateur.

    Avant de lancer le serveur, vérifiez le port configuré dans `env/dev`.

    ```bash
    grep -E "^APP_PORT=" env/dev
    ```

    Exemple attendu :

    ```text
    APP_PORT=8000
    ```

    Le serveur de développement utilisera ce port au démarrage.

    Si le port est déjà utilisé par une autre application, modifiez la valeur dans `env/dev`, par exemple :

    ```env
    APP_PORT=8001
    ```

    Lancez ensuite le serveur :

    ```bash
    forge run
    ```

    Ouvrez le projet dans le navigateur en utilisant le port configuré
    (HTTPS de développement, certificat auto-signé généré par `forge new`) :

    ```text
    https://127.0.0.1:8000
    ```

    Si vous avez modifié `APP_PORT`, adaptez l'adresse.

    Exemple :

    ```text
    http://127.0.0.1:8001
    ```

    !!! success "Validation attendue"
        La page d'accueil du projet Forge doit s'afficher dans le navigateur.

        Le port utilisé dans l'URL doit correspondre à la valeur configurée dans `env/dev`.

    ??? failure "En cas d'erreur : le port est déjà utilisé"
        Si le terminal indique que le port est déjà utilisé, choisissez un autre port dans `env/dev`.

        Exemple :

        ```env
        APP_PORT=8001
        ```

        Relancez ensuite le serveur :

        ```bash
        forge run
        ```

        Ouvrez enfin l'adresse correspondante dans le navigateur :

        ```text
        http://127.0.0.1:8001
        ```

!!! success "Validation finale"
    Le projet Forge est correctement installé si :

    * le serveur démarre avec `forge run` ;
    * le port utilisé correspond à la valeur `APP_PORT` configurée dans `env/dev` ;
    * la page d'accueil du projet s'affiche dans le navigateur ;
    * aucune erreur bloquante n'apparaît dans le terminal.

    Le projet est maintenant prêt pour le développement.

## Poursuivre

Votre projet Forge est maintenant installé, configuré et lancé.

La suite logique est de suivre le parcours du starter **Welcome Forge**.
Il sert à prendre en main un projet Forge réel, étape par étape, sans partir directement dans les sujets avancés.

Vous y verrez notamment :

* l'organisation d'un projet Forge ;
* le rôle des routes ;
* le rôle des contrôleurs ;
* le rôle des vues ;
* l'utilisation de `forge run` ;
* les premières modifications à réaliser dans le projet.

Commencer le parcours : [Welcome Forge](../starters/welcome-forge/index.md)

## Approfondir 

Après le parcours Welcome Forge, vous pourrez revenir vers les pages techniques selon vos besoins :

* [Bases de données (backends)](../guide/bases-de-donnees.md) : choisir et configurer un backend (MariaDB, SQLite, PostgreSQL, SQL Server), `db:init`, comptes et migrations.
* [Installer les opt-ins Forge](opt-ins.md) : extensions officielles du framework.
* [Préparer un déploiement en production](production.md) : serveur, WSGI et reverse proxy.
* [Installer Forge depuis les sources GitHub](github.md) : contribuer ou travailler depuis le dépôt source.
