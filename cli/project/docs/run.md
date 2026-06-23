# La commande run dans Forge

Ce document décrit la commande `forge run`.

Le fichier de code correspondant est `cli/project/run.py`.

## 1. À quoi sert cette commande ?

`forge run` est le point d'entrée officiel pour lancer Forge.
Son comportement dépend de l'environnement applicatif (`APP_ENV`).

En `dev` (défaut), elle lance un superviseur de développement avec autoreload qui relance `python app.py` à chaque changement de fichier.
L'option `--no-reload` désactive le rechargement automatique.
En `prod`, elle refuse de servir directement et indique la stratégie WSGI à employer (Gunicorn).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `cmd_run(args)` | exécute la commande selon `APP_ENV` |
| `main(args)` | point d'entrée de la commande `forge run` |

## 3. Contextes d'utilisation

- **Développement** : lancer l'application avec rechargement automatique.
- **Production** : obtenir la stratégie de lancement WSGI plutôt qu'un serveur de dev.

## 4. Voir aussi

- [Le superviseur de développement](dev_reloader.md) : mécanique de l'autoreload.
- [La commande doctor](doctor.md) : diagnostic du projet.
