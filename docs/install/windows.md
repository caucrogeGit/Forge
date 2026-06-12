# Installation sur Windows 11

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Forge est conçu pour Linux et macOS. Sur Windows, **la voie recommandée est WSL2**
(Windows Subsystem for Linux 2), qui fournit un environnement Linux complet directement
dans Windows 11.

---

## Pourquoi WSL2 et pas Windows natif ?

Forge utilise des conventions Unix (chemins, permissions, scripts shell) qui s'intègrent
mal au système de fichiers Windows. WSL2 fournit une distribution Linux native sans
virtualisation lourde, ce qui permet d'utiliser Forge exactement comme sur un poste Linux.

C'est l'approche recommandée par l'écosystème Python web (Django, Flask et FastAPI
font de même).

---

## Prérequis

- Windows 11 (ou Windows 10 version 2004+)
- Privilèges administrateur sur le poste

---

## Étape 1 — Installer WSL2 + Ubuntu

Suivez la procédure officielle Microsoft :

→ [Documentation Microsoft : Installer WSL2](https://learn.microsoft.com/fr-fr/windows/wsl/install)

En résumé, dans un terminal PowerShell en mode administrateur :

```powershell
wsl --install
```

Cette commande installe Ubuntu par défaut. Redémarrez Windows si demandé, puis ouvrez
un terminal Ubuntu.

---

## Étape 2 — Installer Forge dans WSL2

Une fois Ubuntu lancé, les étapes sont identiques à Linux :

```bash
# Mise à jour du système Ubuntu
sudo apt update && sudo apt upgrade -y

# Python 3.12 (Forge requiert >= 3.12)
sudo apt install -y python3 python3-venv python3-pip

# Vérification
python3 --version   # doit afficher Python 3.12+

# Installation de Forge via pipx (recommandé)
sudo apt install -y pipx
pipx install forge-mvc
pipx ensurepath
source ~/.bashrc    # ou ouvrir un nouveau terminal

# Vérification
forge --version     # doit afficher Forge {{forge_version}}
```

---

## Étape 3 — Créer un projet

```bash
forge new MonProjet
cd MonProjet
```

Puis suivre le [Guide de démarrage](../guide/getting-started.md) normalement.

---

## Accès aux fichiers

Les fichiers créés dans WSL2 sont dans `~/` (répertoire home Linux).
Depuis Windows, ils sont accessibles via l'explorateur de fichiers sous
`\\wsl$\Ubuntu\home\<utilisateur>\`.

Pour éditer avec VS Code depuis Windows :

```bash
# Dans le terminal Ubuntu
code .   # ouvre VS Code côté Windows avec connexion WSL
```

VS Code détecte automatiquement WSL2 et propose l'extension Remote WSL.

---

## MariaDB dans WSL2

Forge nécessite MariaDB. Dans WSL2 :

```bash
sudo apt install -y mariadb-server
sudo service mariadb start
sudo mysql_secure_installation
```

Puis suivre [Préparer MariaDB](mariadb.md).

---

## Frictions connues — Windows natif (sans WSL2)

Si vous souhaitez expérimenter Forge nativement sur Windows sans WSL2, les
frictions suivantes peuvent apparaître :

- **Chemins** : certaines opérations sur fichiers utilisent des séparateurs Unix (`/`)
- **Permissions** : `chmod` est ignoré silencieusement sous Windows
- **MariaDB** : installation différente (MSI Windows vs `apt`)
- **Tests** : certains tests dépendent du système Unix et peuvent échouer
- **forge sync:landing** : dépend de commandes shell Unix

Ces frictions ne sont pas testées ni supportées dans Forge {{forge_version}}. Les contributions
pour le support natif Windows sont bienvenues, mais non planifiées.

---

## Voir aussi

- [Poste Linux (pipx)](poste-linux.md)
- [Préparer MariaDB](mariadb.md)
- [Démarrer avec Forge](../guide/getting-started.md)
