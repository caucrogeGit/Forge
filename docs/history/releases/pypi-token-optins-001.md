# Configuration PyPI - token opt-ins Forge

## 1. Résumé

Objectif : configurer un token PyPI compatible avec la publication des packages Forge opt-in.

Résultat : un nouveau token PyPI à portée "Tous les projets" a été créé et configuré localement dans ~/.pypirc.

Statut : terminé.

## 2. Cause

La publication de `forge-mvc-rbac==1.0.0b6` a été arrêtée proprement avec une erreur HTTP 403.

Cause : le token précédemment configuré était limité au projet `forge-mvc` et ne pouvait pas publier le projet `forge-mvc-rbac`.

## 3. Décision

Un nouveau token PyPI à portée "Tous les projets" a été créé pour permettre la publication initiale et future des packages Forge :

- `forge-mvc`
- `forge-mvc-rbac`
- `forge-mvc-workflow`
- `forge-mvc-stats`
- `forge-mvc-media`
- `forge-mvc-mfa`

## 4. Configuration locale

Le fichier local `~/.pypirc` a été mis à jour.

Configuration attendue :

```ini
[pypi]
username = __token__
password = pypi-***MASQUÉ***
```

Le token réel n'est pas affiché, pas documenté et pas commité.

## 5. Vérifications

Vérifications effectuées :

- `git status` : copie de travail propre ;
- `~/.pypirc` : présent ;
- section `[pypi]` : configurée avec `username = __token__` ;
- token masqué dans les affichages ;
- permissions `~/.pypirc` : `600` ;
- `twine` disponible ;
- `forge-mvc-rbac` non encore publié sur PyPI.

## 6. Sécurité

- Secret affiché : NON ;
- Secret commité : NON ;
- `.pypirc` dans le dépôt Git : NON ;
- anciens tokens parasites supprimés sur PyPI ;
- nouveau token conservé côté PyPI.

## 7. Publication

Aucune publication PyPI n'a été effectuée dans ce ticket.

État :

- `twine upload` exécuté : NON ;
- `forge-mvc-rbac` publié : NON ;
- autres opt-ins publiés : NON ;
- HTTP 429 rencontré : NON.

## 8. Prochain ticket

Prochain ticket recommandé :

`PYPI-OPTINS-001-RETRY` - reprendre la publication de `forge-mvc-rbac==1.0.0b6`.
