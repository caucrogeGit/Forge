# Récapitulatif des composants

Aide-mémoire de tous les composants livrés dans `mvc/views/components/`.
Chaque composant est une **macro Jinja** : importez-la, puis appelez-la.

```jinja
{% from "components/ui.html" import button, card %}
{% from "components/forms.html" import field, submit %}
{% from "components/data.html" import table, pagination %}
{% from "components/interactive.html" import modal, modal_trigger %}
```

Les composants marqués **`{% call %}`** enveloppent un contenu :
`{% call card() %} ... {% endcall %}`.

## `components/ui.html`

| Macro | Signature | Rôle |
|---|---|---|
| `button` | `button(label, variant="primary", href=None, type="button", extra="")` | bouton ou lien (`href`) ; variantes `primary`, `secondary`, `ghost` |
| `card` | `card(extra="")` **`{% call %}`** | carte de contenu |
| `badge` | `badge(label, tone="teal")` | pastille ; tons `teal`/`success`, `warning`, `danger`, `neutral` |
| `alert` | `alert(message, level="info")` | message ; niveaux `success`, `error`, `warning`, `info` |
| `flash_messages` | `flash_messages(flash)` | rend le message flash de session (dict ou None) |
| `page_header` | `page_header(title, subtitle="", action_label="", action_href="")` | titre de page + bouton d'action |
| `empty_state` | `empty_state(message, hint="")` | bloc « aucune donnée » |
| `stat` | `stat(value, label)` | chiffre-clé |
| `breadcrumb` | `breadcrumb(items)` | fil d'Ariane ; `items` = liste de `(libellé, href)`, dernier sans href = courant |
| `navbar` | `navbar(links, current="")` | liens de navigation ; `links` = liste de `(libellé, href)` |

## `components/forms.html`

| Macro | Signature | Rôle |
|---|---|---|
| `field` | `field(name, label="", type="text", value="", placeholder="", required=False, help="", error="")` | champ texte (et `type` : email, password, number...) |
| `textarea_field` | `textarea_field(name, label="", value="", rows=4, placeholder="", required=False, help="", error="")` | zone de texte |
| `select_field` | `select_field(name, label="", options=[], selected="", required=False, error="")` | liste déroulante ; `options` = couples `(valeur, libellé)` |
| `radio_group` | `radio_group(name, label="", options=[], selected="", error="")` | choix exclusif |
| `checkbox` | `checkbox(name, label, checked=False, value="1")` | case à cocher |
| `file_field` | `file_field(name, label="", required=False, help="", error="", accept="")` | envoi de fichier |
| `search_field` | `search_field(name="q", placeholder="Rechercher...", value="")` | champ de recherche |
| `fieldset` | `fieldset(legend="")` **`{% call %}`** | regroupe des champs sous un titre |
| `form_errors` | `form_errors(errors)` | résumé des erreurs (liste de messages) |
| `submit` | `submit(label="Envoyer")` | bouton d'envoi pleine largeur |

!!! note "Validation"
    Passez `error="message"` à `field`, `textarea_field` ou `select_field` pour
    la bordure rouge et le message. La balise `<form>` et le jeton CSRF
    (`{% include "partials/csrf.html" %}`) restent à votre charge.

## `components/data.html`

| Macro | Signature | Rôle |
|---|---|---|
| `table` | `table(headers, rows, empty="Aucune donnée à afficher.")` | tableau en lecture ; `rows` = liste de listes de cellules (texte) |
| `pagination` | `pagination(page, total_pages, base_url="")` | liens `?page=N` ; rien si une seule page |

## `components/interactive.html`

HTML natif, sans framework JavaScript.

| Macro | Signature | Rôle |
|---|---|---|
| `accordion` | `accordion(summary, open=False)` **`{% call %}`** | section repliable (`<details>`) |
| `dropdown` | `dropdown(label)` **`{% call %}`** | menu déroulant (`<details>`) |
| `menu_item` | `menu_item(label, href="#")` | lien de menu, pour `dropdown` |
| `modal_trigger` | `modal_trigger(id, label, variant="primary")` | bouton qui ouvre la modale `id` |
| `modal` | `modal(id, title="")` **`{% call %}`** | fenêtre modale (`<dialog>`) |

## Personnaliser

La charte (couleurs, police, rayons) vit dans `static/src/input.css` (bloc
`@theme`). Ces macros sont **votre code** : étendez-les ou ajoutez les vôtres
dans `mvc/views/components/`, en réutilisant les tokens de la charte.

Voir le parcours pas à pas : [Préambule du système de design](installation.md).
