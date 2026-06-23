# 02 - Création du dépôt Forge-web

## 1. Objectif du tutoriel

Ce tutoriel décrit la procédure propre pour créer le projet local **Forge-web**, séparé du framework **Forge**.

Le projet **Forge-web** servira à publier le site officiel :

```text
https://forgemvc.com
```

Il contiendra progressivement :

- la landing page publique ;
- la documentation publique de Forge ;
- les sources MkDocs ;
- les notes d’infrastructure ;
- les scripts de génération ou de déploiement ;
- plus tard, les éléments nécessaires à la publication sur le serveur.

Ce projet ne doit pas modifier le cœur du framework Forge.

---

## 2. Principe général

Le framework **Forge** et le site **Forge-web** doivent rester séparés.

La séparation évite de mélanger :

- le développement du framework Python ;
- la documentation publique ;
- la landing page ;
- l’infrastructure de publication ;
- les notes DNS / HTTPS / Proxmox.

La bonne organisation est donc :

```text
/home/roger/Projets/
├── Forge/        # Framework Forge
└── Forge-web/    # Site officiel forgemvc.com
```

Cette séparation est importante. Le site web n’est pas une application métier Forge et ne doit pas devenir une extension du framework.

---

## 3. Résultat final attendu

À la fin de la procédure, on doit obtenir :

```text
Forge-web/
├── .git/
├── .gitignore
├── README.md
├── docs/
│   └── .gitkeep
├── infra/
│   └── .gitkeep
├── landing/
│   └── assets/
│       ├── css/
│       │   └── .gitkeep
│       ├── img/
│       │   └── .gitkeep
│       └── js/
│           └── .gitkeep
├── notes/
│   └── .gitkeep
└── scripts/
    └── .gitkeep
```

Le dépôt local doit être synchronisé avec GitHub :

```text
https://github.com/caucrogeGit/Forge-web.git
```

La branche principale doit être :

```text
main
```

---

## 4. Prérequis

Avant de commencer, il faut disposer de :

- Git installé ;
- Python installé ;
- un compte GitHub ;
- un dossier de travail local, ici `/home/roger/Projets`.

Vérification :

```bash
cd /home/roger/Projets
pwd
ls -la
git --version
python3 --version
```

Résultat attendu dans notre cas :

```text
/home/roger/Projets
git version 2.43.0
Python 3.12.3
```

Il faut aussi vérifier que le dossier `Forge-web` n’existe pas déjà :

```bash
test -e Forge-web && echo "ERREUR: Forge-web existe déjà" || echo "OK: Forge-web absent"
```

Résultat attendu :

```text
OK: Forge-web absent
```

---

## 5. Création de la structure du projet

On crée uniquement les dossiers nécessaires au démarrage.

```bash
cd /home/roger/Projets

mkdir -p Forge-web/{landing/assets/{css,js,img},docs,infra,notes,scripts}

find Forge-web -maxdepth 4 -type d | sort
```

Résultat attendu :

```text
Forge-web
Forge-web/docs
Forge-web/infra
Forge-web/landing
Forge-web/landing/assets
Forge-web/landing/assets/css
Forge-web/landing/assets/img
Forge-web/landing/assets/js
Forge-web/notes
Forge-web/scripts
```

### Explication des dossiers

| Dossier | Rôle |
|---|---|
| `landing/` | Contiendra la future page d’accueil statique de forgemvc.com |
| `landing/assets/css/` | Feuilles CSS de la landing page |
| `landing/assets/js/` | JavaScript éventuel de la landing page |
| `landing/assets/img/` | Logos, images et illustrations |
| `docs/` | Sources de documentation ou contenu public MkDocs |
| `infra/` | Notes ou fichiers d’infrastructure sans secrets |
| `notes/` | Notes de travail du projet Forge-web |
| `scripts/` | Scripts locaux de génération ou de déploiement |

Le dossier `site/` n’est pas créé manuellement ici. Il sera généré plus tard par MkDocs et ignoré par Git.

---

## 6. Création du README

Le fichier `README.md` sert à expliquer clairement le rôle du dépôt.

Créer le fichier :

```bash
cd /home/roger/Projets/Forge-web
nano README.md
```

Contenu recommandé :

```md
# Forge-web

Site officiel du framework Forge.

Objectif du projet :

- publier https://forgemvc.com ;
- héberger la landing page publique ;
- héberger la documentation Forge générée avec MkDocs ;
- préparer un déploiement statique simple ;
- garder ce projet séparé du framework Forge.

## Périmètre

Ce dépôt concerne uniquement Forge-web :

- landing page ;
- documentation publique ;
- génération statique ;
- notes d'infrastructure ;
- scripts de build et de déploiement.

Ce dépôt ne doit pas modifier le cœur du framework Forge.

## Structure initiale

- landing/ : source de la landing page statique ;
- docs/ : documentation publique ou sources MkDocs ;
- site/ : site généré, non versionné ;
- infra/ : notes et fichiers d'infrastructure sans secrets ;
- notes/ : notes de travail du projet ;
- scripts/ : scripts locaux de génération ou déploiement.

## Décision initiale

Le site sera statique dans un premier temps.

MkDocs servira à générer la documentation.

Le reverse proxy et HTTPS seront traités plus tard, probablement avec Caddy.

Proxmox ne doit jamais être exposé directement au public.
```

### Pourquoi ce README est important

Le README fixe dès le départ le périmètre du dépôt.

Il évite les dérives suivantes :

- transformer Forge-web en application Forge ;
- modifier le cœur du framework depuis ce dépôt ;
- mélanger site web, framework, mail, firewall et Proxmox ;
- placer des secrets dans le projet.

---

## 7. Création du `.gitignore`

Le fichier `.gitignore` indique à Git ce qu’il ne doit pas versionner.

Créer le fichier :

```bash
cd /home/roger/Projets/Forge-web
nano .gitignore
```

Contenu recommandé :

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# MkDocs / build statique
site/

# Environnements et secrets
.env
.env.*
*.key
*.pem
*.crt
secrets/
.envrc

# Système / éditeurs
.DS_Store
Thumbs.db
.vscode/
.idea/

# Logs
*.log
logs/
```

### Pourquoi ignorer `site/`

Le dossier `site/` sera généré automatiquement par MkDocs.

Il ne doit pas être versionné dans ce dépôt de sources, car il s’agit d’un artefact de build.

On versionne les sources, pas le résultat généré.

### Pourquoi ignorer les secrets

Le dépôt ne doit jamais contenir :

- mots de passe ;
- clés privées ;
- certificats privés ;
- tokens GitHub ;
- tokens Cloudflare ;
- fichiers `.env` réels.

C’est indispensable, surtout pour un projet destiné à être publié.

---

## 8. Ajout des fichiers `.gitkeep`

Git ne versionne pas les dossiers vides.

Pour conserver la structure initiale, on ajoute un fichier `.gitkeep` dans chaque dossier vide.

```bash
cd /home/roger/Projets/Forge-web

find . -type d -empty -exec touch {}/.gitkeep \;

find . -maxdepth 4 -type f | sort
```

Résultat attendu :

```text
./.gitignore
./README.md
./docs/.gitkeep
./infra/.gitkeep
./landing/assets/css/.gitkeep
./landing/assets/img/.gitkeep
./landing/assets/js/.gitkeep
./notes/.gitkeep
./scripts/.gitkeep
```

Attention : il ne faut pas garder de `.gitkeep` à la racine du projet. La racine contient déjà des fichiers, donc elle n’est pas vide.

Si un `.gitkeep` racine a été créé par erreur :

```bash
rm -f ./.gitkeep
```

---

## 9. Initialisation du dépôt Git local

Depuis la racine du projet :

```bash
cd /home/roger/Projets/Forge-web

git init
```

Puis vérifier l’état :

```bash
git status --short
```

Résultat attendu :

```text
?? .gitignore
?? README.md
?? docs/
?? infra/
?? landing/
?? notes/
?? scripts/
```

Les fichiers sont présents mais pas encore suivis par Git.

---

## 10. Ajout des fichiers à l’index Git

Ajouter les fichiers initiaux :

```bash
cd /home/roger/Projets/Forge-web

git add .gitignore README.md docs infra landing notes scripts
```

Vérifier :

```bash
git status --short
```

Résultat attendu :

```text
A  .gitignore
A  README.md
A  docs/.gitkeep
A  infra/.gitkeep
A  landing/assets/css/.gitkeep
A  landing/assets/img/.gitkeep
A  landing/assets/js/.gitkeep
A  notes/.gitkeep
A  scripts/.gitkeep
```

La lettre `A` signifie que Git va ajouter ces fichiers au prochain commit.

---

## 11. Premier commit local

Créer le premier commit :

```bash
cd /home/roger/Projets/Forge-web

git commit -m "init: create Forge-web project structure"
```

Vérifier :

```bash
git status --short
git log --oneline -1
git branch --show-current
```

Résultat attendu :

```text
a9e962e init: create Forge-web project structure
main
```

Le statut Git doit être propre, c’est-à-dire sans fichier modifié ou non suivi.

---

## 12. Création du dépôt GitHub

Créer un dépôt GitHub séparé nommé :

```text
Forge-web
```

Paramètres recommandés :

```text
Visibility : Private au départ
README     : non
.gitignore : non
License    : non
```

Il ne faut pas demander à GitHub de créer un README ou un `.gitignore`, car ces fichiers existent déjà localement.

Sinon GitHub créerait un historique différent, ce qui compliquerait le premier push.

Dépôt créé dans notre cas :

```text
https://github.com/caucrogeGit/Forge-web.git
```

---

## 13. Ajout du dépôt distant

Ajouter GitHub comme remote `origin` :

```bash
cd /home/roger/Projets/Forge-web

git remote add origin https://github.com/caucrogeGit/Forge-web.git
```

Vérifier :

```bash
git remote -v
```

Résultat attendu :

```text
origin  https://github.com/caucrogeGit/Forge-web.git (fetch)
origin  https://github.com/caucrogeGit/Forge-web.git (push)
```

---

## 14. Premier push vers GitHub

Envoyer la branche locale `main` vers GitHub :

```bash
cd /home/roger/Projets/Forge-web

git push -u origin main
```

Résultat attendu :

```text
[new branch]      main -> main
la branche 'main' est paramétrée pour suivre 'origin/main'.
```

L’option `-u` permet d’associer la branche locale `main` à la branche distante `origin/main`.

Après cela, les futurs pushs pourront se faire simplement avec :

```bash
git push
```

---

## 15. Vérification finale

Vérifier que tout est propre :

```bash
cd /home/roger/Projets/Forge-web

git status
git branch -vv
git log --oneline -1
git remote -v
```

Résultat attendu :

```text
Sur la branche main
Votre branche est à jour avec 'origin/main'.

rien à valider, la copie de travail est propre
```

La branche doit indiquer :

```text
main [origin/main]
```

Le dernier commit doit être :

```text
a9e962e init: create Forge-web project structure
```

Le remote doit être :

```text
origin  https://github.com/caucrogeGit/Forge-web.git (fetch)
origin  https://github.com/caucrogeGit/Forge-web.git (push)
```

---

## 16. État final obtenu

À la fin de cette procédure, le projet est correctement initialisé.

État obtenu :

```text
Forge-web local créé
Git local initialisé
Premier commit fait
Dépôt GitHub séparé créé
Remote origin ajouté
Premier push effectué
Branche main synchronisée avec origin/main
```

Le dépôt local est propre :

```text
rien à valider, la copie de travail est propre
```

---

## 17. Points de vigilance

### 17.1 Ne pas travailler dans le dépôt Forge

Avant toute commande, vérifier le dossier courant :

```bash
pwd
```

Le bon dossier est :

```text
/home/roger/Projets/Forge-web
```

Pas :

```text
/home/roger/Projets/Forge
```

### 17.2 Ne pas versionner le dossier `site/`

`site/` sera généré automatiquement.

Il doit rester dans `.gitignore`.

### 17.3 Ne pas stocker de secrets

Aucun secret ne doit être ajouté au dépôt.

Exemples interdits :

```text
.env
clé SSH privée
clé Cloudflare
clé GitHub
clé TLS privée
mot de passe serveur
```

### 17.4 HTTPS ou SSH pour GitHub

Le remote actuel utilise HTTPS :

```text
https://github.com/caucrogeGit/Forge-web.git
```

Ce n’est pas bloquant.

Si GitHub demande trop souvent une authentification, il sera possible plus tard de basculer en SSH :

```text
git@github.com:caucrogeGit/Forge-web.git
```

---

## 18. Conclusion

Le dépôt **Forge-web** est prêt.

Il est maintenant possible de passer à la suite du projet :

```text
03 — Landing page
```

La prochaine étape consistera à créer la première page publique statique de `forgemvc.com`, sans toucher au framework Forge.
