# Avancé 5 : Les quotas vidéo

Objectif : qu'un utilisateur ne remplisse pas le disque, ni la file de transcodage.

## Deux limites, deux ressources

```python
from forge_mvc_video import check_size_quota, check_duration_quota, VideoQuotaError
```

| Contrôle | Ce qu'il protège |
|---|---|
| `check_size_quota` | l'espace disque, occupé par l'original **et** ses rendus |
| `check_duration_quota` | le temps de transcodage, qui est du calcul, pas du stockage |

!!! warning "La durée coûte plus cher que la taille"
    Un fichier de 100 Mio très compressé peut durer deux heures : le transcodage occupera un cœur pendant longtemps, et la file derrière lui attendra.

    Limiter la taille seule laisse donc passer ce qui coûte le plus.

!!! danger "Le quota compte les rendus, pas seulement l'original"
    Une vidéo transcodée occupe la place de l'original plus celle de chaque rendu.

    Compter le seul dépôt ferait dépasser le quota réel d'un facteur deux ou trois, et le disque se remplirait malgré le contrôle.

!!! info "Le refus se dit avant le dépôt, pas après le transcodage"
    Refuser après avoir transcodé, c'est avoir déjà payé le calcul que le quota devait éviter.

## À retenir

- Deux quotas, l'un pour le disque, l'autre pour le temps de calcul.
- Le compte inclut les rendus produits, pas seulement le fichier déposé.
- Le contrôle a lieu avant le travail, jamais après.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
