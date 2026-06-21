# Installation : Progression « Bonjour Forge MFA »

Ce préambule installe le module **opt-in** `forge-mvc-mfa` dans un projet Forge
existant. La progression se réalise ensuite **à la main** : chaque palier décrit
les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  Installer Forge.
- **Python 3.12+**.
- Aucune base de données pour ce parcours : les flux (enrôlement, challenge,
  récupération) sont démontrés **en session**. Une vraie application persiste les
  facteurs (`auth_mfa_factors`) et codes (`auth_mfa_recovery_codes`).

## 1. Installer le module opt-in MFA

`forge-mvc-mfa` est **publié sur PyPI** (statut Alpha) :

```bash
pip install --pre forge-mvc-mfa
```

## 2. Configurer la clé de chiffrement

Les secrets TOTP sont **chiffrés au repos** (Fernet) via `FORGE_MFA_SECRET_KEY`.
Générez une clé :

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Puis renseignez-la dans la configuration Forge (fichier `env/dev`) :
`FORGE_MFA_SECRET_KEY=<clé générée>`. Sans elle, les paliers d'enrôlement et de
chiffrement restent pédagogiques (message explicite) mais ne chiffrent rien.

## 3. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-mfa
```

Le détail de la création d'un projet est décrit dans
Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au
fil des paliers.

## 4. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance MFA et la configuration de la clé.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le
contrôleur, la vue et la route `/mfa-welcome`.

[Continuer avec Bonjour Forge MFA](debutant/mfa-welcome.md)
