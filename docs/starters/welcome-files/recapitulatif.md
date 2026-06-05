# Aide-mémoire de la progression Files

Récapitulatif des paliers de la progression *Bonjour Forge Files* et des API du
module opt-in `forge-mvc-files` introduites à chaque étape.

!!! note "Module opt-in et fondation"
    `forge-mvc-files` est l'upload générique extrait du core (ADR-019), **sans
    état**. Il dépend de rien d'autre que le core, et n'est pas encore publié sur
    PyPI : on l'installe depuis les sources (palier « Installation »). C'est la
    fondation sur laquelle `forge-mvc-images` est bâti ; les futurs opt-ins média
    composeront ses primitives (ADR-020).

## Niveau débutant — inspecter, stocker, servir

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge Files](debutant/files-welcome.md) | Inspecter racine et politique d'upload | `upload_root` |
| 2 | [Stocker un document](debutant/file-store.md) | Valider puis écrire (façade document) | `save_upload`, `SavedUpload` |
| 3 | [Servir un fichier](debutant/file-serve.md) | Relire un fichier, anti-traversal + 404 | `serve_media_file` |

## Niveau intermédiaire — valider, limiter, supprimer

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Valider un upload](intermediaire/file-validate.md) | Nommer la règle qui rejette | hiérarchie `UploadError` |
| 2 | [Limiter les uploads](intermediaire/file-rate-limit.md) | Rate-limit par IP | `is_upload_rate_limited`, `record_upload_attempt` |
| 3 | [Supprimer un fichier](intermediaire/file-delete.md) | Supprimer par chemin, idempotent | `delete_media_file` |

## Niveau avancé — primitives de stockage sécurisé

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Assainir un nom de fichier](avance/file-safe-name.md) | Réduire un nom à un nom sûr | `secure_filename` |
| 2 | [Chemin anti-traversal](avance/file-safe-path.md) | Juger/normaliser un chemin | `is_safe_media_path`, `normalize_media_path` |
| 3 | [Écrire des octets générés](avance/file-bytes.md) | Écrire un contenu côté serveur | `save_bytes` |
