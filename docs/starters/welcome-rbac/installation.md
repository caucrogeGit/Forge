# Installation — Progression « Bonjour Forge RBAC »

Ce préambule installe le module **opt-in** `forge-mvc-rbac` et génère le projet de
départ. C'est la **seule page du parcours** qui contient des commandes de création :
tous les paliers suivants supposent le projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir [Installer Forge](../../install/poste-linux.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- Aucune base de données pour la majorité du parcours : RBAC est **déclaratif**
  (contrat `mvc/security/rbac.json`). Le palier de résolution par utilisateur utilise
  un `fetch_all` de démonstration ; une vraie application persiste rôles et
  permissions (`rbac`, `user_roles`).

## 1. Installer le module opt-in RBAC

`forge-mvc-rbac` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-rbac
```

## 2. Générer le projet de départ

Le starter `rbac-welcome` livre un contrat `mvc/security/rbac.json` de démonstration :

```bash
forge starter:build rbac-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/rbac-welcome` : la page affiche **« Bonjour Forge RBAC »**.
`/rbac-welcome/inspect` montre le contrat chargé (rôles, permissions, entités).

## 4. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance RBAC et le contrat.

## Après l'installation

[Continuer avec Bonjour Forge RBAC](debutant/rbac-welcome.md)
