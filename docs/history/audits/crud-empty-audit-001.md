# Audit CRUD-EMPTY-AUDIT-001

## Résumé

Conclusion : **Cas B — états vides partiels**.

Forge possède déjà un socle d'états vides CRUD :

- les listes générées par `make:crud` affichent un état vide générique quand la collection est vide ;
- cet état vide est couvert par TPL-005 ;
- la recherche `q`, les filtres, le tri et la pagination conservent leurs paramètres dans le contexte ;
- une page hors limite est bornée par `Pagination` vers une page cohérente ;
- les relations `many_to_many` sans lien affichent un état vide lisible dans list/show.

Le manque restant est précis : l'état vide de liste ne distingue pas encore une table réellement vide d'un résultat vide après recherche, filtre, ou recherche + filtre. `CRUD-EMPTY-001` reste donc utile, mais doit être reformulé comme un ticket d'états vides contextuels, pas comme une création du socle.

## État du code

`forge_cli/entities/make_crud.py` génère un état vide directement dans `index.html` :

```jinja
{% if contacts %}
    {# tableau #}
{% else %}
<div class="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">
    {{ trans('crud.empty') }}
</div>
{% endif %}
```

La liste vide générale est donc gérée.

La recherche et les filtres réutilisent le même état vide générique. Le contrôleur généré lit `q`, construit les filtres, calcule le total avec les mêmes conditions que la liste, puis transmet `pagination.q` et `pagination.filters` au template. Le formulaire conserve les valeurs actives.

La pagination utilise `core.mvc.view.pagination.Pagination`. Une page absente, non numérique, négative ou trop grande revient à une page valide. Si le résultat filtré est vide, le template affiche l'état vide générique.

Pour les relations `many_to_many` côté source :

- la liste affiche `—` quand aucune étiquette liée n'existe ;
- la fiche show affiche `Aucun <EntitéCible>` quand la relation est vide.

## État des composants

Il n'existe pas de composant Jinja dédié aux états vides dans `mvc/views/components/`.

Les composants présents sont :

- `alert.html` ;
- `badge.html` ;
- `button.html` ;
- `form_field.html` ;
- `pagination.html` ;
- `table.html`.

Les tests TPL confirment que `make:crud` utilise seulement `components/button.html`. Les états vides sont donc intégrés directement dans les templates générés, ce qui est cohérent avec la documentation front actuelle.

## État des tests

Les tests existants couvrent déjà le socle TPL-005 :

- `test_index_etat_vide_utilise_div_style` ;
- `test_index_etat_vide_contient_trans_crud_empty` ;
- `test_index_etat_vide_est_dans_else` ;
- `test_index_etat_vide_sans_p_tag` ;
- `test_show_sans_etat_vide` ;
- `test_form_sans_etat_vide` ;
- `test_index_etat_vide_sans_htmx` ;
- `test_index_etat_vide_sans_alpine`.

Les tests `many_to_many` couvrent aussi :

- affichage `—` dans la liste quand aucune étiquette liée n'existe ;
- affichage `Aucun Tag` dans la fiche show quand aucune relation n'existe.

Les tests recherche, filtres, tri et pagination couvrent la conservation de `q`, filtres, `sort`, `direction` et page, mais ne testent pas de message d'état vide différencié. C'est cohérent avec le code actuel : il n'existe pas encore de message différencié.

## État de la documentation

`docs/front.md` documente déjà TPL-005 : l'état vide est générique, utilise `crud.empty`, et n'est pas un composant dédié.

`docs/reference.md` documentait la recherche, les filtres, le tri et la pagination, mais pas explicitement l'état vide généré dans les listes CRUD. Cette page est mise en cohérence par ce ticket.

`docs/guide.md` mentionnait recherche, tri et pagination dans les listes générées. Une mention courte de l'état vide générique suffit.

`docs/roadmap.md` indiquait déjà `CRUD-PAGINATION-001` terminé et `CRUD-EMPTY-001` prochain. Elle doit maintenant insérer `CRUD-EMPTY-AUDIT-001` terminé et reformuler `CRUD-EMPTY-001` comme prochain ticket contextualisé.

## Analyse

La liste vide est-elle gérée ?

Oui. `index.html` généré contient un bloc `{% else %}` avec `trans('crud.empty')`.

La recherche sans résultat est-elle gérée ?

Oui fonctionnellement, par le même état vide générique. Non, elle n'est pas distinguée par un message spécifique.

Les filtres sans résultat sont-ils gérés ?

Oui fonctionnellement, par le même état vide générique. Non, ils ne produisent pas encore un message spécifique.

Les relations `many_to_many` vides sont-elles gérées ?

Oui. La liste affiche `—` et la fiche show affiche `Aucun <EntitéCible>`.

Les messages sont-ils lisibles ?

Oui pour le socle. Le message `Aucun élément à afficher.` est clair, mais trop général pour expliquer une recherche ou un filtre sans résultat.

Manque-t-il un vrai `CRUD-EMPTY-001` ?

Oui, mais sous une forme réduite : il doit traiter les états vides contextuels, sans recréer le socle TPL-005.

## Conclusion

### Cas B — États vides partiels

`CRUD-EMPTY-001` ne doit pas être lancé comme un ticket de création des états vides CRUD : le socle existe déjà depuis TPL-005.

Il doit être reformulé pour couvrir uniquement :

- message spécifique quand `q` ne retourne aucun résultat ;
- message spécifique quand des filtres ne retournent aucun résultat ;
- message spécifique quand `q` + filtres ne retournent aucun résultat ;
- conservation des contrôles actifs dans ces états ;
- absence de HTMX, JavaScript ou composant lourd.

## Recommandation

Marquer `CRUD-EMPTY-AUDIT-001` terminé.
Conserver `CRUD-EMPTY-001` comme prochain ticket, mais reformulé sur les états vides contextuels.
Ne pas modifier la mécanique de recherche, filtres, tri, pagination ou `many_to_many` dans ce prochain ticket.
Ne pas ajouter HTMX ni JavaScript.
