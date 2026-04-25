# Contribuer à Forge

Merci de l'intérêt que vous portez à Forge.

## Comment contribuer

1. Forkez le dépôt
2. Créez une branche depuis `master` : `git checkout -b ma-contribution`
3. Committez vos changements avec un message clair
4. Ouvrez une Pull Request en décrivant ce que vous avez fait et pourquoi

## Cession de droits

En soumettant une contribution (Pull Request, patch, suggestion de code), vous
acceptez de céder l'intégralité des droits de propriété intellectuelle sur
cette contribution à Roger Cauchon, sans restriction et sans compensation.

Votre contribution sera intégrée sous la même licence propriétaire que le
reste du projet (voir [LICENSE](LICENSE)).

## Ce que nous acceptons

- Corrections de bugs
- Améliorations de performances
- Documentation

## Ce que nous n'acceptons pas

- Ajout de dépendances externes au runtime
- Changements qui cassent la compatibilité ascendante sans discussion préalable

## Checklist release

Avant de préparer une release ou de fusionner un changement de fond, exécuter :

```bash
python -m pytest tests/ -q
forge check:model
python -m mkdocs build --strict
python -m pip install -e . --no-deps
```

Pour le modèle d'entités, vérifier aussi que :

- les JSON invalides bloquent la génération ;
- les fichiers manuels existants ne sont pas écrasés ;
- les contraintes SQL hors V1 restent dans des scripts applicatifs séparés, jamais dans les fichiers générés sous `mvc/entities/`.

## Contact

Pour toute question avant de contribuer : caucroge@gmail.com
