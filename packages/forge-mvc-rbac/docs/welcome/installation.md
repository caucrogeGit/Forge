# Installation : Progression « Welcome RBAC »

Ce préambule installe le module **opt-in** `forge-mvc-rbac` dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- Aucune base de données pour la majorité du parcours : RBAC est **déclaratif** (contrat `mvc/security/rbac.json`).
  Le palier de résolution par utilisateur utilise un `fetch_all` de démonstration ; une vraie application persiste rôles et permissions (`rbac`, `user_roles`).

## 1. Installer le module opt-in RBAC

`forge-mvc-rbac` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-rbac
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-rbac
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours, dont le contrat `mvc/security/rbac.json` de démonstration, se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance RBAC et le contrat.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrat, le contrôleur, la vue et la route `/rbac-welcome`.

[Continuer sur le starter Welcome RBAC](debutant/rbac-welcome.md)
