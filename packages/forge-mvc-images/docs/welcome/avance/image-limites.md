# Avancé 4 : Les limites de dimensions

Objectif : qu'une image de 30 000 pixels de côté ne mette pas le serveur à genoux.

## Le poids ne suffit pas

Un JPEG de 200 Kio peut porter 25 000 × 25 000 pixels.
Décompressé, il demande plusieurs gigaoctets de mémoire : la limite de taille du fichier ne l'arrête pas, c'est la **décompression** qui coûte.

```python
from forge_mvc_images import check_dimensions, check_weight, ImageLimitsError
```

Les deux contrôles sont distincts, et tous deux nécessaires.

| Contrôle | Ce qu'il arrête |
|---|---|
| `check_weight` | un fichier trop lourd, avant même de le lire |
| `check_dimensions` | une image dont la surface décompressée est déraisonnable |

!!! danger "Le contrôle des dimensions vient avant le décodage complet"
    Lire l'en-tête suffit à connaître la taille.

    Décoder d'abord et vérifier ensuite, c'est avoir déjà payé le coût que le contrôle devait éviter.

!!! warning "Une limite trop basse refuse des photos ordinaires"
    Un appareil récent produit couramment 6000 × 4000.

    Une limite calée sur l'écran plutôt que sur la mémoire ferait refuser des dépôts légitimes, et la garde finirait désactivée.

!!! info "Le refus se dit à l'utilisateur"
    `ImageLimitsError` porte la dimension trouvée et la limite.

    « Votre image fait 12000 pixels de large, le maximum est 8000 » se corrige ; « erreur interne » se signale au support.

## À retenir

- Poids et dimensions sont deux limites différentes, et la seconde protège la mémoire.
- Le contrôle lit l'en-tête, il ne décode pas l'image entière.
- Le message doit permettre à l'utilisateur de corriger seul.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
