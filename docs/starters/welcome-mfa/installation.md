# Installation — Progression « Bonjour Forge MFA »

Ce préambule installe le module **opt-in** `forge-mvc-mfa` et génère le projet de
départ. C'est la **seule page du parcours** qui contient des commandes de création :
tous les paliers suivants supposent le projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir [Installer Forge](../../install/index.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/index.md).
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

## 3. Générer le projet de départ

```bash
forge starter:build mfa-welcome
```

## 4. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/mfa-welcome` : la page affiche **« Bonjour Forge MFA »**.
`/mfa-welcome/inspect` indique facteurs, statuts et état de la clé.

## 5. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance MFA et la configuration de la clé.

## Après l'installation

[Continuer avec Bonjour Forge MFA](debutant/mfa-welcome.md)
