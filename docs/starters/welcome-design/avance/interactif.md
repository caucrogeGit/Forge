# Les composants interactifs

**Objectif** : ajouter un accordéon, un menu déroulant et une modale de
confirmation, sans aucun framework JavaScript.

**Ce que vous allez apprendre :** `components/interactive.html` s'appuie sur les
éléments natifs `<details>` (accordéon, menu) et `<dialog>` (modale). Fidèle à
la charte : pas de magie, pas de dépendance JS imposée.

## Accordéon (zéro JS)

```jinja
{% from "components/interactive.html" import accordion %}

{% call accordion("Coordonnées détaillées") %}
  Adresse, téléphone et notes du contact.
{% endcall %}
```

L'ouverture et la fermeture sont natives (`<details>`), sans une ligne de
JavaScript.

## Menu déroulant (zéro JS)

```jinja
{% from "components/interactive.html" import dropdown, menu_item %}

{% call dropdown("Actions") %}
  {{ menu_item("Modifier", "/showcase") }}
  {{ menu_item("Archiver", "/showcase") }}
{% endcall %}
```

## Modale de confirmation

La modale utilise l'élément natif `<dialog>` : un bouton l'ouvre via
`showModal()` (méthode native, pas un framework), et le formulaire
`method="dialog"` la ferme sans JavaScript.

```jinja
{% from "components/interactive.html" import modal, modal_trigger %}

{{ modal_trigger("confirm-suppr", "Supprimer", variant="ghost") }}

{% call modal("confirm-suppr", "Confirmer la suppression") %}
  <p>Cette action est définitive.</p>
  <div class="mt-4 flex justify-end gap-2">
    <form method="dialog"><button class="px-4 py-2 text-sm">Annuler</button></form>
    <form method="post" action="/showcase/delete">
      {% include "partials/csrf.html" %}
      <button class="px-4 py-2 text-sm font-semibold text-white bg-teal rounded-[10px]">Supprimer</button>
    </form>
  </div>
{% endcall %}
```

??? note "À retenir"
    - `accordion` et `dropdown` reposent sur `<details>` : zéro JavaScript.
    - `modal` repose sur `<dialog>` : ouverture via `showModal()` natif,
      fermeture via `<form method="dialog">`.
    - Les versions animées (htmx / alpine) relèveront d'un choix frontend
      séparé ; le squelette n'impose aucun framework.

[Voir le bilan du parcours](bilan.md)
