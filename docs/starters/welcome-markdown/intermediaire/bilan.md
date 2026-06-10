# Bilan : niveau intermédiaire

Votre page « Prise en main de Forge » est devenue **riche** : tableau des commandes, glossaire, encadrés de mise en garde, dépannage repliable et bloc d'installation.

## Les notions acquises

- Palier 1 : tableaux et alignement des colonnes.
- Palier 2 : listes de définition.
- Palier 3 : admonitions (`!!!`), types et titres.
- Palier 4 : blocs dépliables (`???`, `???+`).
- Palier 5 : blocs de code colorés (langage, `linenums`, `hl_lines`, `title`).

## État de votre page

Voici un assemblage possible de `prise-en-main.md` à ce stade :

````md
# Prise en main de Forge

Forge est un framework web Python explicite, pédagogique et testable.

## Présentation

Forge est **explicite** : le `SQL` reste visible, sans _magie cachée_.

## Principes

- **Explicite** : le SQL reste visible.
- **Minimal** : un noyau réduit, des modules opt-in.
- **Testable** : on teste avant d'élargir.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install forge-mvc
forge new mon-projet
```

## Commandes

| Commande | Rôle |
|:---|:---|
| `forge new <nom>` | crée un nouveau projet |
| `forge serve` | lance le serveur de développement |
| `forge migration:apply` | applique les migrations en attente |

## Prérequis

!!! warning "Version de Python"
    Forge exige Python 3.12 ou plus récent.

## Glossaire

Module opt-in
:   Brique installable séparément, hors du noyau minimal.

## Dépannage

??? question "« commande forge introuvable »"
    Vérifiez que l'environnement virtuel est activé.
````

## Et ensuite

La page est complète et agréable à lire.

Le niveau avancé y ajoute la touche professionnelle : onglets, diagrammes, texte enrichi, notes de bas de page, annotations de relecture et formules.

[Niveau avancé : Offrir des variantes avec les onglets](../avance/onglets.md)
