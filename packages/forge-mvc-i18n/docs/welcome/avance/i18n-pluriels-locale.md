# Avancé 4 : Pluriels et détection de la locale

Objectif : écrire « 1 article » et « 3 articles », et servir la bonne langue.

## Les pluriels

Une clé pluralisée porte ses formes dans le catalogue.

```json
{"articles": {"one": "{n} article", "other": "{n} articles"}}
```

```python
from forge_mvc_i18n import trans

trans("articles", "fr", count=compte).format(n=compte)
```

| Langue | 0 | 1 | 2 |
|---|---|---|---|
| français | singulier | singulier | pluriel |
| anglais | pluriel | singulier | pluriel |

!!! danger "Forge implémente deux formes, CLDR en définit six"
    C'est exact pour le français, l'anglais et la plupart des langues d'Europe occidentale.

    C'est **faux** pour le russe, l'arabe, le polonais et le gallois : `plural_form` lève pour ces langues plutôt que de rendre une forme qu'elle sait fausse. Une implémentation partielle donnerait l'impression de couvrir une langue qu'elle massacre.

!!! warning "Une forme absente est refusée au chargement"
    Pas à la requête qui porte le nombre manquant.

    Sans cela, la page marche pour un article et casse pour deux, et le défaut se découvre en production.

!!! info "Le texte n'est pas formaté pour vous"
    `trans` choisit la forme ; le `.format(n=compte)` est à vous.

    Le module n'a jamais substitué, et le faire casserait toute traduction contenant une accolade littérale.

## La détection de la locale

```python
from forge_mvc_i18n import detect_locale

langue = detect_locale(
    session_locale=session.get("locale"),
    accept_language=request.header("Accept-Language"),
    available=["fr", "en"],
    default="fr",
)
```

L'ordre va du plus intentionnel au plus supposé : la session, puis l'en-tête du navigateur, puis le défaut.

!!! danger "Sans `available`, les sources venues du client sont refusées"
    La locale devient un nom de fichier de catalogue.

    Un `Accept-Language: ../../etc/passwd` non borné serait une traversée de chemin : mieux vaut rendre le défaut que charger un catalogue qu'on n'a pas choisi de servir.

!!! info "Les clés manquantes se voient hors production"
    Une clé absente est affichée telle quelle, ce qui est le bon comportement : une page ne doit pas casser pour une traduction manquante.

    `missing_keys()` les liste, en développement seulement : en production, ce relevé ne s'accumule pas.

## À retenir

- Deux formes de pluriel, et un refus net pour les langues qui en demandent plus.
- Le choix de forme est à `trans` ; la substitution du nombre est à vous.
- La détection est fail-closed : sans liste de langues servies, le client ne décide rien.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
