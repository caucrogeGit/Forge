# Audit CRUD-RELATION-FIELD-AUDIT-001

## Résumé

Conclusion : **Cas A — CRUD-RELATION-FIELD-001 déjà couvert**.

Les champs relationnels CRUD de base sont déjà présents pour le périmètre V1 :

- `many_to_one` déclaré dans `relations.json` ;
- SQL FK généré dans `relations.sql` ;
- `RelationField` core pour les clés étrangères ;
- formulaire create/edit avec `<select>` pour les `many_to_one` ;
- choix cible chargés par le contrôleur et le modèle générés ;
- affichage list via `LEFT JOIN` et alias `<fk>_label` ;
- filtres relationnels `many_to_one` dans les listes ;
- `many_to_many` côté source avec `<select multiple>` ;
- extraction/déduplication des ids multiples ;
- insertion/synchronisation de la table pivot ;
- affichage list/show côté source.

Le ticket `CRUD-RELATION-FIELD-001` ne doit donc pas recréer une mécanique de champs relationnels. Les besoins restants relèvent plutôt d'incréments distincts : autocomplete/HTMX, côté inverse `many_to_many`, `label_field` explicite, ou UI des `pivot_fields`.

## État many_to_one

Les relations `many_to_one` sont déclarées dans `mvc/entities/relations.json` avec :

- `from_entity` ;
- `to_entity` ;
- `from_field` ;
- `to_field` ;
- `foreign_key_name` ;
- `on_delete` ;
- `on_update`.

`forge sync:relations` génère une contrainte FK explicite :

```sql
ALTER TABLE contact
    ADD CONSTRAINT fk_contact_ville
    FOREIGN KEY (VilleId)
    REFERENCES ville (Id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
```

`forge make:crud` exploite déjà ces relations :

- le formulaire Python généré utilise `RelationField(...)` ;
- la vue `form.html` rend un `<select name="<fk>">` ;
- le contrôleur fournit les options via `get_<target>_choices()` ;
- le modèle charge les choix avec `SELECT id, label FROM target ORDER BY label` ;
- le modèle de liste utilise un `LEFT JOIN` et alias stable `<fk>_label` ;
- le template index affiche le libellé cible ;
- les filtres relationnels sont rendus en `<select>` ;
- les filtres relationnels sont combinés avec `q`, filtres simples, tri et pagination.

Le champ de libellé cible suit la convention existante : nom préféré (`name`, `nom`, `title`, `titre`, `label`, `libelle`), puis premier champ texte, puis clé primaire.

## État many_to_many

Les relations `many_to_many` sont déclarées dans `relations.json` avec :

- `source` ;
- `target` ;
- `pivot_table` ;
- `source_key` ;
- `target_key` ;
- `pivot_fields` optionnel.

`forge sync:relations` génère déjà la table pivot SQL, avec :

- colonnes source/cible ;
- clé primaire composite ;
- index utiles ;
- FK `ON DELETE CASCADE` ;
- colonnes `pivot_fields` si déclarées.

`forge make:crud` exploite déjà les relations `many_to_many` côté source :

- formulaire create/edit avec `<select multiple name="{target}_ids">` ;
- chargement des choix cible ;
- chargement des ids existants en édition ;
- extraction des ids multiples depuis la requête ;
- conversion en entiers positifs ;
- déduplication stable ;
- insertion pivot à la création ;
- synchronisation simple à l'édition par `DELETE` puis `INSERT` ;
- affichage des libellés liés dans la liste ;
- affichage des libellés liés dans la fiche show ;
- état vide lisible (`—` en liste, `Aucun <EntitéCible>` en show).

Limites conservées :

- seul le côté source est traité ;
- pas de côté inverse target ;
- pas d'autocomplete ;
- pas d'HTMX ;
- pas de liens automatiques vers les fiches target ;
- pas de saisie/édition/affichage des `pivot_fields`.

## État core/forms

`core.forms.RelationField` existe.

Il hérite de `ChoiceField` et représente un champ `many_to_one` :

- il ne fait aucune requête SQL ;
- il valide la valeur contre une liste de choix ;
- il accepte des choix fournis directement ou via `choices_key` dans les options du formulaire ;
- il conserve des attributs sémantiques `target` et `target_label_field`.

`make:crud` l'utilise bien dans les formulaires Python générés pour les FK déclarées dans `relations.json`.

`core.forms.RelatedIdsField` existe aussi pour une liste d'identifiants liés, mais `make:crud` ne l'utilise pas pour les `many_to_many`. Le CRUD généré garde une extraction locale explicite (`_parse_many_ids`) afin de rester lisible et aligné avec les tickets `REL-M2M-003/004`. Ce n'est pas un manque bloquant pour le périmètre actuel.

## État des tests

Tests `core/forms` :

- `tests/test_forms_relation_field.py` couvre l'import, les attributs `target` / `target_label_field`, la validation des choix, les choix absents, les valeurs vides et l'intégration via `Form(..., choices_key=...)`.

Tests `make:crud` `many_to_one` :

- génération `RelationField` ;
- génération `<select>` ;
- passage des choix au formulaire ;
- chargement des options de filtre relationnel ;
- fonction modèle de choix ;
- syntaxe des fichiers générés ;
- fallback du label cible ;
- filtre relationnel en `<select>` ;
- `LEFT JOIN` ;
- alias stable ;
- colonnes qualifiées ;
- exclusion de la FK des champs recherchables ;
- affichage du label cible.

Tests filtres relationnels :

- lecture du paramètre GET ;
- parsing entier ;
- valeur vide ou invalide ignorée ;
- filtre FK qualifié ;
- combinaison avec filtre simple ;
- conservation dans pagination et tri ;
- select de filtre et option vide.

Tests `many_to_many` :

- détection côté source ;
- absence de génération côté target ;
- select multiple ;
- chargement des choix ;
- ids existants pour edit ;
- extraction/déduplication ;
- insertion pivot create ;
- synchronisation pivot edit ;
- plusieurs relations ;
- compatibilité `many_to_one` ;
- affichage list/show ;
- états vides ;
- absence de repository pivot ou logique Auth/RBAC.

## État de la documentation

`docs/relations.md` documente :

- `many_to_one` ;
- `many_to_many` ;
- SQL FK et pivot ;
- exploitation CRUD ;
- limites actuelles.

Une imprécision a été corrigée : le formulaire Python généré utilise `RelationField`, pas un simple `ChoiceField`.

`docs/reference.md` documente déjà :

- `RelationField` ;
- `forge make:crud` avec champs relationnels ;
- filtres relationnels ;
- `many_to_many` côté source ;
- limites sans autocomplete ni HTMX.

`docs/guide.md` reste volontairement court et ne promet pas plus que le code.

`docs/roadmap.md` doit maintenant marquer l'audit terminé, marquer `CRUD-RELATION-FIELD-001` comme couvert, et recommander le prochain incrément : `CRUD-HTMX-001` ou un audit HTMX si l'on veut éviter de recoder un mécanisme déjà partiel.

## Analyse

Les champs `many_to_one` sont-ils suffisants ?

Oui pour le CRUD HTML classique V1. Ils couvrent create/edit, list, filtres, validation côté formulaire et conservation avec `q`/filtres/tri/pagination.

Les champs `many_to_many` sont-ils suffisants ?

Oui pour le périmètre côté source V1. Ils couvrent create/edit, pivot sync, list/show et états vides. Ils ne couvrent pas le côté inverse, l'autocomplete ni les champs pivot enrichis dans l'UI, mais ces sujets relèvent d'autres tickets.

Manque-t-il un vrai `CRUD-RELATION-FIELD-001` ?

Non sous ce nom. Un ticket générique "champs relationnels propres" risquerait de dupliquer ce qui existe déjà.

Le prochain besoin est-il plutôt autocomplete/HTMX, pivot enrichi UI, côté inverse, ou rien ?

Le prochain besoin logique côté CRUD enrichi est l'amélioration progressive de l'expérience de liste/formulaire avec HTMX ou son audit préalable. Les autres sujets doivent rester séparés :

- côté inverse `many_to_many` ;
- `label_field` explicite dans `relations.json` ;
- UI des champs `pivot_fields` ;
- autocomplete/tags UI.

## Conclusion

### Cas A — CRUD-RELATION-FIELD-001 déjà couvert

Le ticket `CRUD-RELATION-FIELD-001` est inutile dans son intitulé actuel.

Le socle relationnel CRUD est déjà présent et testé. Les limites restantes sont des fonctionnalités plus spécifiques, qui doivent être traitées dans des tickets dédiés plutôt qu'en recréant une mécanique de champ relationnel.

## Recommandation

Marquer `CRUD-RELATION-FIELD-AUDIT-001` terminé.
Marquer `CRUD-RELATION-FIELD-001` couvert par l'existant.
Ne pas créer de nouveau champ relationnel générique.
Prochain ticket recommandé : `CRUD-HTMX-001` ou, par prudence, `CRUD-HTMX-AUDIT-001`.
