# Vérifier l'environnement

Objectif : lancer `forge deploy:check` et lire ses résultats.

**Ce que vous allez apprendre :** `forge deploy:check` contrôle l'environnement de production sans rien modifier.
Elle affiche des lignes taguées `[OK]`, `[WARN]` ou `[ERREUR]`, et sort en code 1 si une erreur bloquante existe.

Premier palier du **niveau intermédiaire** de la progression Deploy.

!!! note "Module opt-in"
    Si `forge-mvc-deploy` n'est pas installé, la commande `deploy:check` est absente.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- lancer une vérification en lecture seule avec `forge deploy:check` ;
- lire les tags `[OK]`, `[WARN]` et `[ERREUR]` ;
- corriger une variable manquante dans `env/prod`.

## Commandes Forge utilisées

| Commande | Rôle dans ce starter |
|----------|----------------------|
| `forge deploy:check` | Contrôle l'environnement de production, sans rien modifier. |

## 1. Lancer la vérification

```bash
forge deploy:check
```

### Comprendre ce code

- La commande ne modifie rien : elle lit l'environnement et rend un rapport.
- Chaque ligne porte un tag : `[OK]`, `[WARN]` ou `[ERREUR]`.
- La sortie vaut code 1 si au moins une erreur bloquante est détectée.

## 2. Ce qui est contrôlé

| Contrôle | Exemples |
|----------|----------|
| Interpréteur | Python 3.12 ou supérieur. |
| Environnement | présence de `.venv` et du dossier `env/`. |
| Fichier de prod | `env/prod` et ses variables `DB_APP_HOST`, `DB_NAME`, `DB_APP_LOGIN`, `UPLOAD_ROOT`. |
| Cohérence TLS | HTTP/HTTPS Nginx en accord avec `APP_SSL_ENABLED`. |
| Modules | `mariadb`, `jinja2`, `gunicorn` importables. |
| Fichiers | présence de `wsgi.py` et des fichiers `deploy/`. |

### Comprendre ce code

- Un module absent ou une variable manquante remonte en `[ERREUR]`.
- Une incohérence non bloquante remonte en `[WARN]`, à examiner sans urgence.
- Les fichiers `deploy/` doivent exister : c'est le rôle de `forge deploy:init`.

## 3. Corriger env/prod

```bash
forge deploy:check
# [ERREUR] env/prod : variable DB_NAME absente
```

### Comprendre ce code

- Une variable manquante dans `env/prod` produit une ligne `[ERREUR]`.
- Renseignez la variable signalée, puis relancez `forge deploy:check`.
- La commande ne corrige rien elle-même : elle diagnostique, vous corrigez.

## À retenir

- `forge deploy:check` vérifie l'environnement de production sans rien modifier.
- Les résultats sont tagués `[OK]`, `[WARN]` ou `[ERREUR]`.
- Une erreur bloquante fait sortir la commande en code 1.

## Après ce starter

Vous savez diagnostiquer l'environnement.
Voyons comment adapter les gabarits Nginx et systemd.

[Adapter les gabarits](deploy-templates.md)
