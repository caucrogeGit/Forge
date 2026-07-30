# Retirer une distribution absorbée de PyPI

Ce document décrit le geste à faire quand un paquet Forge est absorbé par un autre.
Il complète le garde de complétude, qui signale l'orphelin mais ne peut pas agir à la place d'un humain.

## Le problème

Un paquet absorbé quitte `packages/`, mais reste installable depuis PyPI.
`pip install forge-mvc-pivot` continue donc de réussir et de servir un code que le dépôt ne maintient plus.
Deux façons d'obtenir la même capacité coexistent, dont une morte, ce que le principe 11 refuse.

## Le geste : retirer, pas supprimer

Le retrait PyPI, dit **yank**, laisse la version servie à qui l'épingle déjà dans son `requirements.txt`.
Aucun projet existant ne casse.
En revanche la version sort de toute résolution nouvelle : un `pip install` sans épinglage ne la choisira plus.

Supprimer le projet PyPI ferait l'inverse, et casserait immédiatement tout projet qui l'épingle.
C'est pourquoi Forge ne supprime jamais, il retire.

## Les distributions concernées

| Distribution | Absorbée par | Décision |
|---|---|---|
| `forge-mvc-pivot` | `forge-mvc-entities` (ADR-070) | retirer toutes les versions |
| `forge-mvc-media` | `forge-mvc-images` (ADR-018) | retirer toutes les versions |

## Marche à suivre

Le retrait se fait depuis l'interface PyPI, projet par projet.

1. Ouvrir `https://pypi.org/manage/project/<nom>/releases/`.
2. Pour chaque version, choisir « Yank ».
3. Renseigner la raison, qui s'affichera à qui tente d'installer.
   Pour le pivot : `Absorbé par forge-mvc-entities (ADR-070) ; installez forge-mvc-entities.`
   Pour media : `Absorbé par forge-mvc-images (ADR-018) ; installez forge-mvc-images.`

Le retrait est réversible : une version retirée par erreur se rétablit depuis la même page.

## Vérifier

Le garde de complétude ne compte que les versions **installables**.

```bash
python tools/check_pypi_completeness.py
```

Tant qu'une version reste servie, la ligne `[WARN] ... ORPHELIN` s'affiche.
Une fois toutes les versions retirées, elle disparaît d'elle-même.

## Quand un paquet est absorbé

Trois gestes vont ensemble, et le troisième s'oublie facilement.

1. Retirer le dossier de `packages/`, et laisser un test d'absence à la place des tests du paquet.
2. Inscrire le nom dans `ABSORBED`, au sommet de `tools/check_pypi_completeness.py`, avec l'ADR qui décide.
3. Retirer les versions publiées, comme ci-dessus.

## Voir aussi

- [La politique de release](release-policy.md) : le cycle complet de publication.
