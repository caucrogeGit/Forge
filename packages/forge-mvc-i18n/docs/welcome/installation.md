# Installation : Progression « Welcome i18n »

Ce préambule installe le module **opt-in** `forge-mvc-i18n` dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et le code à écrire.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.
    Pour la décision d'architecture, voir ADR-027 : Extraction i18n.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- Aucune base de données : l'i18n lit des **catalogues JSON** sur disque, pas la base.

## 1. Installer le module opt-in i18n

`forge-mvc-i18n` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-i18n
```

!!! note "Repli no-op du noyau"
    Sans le module, le noyau fournit un `trans()` **no-op** qui retourne la clé telle quelle : une application sans i18n ne casse pas.
    Installer l'opt-in active la vraie traduction par catalogues.

## 2. Disposer d'un projet Forge

```bash
forge new mon-projet-i18n
```

Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance i18n.

## Après l'installation

Vous pouvez attaquer le premier palier, où vous traduirez votre première chaîne.

[Continuer sur le starter Welcome i18n](debutant/i18n-welcome.md)
