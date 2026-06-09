# Numéros de version brûlés sur PyPI

Ce document recense les numéros de version qui **ne peuvent plus jamais être
publiés** sur PyPI pour le paquet `forge-mvc`. Il sert de garde-fou : avant
tout bump de version et tout tag de release, vérifier que la version cible
n'est pas dans la liste ci-dessous.

## Pourquoi un numéro peut être « brûlé »

PyPI applique une règle stricte et irréversible : un numéro de version (et un
nom de fichier) qui a déjà été utilisé ne peut **jamais** être réutilisé, même
après suppression de la release. Une tentative de réupload échoue avec une
erreur du type « This filename has already been used ».

Yanker (remiser) une version ne libère pas le numéro non plus : la version
reste occupée par son ancien contenu. Que le numéro soit yanked ou supprimé,
il est indisponible pour un nouveau contenu.

## Liste des numéros interdits

| Version | Statut | Origine | Action requise |
|---|---|---|---|
| `1.0.1` | supprimée de PyPI (2026-06-09) | prototype Forge 1.x d'avant le renumérotage vers la trajectoire publique 1.0 | ne jamais bumper ni taguer |
| `1.1.0` | supprimée de PyPI (2026-06-09) | prototype Forge 1.x d'avant le renumérotage vers la trajectoire publique 1.0 | ne jamais bumper ni taguer |

Ces deux versions avaient été publiées le 2026-05-01, puis remisées (yanked),
puis supprimées définitivement le 2026-06-09 pour réparer la commande
`forge update` (voir section suivante).

## Conséquence pratique sur le versionnage

La trajectoire actuelle est `1.0.0bN` (bêta publique), puis un jour `1.0.0`
stable. **Après le `1.0.0` stable, les premiers correctifs et élargissements
ne pourront pas s'appeler `1.0.1` ni `1.1.0`.** Il faudra sauter ces numéros,
par exemple :

- au lieu de `1.0.1` : passer à `1.0.2` ;
- au lieu de `1.1.0` : passer à `1.1.1` (ou un autre incrément mineur libre).

## Contexte : pourquoi ces versions ont été supprimées

Tant que `1.0.1` et `1.1.0` (versions **finales**) existaient sur l'index,
même remisées, elles cassaient `forge update`. La commande lance
`pip install --upgrade forge-mvc` sans `--pre`. Or :

1. pip constate qu'il existe des versions finales sur l'index, donc il exclut
   toutes les pré-releases, dont la dernière bêta ;
2. puis il écarte `1.0.1` et `1.1.0` parce qu'elles sont yanked ;
3. il ne reste alors rien de plus récent que la version installée, et
   l'utilisateur reste bloqué sur son ancienne bêta.

Leur suppression complète rétablit le repli automatique de pip sur les
pré-releases : il n'y a plus aucune version finale sur l'index, donc
`forge update` sans `--pre` récupère de nouveau la dernière bêta.

## Vérification de l'état de l'index

Pour contrôler à tout moment qu'aucun numéro brûlé n'est réapparu sur PyPI :

```bash
curl -s -H "Cache-Control: no-cache" "https://pypi.org/pypi/forge-mvc/json" \
  | python3 -c "import sys,json; r=list(json.load(sys.stdin)['releases']); print('1.0.1 present ?', '1.0.1' in r); print('1.1.0 present ?', '1.1.0' in r)"
```

Les deux réponses doivent être `False`.
