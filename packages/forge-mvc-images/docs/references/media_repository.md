# Le dépôt de médias dans Forge

Ce document décrit les opérations en base de données sur les médias rattachés à une entité.

Le fichier de code correspondant est `forge_mvc_images/media_repository.py`.

## 1. À quoi sert ce module ?

Une image stockée sur le disque ne sert à rien si on ne sait pas à quoi elle appartient.
Le **dépôt de médias** enregistre, liste et met à jour les associations entre un fichier et une entité (un article, un produit…) en base.

Le SQL reste **visible** (principe charte « garder SQL visible ») ; ce module n'est pas un ORM.

## 2. Rattacher un média

| Fonction | Rôle |
|---|---|
| `attach_media_to_entity(saved_upload, *, entity_name, entity_id, role="default", position=None, alt_text=None)` | crée l'enregistrement à partir d'un upload sauvegardé ; retourne l'id du média |
| `create_media_record(*, entity_name, entity_id, path, …)` | crée un enregistrement à partir de champs bruts ; retourne l'id |

`role` distingue les usages (`cover`, `gallery`, `default`) ; `position` ordonne les médias d'une galerie.

## 3. Lire

| Fonction | Rôle |
|---|---|
| `get_media_record(media_id)` | l'enregistrement d'un média, ou `None` |
| `list_media_for_entity(entity_name, entity_id, *, role=None)` | les médias d'une entité, filtrés par rôle si fourni |

## 4. Mettre à jour

| Fonction | Rôle |
|---|---|
| `update_media_alt_text(media_id, alt_text)` | change le texte alternatif (accessibilité) |
| `update_media_position(media_id, position)` | change la position dans la galerie |

## 5. Supprimer

| Fonction | Rôle |
|---|---|
| `delete_media_record(media_id)` | supprime l'enregistrement en base ; retourne `True` s'il existait |
| `delete_media(media_id, *, delete_files=False, variants=True)` | supprime l'enregistrement **et**, si `delete_files=True`, le fichier et ses variantes |

`delete_media` est l'opération complète à appeler lors du `destroy` d'une entité : elle évite les fichiers orphelins.

## 6. Le paramètre `db`

Chaque fonction accepte un `db` optionnel (injection) ; à défaut, la connexion du noyau est utilisée.
Pratique pour les tests, qui passent une connexion simulée.

## 7. Contextes d'utilisation

- **Après upload** : `attach_media_to_entity(saved, entity_name=…, entity_id=…)`.
- **Page de détail** : `list_media_for_entity(...)` pour afficher les médias.
- **Suppression d'entité** : `delete_media(media_id, delete_files=True, variants=True)`.

## 8. Voir aussi

- [Le traitement d'image](processing.md) : produit les fichiers et variantes.
- [La galerie](media_gallery.md) : helpers de lecture pour l'affichage.
