# Intermédiaire 4 : Les préréglages de variantes

Objectif : décider une fois pour toutes des tailles produites, sans les écrire dans chaque contrôleur.

## Une déclaration, pas du code

```bash
IMAGE_PRESETS=vignette:200x200:crop,large:1200x1200:fit
```

Chaque entrée dit un nom, des dimensions, et un mode.

| Mode | Ce qu'il fait |
|---|---|
| `fit` | l'image entre dans la boîte, ses proportions sont gardées, elle peut être plus petite |
| `crop` | l'image remplit la boîte exactement, ce qui dépasse est coupé |

Sans déclaration, Forge produit `medium` en 1280 et `thumbnail` en 300, tous deux en `fit`.

!!! warning "Une déclaration mal formée est refusée au démarrage"
    `IMAGE_PRESETS=mauvais` lève, et le message dit la forme attendue.

    Retomber sur les préréglages par défaut serait pire : l'application produirait des tailles que personne n'a demandées, et le réglage passerait pour appliqué.

!!! danger "Une dimension nulle est refusée"
    `large:1200x0:fit` est une faute de frappe courante, pour dire « largeur imposée, hauteur libre ».

    Forge ne l'interprète pas ainsi et refuse : une hauteur nulle produirait une image vide, ou une division par zéro selon le chemin.

!!! info "Changer un préréglage ne régénère rien"
    Les variantes déjà écrites restent telles quelles.

    Régénérer un fonds d'images est une opération de votre application, pas un effet de bord d'un changement de configuration.

## À retenir

- Une variable d'environnement décrit les variantes, en une ligne.
- `fit` respecte les proportions, `crop` remplit et coupe.
- Une déclaration invalide refuse de démarrer plutôt que de se rabattre.

## Étape suivante

[Suivant : le recadrage focal](image-focal.md)
