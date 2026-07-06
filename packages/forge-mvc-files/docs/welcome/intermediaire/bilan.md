# Bilan : niveau intermédiaire (Files)

Récapitulatif du **niveau intermédiaire** de la progression *Welcome Files*.
Ce niveau couvre la **robustesse** : valider finement, limiter les abus, supprimer proprement.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Valider un upload](file-validate.md) | Nommer la règle qui rejette (extension/MIME/taille) via la hiérarchie `UploadError`. |
| 2 : [Limiter les uploads](file-rate-limit.md) | Protéger la route par rate-limit IP (`is_upload_rate_limited` / `record_upload_attempt`). |
| 3 : [Supprimer un fichier](file-delete.md) | Supprimer par chemin relatif (`delete_media_file`), anti-traversal et idempotent. |

Vous savez rendre une route d'upload robuste et tenir le cycle de vie complet d'un fichier.

## Et ensuite

Place au niveau **avancé** : les **primitives** anti-traversal sous le capot, la boîte à outils que les opt-ins média composent (ADR-020).

[Niveau avancé : Assainir un nom de fichier](../avance/file-safe-name.md)
