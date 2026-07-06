# Générer les fichiers

Objectif : lancer `forge deploy:init` et comprendre les fichiers générés.

**Ce que vous allez apprendre :** `forge deploy:init` produit les fichiers de déploiement à la racine du projet, en mode write-if-new.
Chaque fichier est un modèle à adapter, jamais écrasé s'il existe déjà.

Deuxième palier du **niveau débutant** de la progression Deploy.

## Ce que ce starter montre

- générer les fichiers de déploiement avec `forge deploy:init` ;
- repérer où chaque fichier est créé ;
- comprendre l'écriture write-if-new.

## Commandes Forge utilisées

| Commande | Rôle dans ce starter |
|----------|----------------------|
| `forge deploy:init` | Génère les fichiers de déploiement (write-if-new). |

## 1. Lancer la génération

Depuis la racine du projet :

```bash
forge deploy:init
```

### Comprendre ce code

- La commande s'exécute depuis la racine du projet Forge.
- Elle crée les fichiers manquants et laisse intacts ceux qui existent déjà.
- Rien n'est écrit dans votre code applicatif : seuls des fichiers de déploiement apparaissent.

## 2. Les fichiers générés

| Fichier | Rôle |
|---------|------|
| `wsgi.py` | Point d'entrée WSGI, à la racine, lancé par Gunicorn. |
| `deploy/nginx/forge-app.conf` | Config Nginx en reverse proxy devant Forge. |
| `deploy/systemd/forge-app.service` | Unité systemd lançant Gunicorn. |
| `deploy/README_DEPLOY.md` | Marche à suivre pour la mise en production. |

### Comprendre ce code

- `wsgi.py` est le point d'entrée que Gunicorn importe pour servir l'application.
- La config Nginx termine HTTPS côté public et relaie vers Forge en HTTP local.
- La taille `client_max_body_size` de Nginx est calibrée sur `UPLOAD_MAX_SIZE` lu dans `config.py`.

## 3. Le mode write-if-new

```bash
forge deploy:init   # première fois : crée les fichiers
forge deploy:init   # deuxième fois : ne touche pas aux fichiers existants
```

### Comprendre ce code

- Un fichier déjà présent n'est jamais écrasé (principe 9, pas d'écriture invisible).
- Vous pouvez personnaliser un gabarit puis relancer `deploy:init` sans risque.
- Pour repartir d'un modèle neuf, supprimez le fichier à la main avant de relancer.

## À retenir

- `forge deploy:init` génère `wsgi.py` et le dossier `deploy/` à la racine du projet.
- Les fichiers générés sont des modèles à adapter, jamais écrasés s'ils existent.
- `client_max_body_size` est calibré sur `UPLOAD_MAX_SIZE` du projet.

## Après ce starter

Vous avez généré les fichiers de déploiement.
Faisons le point sur ce niveau débutant.

[Bilan](bilan.md)
