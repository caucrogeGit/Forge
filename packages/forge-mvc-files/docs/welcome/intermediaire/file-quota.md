# Intermédiaire 4 : Les quotas

Objectif : qu'un utilisateur ne remplisse pas le disque à lui seul.

## Deux limites, deux natures de propriétaire

```bash
FILES_QUOTA_USER_BYTES=104857600     # 100 Mio par utilisateur
FILES_QUOTA_USER_FILES=200           # 200 fichiers par utilisateur
FILES_QUOTA_BYTES=1073741824         # défaut commun, toutes natures
```

Le réglage propre à une nature l'emporte sur le commun.
Sans aucun des deux, il n'y a **pas** de quota : Forge ne décide pas d'une limite à votre place.

```python
from forge_mvc_files import quota_for, owner_file_count

quota = quota_for("user")
```

!!! warning "Le quota se mesure sur le registre, pas sur le disque"
    Un fichier écrit sans être inscrit au registre ne compte pas.

    C'est pourquoi tout ce que Forge écrit s'inscrit : un fichier qui échappe au registre échappe aussi au quota, et à la purge d'orphelins.

!!! danger "Le quota est contrôlé avant l'écriture, jamais après"
    Vérifier après coup demanderait d'effacer, et une écriture partielle laisserait un fichier orphelin sur le disque.

!!! info "Un dépassement est une erreur métier, pas une panne"
    `FilesQuotaError` porte de quoi le dire à l'utilisateur : ce qu'il occupe, et ce qu'il a droit d'occuper.

    Un message « erreur interne » sur un quota dépassé fait ouvrir un ticket pour rien.

## À retenir

- Deux niveaux de réglage, du propre au commun, et rien par défaut.
- Le compte se fait sur le registre, donc tout écrit doit s'y inscrire.
- Le dépassement se dit à l'utilisateur, il ne se journalise pas seulement.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
