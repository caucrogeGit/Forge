# Les champs de formulaire dans Forge

Ce document décrit les types de champ déclarables sur un formulaire.

Le fichier de code correspondant est `core/forms/fields.py`.

## 1. À quoi sert ce module ?

Chaque champ d'un formulaire lit sa valeur brute, la **convertit** vers le bon type Python et la **valide**.
Ce module fournit la classe de base `Field` et les champs typés prêts à l'emploi.

## 2. Les champs disponibles

| Champ | Type / rôle |
|---|---|
| `StringField` | chaîne (avec longueurs) |
| `TextAreaField` | texte long |
| `IntegerField`, `DecimalField` | nombres |
| `BooleanField` | booléen (case à cocher) |
| `EmailField`, `UrlField`, `PhoneField` | chaînes au format vérifié |
| `DateField`, `DateTimeField` | dates |
| `SlugField` | slug d'URL |
| `ChoiceField` | choix dans une liste explicite |
| `RelationField` | clé étrangère `many_to_one` validée par liste blanche |
| `RelatedIdsField` | liste d'identifiants liés (pivots) |
| `FileField`, `ImageField` | fichiers téléversés |

## 3. Le contrat commun

Tout champ dérive de `Field` : il lit la valeur, la convertit, applique ses contraintes (`required`, longueurs, plages…) et lève `ValidationError` en cas de refus.
`RelationField` valide l'identifiant cible par **liste blanche** (pas d'interpolation).

## 4. Contextes d'utilisation

- **Déclaration de formulaire** : assembler des champs sur une classe `Form`.

## 5. Voir aussi

- [Les formulaires](form.md) : `Form` qui assemble les champs.
- [L'erreur de validation](exceptions.md).
