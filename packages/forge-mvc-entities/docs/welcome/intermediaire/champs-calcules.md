# Intermédiaire 3 : Les champs calculés

Objectif : un total, un âge, un nom complet, sans jamais les stocker.

## Le problème que cela retire

Une valeur dérivée d'autres colonnes ment dès qu'une source change.
Sans champ calculé, l'application duplique l'expression dans chaque requête, ou rapatrie tout pour recalculer en Python.

```json
{
  "name": "resume",
  "type": "string",
  "max_length": 200,
  "computed": "SUBSTR(Titre, 1, 40)"
}
```

## Ce que Forge en fait

| Endroit | Ce qui se passe |
|---|---|
| La table | **aucune colonne** n'est créée |
| Les lectures | l'expression est projetée : `(SUBSTR(Titre, 1, 40)) AS "Resume"` |
| Les écritures | le champ est absent de l'`INSERT` et de l'`UPDATE` |
| Le formulaire | le champ n'y figure pas |

Le champ se lit partout où les autres se lisent, et ne s'écrit nulle part.

!!! danger "L'expression part telle quelle dans le SQL"
    Elle n'est pas paramétrée, et elle ne peut pas l'être.

    Le contrat d'entité est du code du projet, relu et versionné, jamais une donnée d'utilisateur : n'y mettez rien qui vienne d'ailleurs.

!!! warning "Certaines combinaisons sont refusées, et c'est voulu"
    `required`, `unique`, `default`, `form`, `source` et `foreign_key` supposent une colonne stockée.

    Les accepter produirait du SQL faux plutôt qu'une simple maladresse : la validation les refuse en nommant le conflit.

!!! info "Écrivez l'expression avec les noms de colonnes"
    `SUBSTR(Titre, 1, 40)`, et non `SUBSTR(titre, 1, 40)`.

    L'expression est recopiée dans le `SELECT` sans traduction : ce sont les colonnes de la table qu'elle voit, pas les noms de champs du contrat.

## À retenir

- Un champ calculé n'a pas de colonne, et ne peut pas être saisi.
- L'expression est projetée à chaque lecture, jamais stockée.
- Elle emploie les noms de **colonnes**, et ne doit rien contenir qui vienne d'un utilisateur.

## Étape suivante

[Suivant : l'unicité composite](unicite-composite.md)
