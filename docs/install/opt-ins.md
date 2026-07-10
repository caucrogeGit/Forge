# Contrat d’installation des opt-ins Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page explique le contrat d’installation des opt-ins Forge.

Un opt-in Forge est une brique officielle optionnelle.
Il ajoute une capacité au framework sans alourdir le core.

Exemples :

* `forge-mvc-iot` pour les fonctions IoT ;
* `forge-mvc-rbac` pour les rôles et permissions ;
* `forge-mvc-files` pour les fichiers ;
* `forge-mvc-images` pour les images ;
* `forge-mvc-video` pour la vidéo ;
* `forge-mvc-mail` pour le mail.

Le principe est simple :

```text
Forge Core reste minimal.
Chaque opt-in s'installe explicitement.
Chaque opt-in se branche explicitement quand le projet en a besoin.
```

---

## Objectif

À la fin de cette page, vous devez savoir :

* ce qu’est un opt-in Forge ;
* comment lister les opt-ins disponibles ;
* comment installer le package d’un opt-in ;
* comment le brancher dans un projet quand c’est nécessaire ;
* quelle différence existe entre installation et activation ;
* quelles pages consulter pour approfondir chaque brique.

---

## Core Forge et opt-ins

Forge est séparé en deux niveaux.

| Élément       | Rôle                 | Installation                |
| ------------- | -------------------- | --------------------------- |
| `forge-mvc`   | Core du framework    | Obligatoire                 |
| `forge-mvc-*` | Briques optionnelles | Selon les besoins du projet |

Le core fournit la structure principale :

* CLI Forge ;
* routing ;
* contrôleurs ;
* vues ;
* sécurité ;
* base de données ;
* migrations ;
* génération ;
* conventions projet.

Les opt-ins ajoutent des capacités spécialisées :

* IoT ;
* fichiers ;
* images ;
* audio ;
* vidéo ;
* mail ;
* RBAC ;
* MFA ;
* workflow ;
* statistiques ;
* pivot enrichi ;
* internationalisation.

Le core ne doit pas dépendre automatiquement de tous les opt-ins.
Cette séparation garde Forge plus léger, plus lisible et plus maîtrisable.

---

## Les deux étapes d’un opt-in

L’utilisation d’un opt-in peut demander deux gestes distincts.

```text
1. Installer le package Python.
2. Brancher l’opt-in dans le projet si la brique en a besoin.
```

Ces deux étapes ne font pas la même chose.

| Étape        | Ce qu’elle fait                        | Exemple                      |
| ------------ | -------------------------------------- | ---------------------------- |
| Installation | Rend le package Python disponible      | `forge-mvc-iot` est installé |
| Branchement  | Ajoute la couche locale dans le projet | `optins/iot/` est créé       |

Certains opt-ins sont de simples bibliothèques : ils s’installent, puis s’utilisent par import ou par commande.

D’autres opt-ins ajoutent des routes, des vues ou une intégration projet.
Dans ce cas, ils doivent aussi être branchés explicitement.

---

## Lister les opt-ins disponibles

Depuis un projet Forge :

```bash
forge opt-in:list
```

Cette commande affiche les opt-ins officiels et leur état local.

Elle est en lecture seule.

Elle ne crée aucun fichier, n’installe aucun package et ne modifie pas le projet.

---

## Obtenir la commande d’installation d’un opt-in

Forge fournit une commande d’aide :

```bash
forge opt-in:install iot
```

Cette commande n’installe rien directement.

Elle affiche la commande adaptée à votre environnement :

* installation dans l’environnement Python courant ;
* ou injection dans l’environnement `pipx` de Forge si Forge est installé via `pipx`.

Exemple de sortie possible avec `pipx` :

```bash
pipx inject forge-mvc forge-mvc-iot --pip-args="--pre"
```

Exemple de sortie possible dans un environnement virtuel actif :

```bash
python -m pip install --pre forge-mvc-iot
```

Le choix d’afficher la commande plutôt que de l’exécuter automatiquement est volontaire : l’installation d’un opt-in reste un geste explicite du développeur.

---

## Installer un opt-in dans un projet Forge

Depuis le dossier du projet :

```bash
source .venv/bin/activate
```

Demander la commande d’installation :

```bash
forge opt-in:install iot
```

Copier puis lancer la commande proposée.

Vérifier ensuite que l’opt-in est visible :

```bash
forge opt-in:list
```

---

## Brancher un opt-in dans le projet

Pour les opt-ins qui nécessitent une intégration locale, Forge utilise la commande :

```bash
forge opt-in:enable <nom>
```

Par défaut, cette commande travaille en simulation.

Exemple avec l’opt-in IoT :

```bash
forge opt-in:enable iot
```

Cette commande affiche ce qui serait créé ou modifié, sans écrire dans le projet.

Pour appliquer réellement le branchement :

```bash
forge opt-in:enable iot --apply
```

Le branchement peut créer une couche locale du type :

```text
optins/
└── iot/
    └── routes.py
```

Il peut aussi ajouter le point de branchement nécessaire dans les routes du projet.

---

## Vérifier l’état après branchement

Après installation et branchement :

```bash
forge opt-in:list
```

Puis vérifier le projet :

```bash
forge doctor
```

Si l’opt-in ajoute des migrations, des routes ou une configuration spécifique, consulter la page dédiée de l’opt-in.

---

## Liste des opt-ins officiels

| Identifiant       | Package                    | Rôle principal                                     |
| ----------------- | -------------------------- | -------------------------------------------------- |
| `admin`           | `forge-mvc-admin`          | Back-office applicatif (CRUD générique, auth, RBAC) |
| `audio`           | `forge-mvc-audio`          | Upload, sondage, transcodage MP3 et lecture audio  |
| `audit`           | `forge-mvc-audit`          | Journal d’audit applicatif (table `audit_log`)     |
| `deploy`          | `forge-mvc-deploy`         | Outillage de déploiement (`deploy:init`, `deploy:check`) |
| `entities`        | `forge-mvc-entities`       | Moteur d’entités (`make:entity/crud`, `migration:*`, pivot) |
| `files`           | `forge-mvc-files`          | Upload générique, stockage et service de fichiers  |
| `i18n`            | `forge-mvc-i18n`           | Internationalisation, catalogues et traduction     |
| `images`          | `forge-mvc-images`         | Traitement d’images et médias applicatifs          |
| `import-export`   | `forge-mvc-import-export`  | Échange CSV (import validé, export `to_csv`)       |
| `iot`             | `forge-mvc-iot`            | Réception MQTT, stockage et API HTTP IoT           |
| `jobs`            | `forge-mvc-jobs`           | File de tâches de fond adossée à la base           |
| `mail`            | `forge-mvc-mail`           | Composition et envoi d’e-mails                     |
| `mfa`             | `forge-mvc-mfa`            | Authentification multi-facteurs                    |
| `notifications`   | `forge-mvc-notifications`  | Notifications in-app (table `notifications`)       |
| `qrcode`          | `forge-mvc-qrcode`         | Génération de QR Codes (PNG/SVG)                   |
| `rbac`            | `forge-mvc-rbac`           | Rôles, permissions et contrôle d’accès             |
| `settings`        | `forge-mvc-settings`       | Paramètres applicatifs persistés (`app_settings`)  |
| `stats`           | `forge-mvc-stats`          | Agrégats et compteurs                              |
| `video`           | `forge-mvc-video`          | Upload, transcodage MP4 et lecture vidéo           |
| `workflow`        | `forge-mvc-workflow`       | Statuts et transitions applicatives                |

Le moteur d’entités `entities` fournit les commandes de modélisation (`make:entity`, `make:crud`, `migration:*`, pivot enrichi ; ADR-070).
Une fois installé, ses commandes sont découvertes automatiquement par la CLI.

---

## Installer directement un package

Il est aussi possible d’installer directement un opt-in par son nom de package.

Exemple :

```bash
python -m pip install --pre forge-mvc-iot
```

Ou avec `pipx` si Forge est installé globalement par `pipx` :

```bash
pipx inject forge-mvc forge-mvc-iot --pip-args="--pre"
```

La commande `forge opt-in:install <nom>` reste recommandée, car elle affiche la commande adaptée à l’environnement courant.

---

## Installer plusieurs opt-ins

Installer plusieurs opt-ins est possible, mais il faut éviter de tout installer par réflexe.

La règle recommandée est :

```text
Installer seulement les briques nécessaires au projet.
```

Exemple :

```bash
python -m pip install --pre forge-mvc-files forge-mvc-images
```

Cette commande peut être pertinente pour un projet qui gère des images.

Pour un projet IoT :

```bash
python -m pip install --pre forge-mvc-iot
```

Pour un projet avec rôles et permissions :

```bash
python -m pip install --pre forge-mvc-rbac
```

---

## Cas particulier des extras

Le package `forge-mvc` peut exposer certains extras comme raccourcis d’installation.

Exemple :

```bash
python -m pip install --pre "forge-mvc[rbac]"
```

Les extras sont pratiques, mais ils ne sont pas le contrat principal.

Le contrat principal reste :

```text
un opt-in = un package forge-mvc-*
```

Exemple :

```bash
python -m pip install --pre forge-mvc-rbac
```

Cette forme est plus explicite et reste la plus lisible dans la documentation.

---

## Ce que l’installation ne fait pas automatiquement

Installer un package opt-in ne veut pas dire que tout est configuré dans le projet.

Selon la brique, il peut rester à faire :

* brancher l’opt-in avec `forge opt-in:enable <nom> --apply` ;
* ajouter des variables dans `env/dev` ;
* initialiser des migrations ;
* appliquer des migrations SQL ;
* lancer une commande de diagnostic propre à l’opt-in ;
* consulter la documentation dédiée.

Exemple pour IoT :

```bash
forge opt-in:enable iot --apply
forge iot:doctor
forge iot:init
forge db:apply
```

Les commandes exactes dépendent de l’opt-in utilisé.

---

## Règle de sécurité

Un opt-in ne doit pas modifier le projet en silence.

Les commandes de branchement doivent rester explicites.

Quand une commande peut écrire dans le projet, elle doit annoncer ce qu’elle va faire et demander une application volontaire, par exemple avec :

```bash
--apply
```

Cette règle protège les fichiers du projet et évite les modifications cachées.

---

## Résultat attendu

Après installation et branchement d’un opt-in, les commandes suivantes doivent permettre de vérifier l’état du projet :

```bash
forge opt-in:list
forge doctor
```

Si l’opt-in possède une commande de diagnostic dédiée, l’utiliser également.

Exemple :

```bash
forge iot:doctor
```

---

## Poursuivre selon l’opt-in

Pour continuer, consulter la documentation dédiée à la brique installée :

* [Structure des opt-ins dans un projet Forge](../architecture/optins-project-structure.md)
* [Référence CLI : commandes `opt-in:*`](../reference/cli-commands.md#opt-ins-branchement-projet)
* Forge IoT
* Configuration Forge IoT
* [Migrations SQL](../features/migrations.md)
* [Préparer MariaDB](mariadb.md)
* [Installation sur Debian, Ubuntu et leurs dérivées](poste-linux.md)
