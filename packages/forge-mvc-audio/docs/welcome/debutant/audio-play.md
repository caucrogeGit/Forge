# Lire un audio

Objectif : brancher la route de **lecture officielle** de Forge Audio — streaming
HTTP Range — sans écrire de code métier.

**Ce que vous allez apprendre :** `register_audio_routes(router)` enregistre la
route `GET /audio/{uuid}` qui sert un fichier audio en **streaming** (support des
requêtes HTTP Range, donc le *seek* dans un lecteur). Le code vit dans le paquet ;
on ne fait que le **brancher**.

Troisième palier du **niveau débutant** de la progression audio.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-audio` installé (palier « Installation »).

## Ce que ce starter montre

- le branchement de la route officielle avec `register_audio_routes(router)` ;
- `GET /audio/{uuid}` en streaming HTTP Range ;
- aucun contrôleur applicatif : la lecture appartient au module.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.register_audio_routes` | Brancher la route de lecture (`GET /audio/{uuid}`). | Audio |

## Tester

```bash
forge run
```

Téléversez un audio au palier précédent, notez son `uuid`, puis ouvrez
`https://localhost:8000/audio/<uuid>` : le fichier est servi en streaming.

## La route

Ce palier ne crée **aucun contrôleur** : le code de lecture vit dans le paquet
`forge-mvc-audio` ; on ne fait que le brancher.
Ajoutez ces lignes dans `mvc/routes.py` (au niveau du module, pas dans un groupe :
`register_audio_routes` déclare ses propres routes) :

```python
# mvc/routes.py
# Branche la route de lecture officielle de Forge Audio (streaming HTTP Range) :
#   GET /audio/{uuid}
# Le code métier vit dans le paquet forge-mvc-audio ; on ne fait que le brancher.
from forge_mvc_audio import register_audio_routes

register_audio_routes(router)
```

### Comprendre ce code

- On ne réimplémente **pas** la lecture : `register_audio_routes` apporte une route
  testée (Range, types MIME, anti-traversal par uuid). C'est la convention Forge
  « le module fournit, l'application branche ».
- Si un `api_token` est configuré, la route exige un `Authorization: Bearer …` —
  rien à coder côté application.

## À retenir

- La lecture audio est **fournie** par le module, **branchée** explicitement.
- `GET /audio/{uuid}` sert en **streaming HTTP Range** (seek possible).
- Brancher une route officielle > réécrire un service de fichiers.

## Après ce starter

Vous savez stocker et lire. La suite (niveau avancé) : sonder et transcoder.

[Bilan du niveau débutant](bilan.md)
