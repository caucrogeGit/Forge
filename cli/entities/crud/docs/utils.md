# Les helpers de champs CRUD dans Forge

Ce document décrit les helpers de champs purs du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/utils.py`.

## 1. À quoi sert ce module ?

Il regroupe des helpers purs sur les champs d'une entité, utilisés par les *builders* CRUD.
Il détermine par exemple la clé primaire, les champs non générés, le type d'`input` HTML, ou les champs de recherche et de libellé.

Conformément au principe 11, `_to_snake` est réexporté depuis le module de validation, qui en porte la définition canonique.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `_pk_field(definition)` | champ clé primaire de l'entité |
| `_non_pk_fields(definition)` | champs hors clé primaire |
| `_html_input_type(f)` / `_is_textarea(f)` | type d'`input` HTML d'un champ |
| `_text_search_fields(...)` / `_text_label_fields(definition)` | champs de recherche et de libellé |
| `_humanize(name)` | libellé lisible d'un nom de champ |

## 3. Contextes d'utilisation

- **Génération CRUD** : fournir aux *builders* des informations dérivées des champs.
- **Cohérence** : centraliser les helpers de champs pour éviter la duplication.

## 4. Voir aussi

- [Le builder de formulaire](form_builder.md) : consommateur du typage des champs.
- [Les builders de vues](views_builder.md) : consommateurs des helpers d'affichage.
