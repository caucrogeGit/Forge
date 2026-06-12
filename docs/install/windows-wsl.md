# Préparer WSL2 pour Forge sur Windows

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page explique comment préparer un poste Windows pour utiliser Forge dans un environnement Linux avec WSL2.

Elle ne remplace pas la procédure Linux.
Elle prépare simplement Ubuntu sous Windows, puis vous renvoie vers l’installation standard sur Debian, Ubuntu et leurs dérivées.

---

## Objectif

À la fin de cette page, vous devez disposer :

* de WSL2 activé sur Windows ;
* d’une distribution Ubuntu installée ;
* d’un terminal Ubuntu fonctionnel ;
* d’un dossier de travail Linux prêt pour vos projets Forge ;
* de VS Code connecté à WSL si vous souhaitez développer depuis Windows.

Une fois cette préparation terminée, l’installation de Forge continue ici :

[Installation sur Debian, Ubuntu et leurs dérivées](poste-linux.md)

---

## Pourquoi utiliser WSL2 ?

Forge est conçu pour fonctionner naturellement dans un environnement Linux.

Sous Windows, la solution recommandée est WSL2, car elle permet d’utiliser une vraie distribution Linux sans installer une machine virtuelle complète.

Le principe est le suivant :

```text
Windows 11
└── WSL2
    └── Ubuntu
        └── Projets Forge
```

Vous utilisez Windows pour l’interface, mais Forge, Python, MariaDB, Git et les fichiers du projet fonctionnent côté Linux.

---

## Prérequis

Avant de commencer, il faut disposer :

* d’un poste Windows 11 ;
* d’un compte administrateur sur la machine ;
* d’une connexion Internet ;
* de VS Code installé côté Windows si vous voulez travailler avec un éditeur graphique.

WSL2 fonctionne aussi sur certaines versions de Windows 10, mais Windows 11 reste le parcours le plus simple.

---

## Installer WSL2 et Ubuntu

Ouvrir PowerShell en mode administrateur.

Installer Ubuntu avec WSL :

```powershell
wsl --install -d Ubuntu-24.04
```

Redémarrer Windows si l’installation le demande.

Au premier lancement d’Ubuntu, Windows demande de créer :

* un nom d’utilisateur Linux ;
* un mot de passe Linux.

Ce compte Linux sera utilisé pour travailler dans Ubuntu.

---

## Vérifier Ubuntu

Ouvrir le terminal Ubuntu depuis le menu Démarrer.

Vérifier la version installée :

```bash
lsb_release -a
```

Le résultat doit indiquer Ubuntu 24.04 ou une version compatible.

Mettre Ubuntu à jour :

```bash
sudo apt update
sudo apt upgrade -y
```

À ce stade, Ubuntu est prêt à recevoir les outils nécessaires à Forge.

---

## Créer un dossier de travail Linux

Créer un dossier pour les projets :

```bash
mkdir -p ~/Projets
cd ~/Projets
```

Les projets Forge doivent être créés dans ce dossier ou dans un autre dossier situé dans le système de fichiers Linux.

Exemple recommandé :

```text
~/Projets/MonProjet
```

---

## Point important : ne pas travailler dans `/mnt/c`

WSL permet d’accéder aux fichiers Windows depuis Linux avec des chemins comme :

```text
/mnt/c/Users/...
```

Pour Forge, ce n’est pas recommandé.

Un projet Forge doit rester dans le système de fichiers Linux, par exemple :

```text
~/Projets/MonProjet
```

Éviter :

```text
/mnt/c/Users/VotreNom/Documents/MonProjet
```

Travailler dans `/mnt/c` peut provoquer :

* des ralentissements importants ;
* des problèmes de permissions ;
* des comportements Git incohérents ;
* des problèmes avec les outils Python ;
* des difficultés avec MariaDB ou les fichiers générés.

La règle simple :

```text
Le code Forge reste côté Linux.
Windows sert à afficher l’éditeur et le navigateur.
```

---

## Installer VS Code côté Windows

Installer Visual Studio Code sur Windows si ce n’est pas déjà fait.

Ensuite, installer l’extension officielle :

```text
WSL
```

Nom technique de l’extension :

```text
ms-vscode-remote.remote-wsl
```

Cette extension permet à VS Code de se connecter à Ubuntu et d’éditer directement les fichiers Linux.

---

## Ouvrir Ubuntu dans VS Code

Depuis le terminal Ubuntu :

```bash
cd ~/Projets
code .
```

Au premier lancement, VS Code installe automatiquement son serveur distant dans WSL.

L’interface reste côté Windows, mais les fichiers ouverts sont bien ceux d’Ubuntu.

Pour un projet Forge, le principe sera ensuite :

```bash
cd ~/Projets/MonProjet
code .
```

---

## Vérifier que WSL est prêt

Depuis Ubuntu, vérifier les points suivants :

```bash
pwd
```

Le résultat doit ressembler à :

```text
/home/votre_utilisateur
```

Vérifier que le dossier de projets existe :

```bash
ls -la ~/Projets
```

Vérifier que VS Code peut s’ouvrir depuis Ubuntu :

```bash
code .
```

Si ces commandes fonctionnent, la préparation WSL est terminée.

---

## Poursuivre l’installation de Forge

WSL est maintenant prêt.

La suite se fait comme sur un poste Linux classique, car Ubuntu sous WSL se comporte comme une distribution Linux.

Poursuivre avec : [Installation sur Debian, Ubuntu et leurs dérivées](poste-linux.md)

---

## Dépannage WSL

Si le serveur de développement Forge ne répond pas correctement sous WSL, consulter :

[Dépannage du serveur de développement sous WSL2](wsl-dev-server.md)

Cette page traite notamment :

* les ports déjà utilisés ;
* les problèmes HTTPS local ;
* les comportements particuliers de VS Code avec WSL ;
* les différences entre `localhost` Windows et Ubuntu.

---

## Résultat attendu

À la fin de cette préparation, l’environnement doit être dans cet état :

| Élément                    | Résultat attendu       |
| -------------------------- | ---------------------- |
| WSL2                       | activé                 |
| Ubuntu                     | installé et à jour     |
| Terminal Ubuntu            | fonctionnel            |
| Dossier `~/Projets`        | créé                   |
| Projet placé dans `/mnt/c` | non                    |
| VS Code Remote WSL         | fonctionnel si utilisé |
