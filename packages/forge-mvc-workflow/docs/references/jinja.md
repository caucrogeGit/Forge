# Les helpers Jinja dans Forge Workflow

Ce document décrit les helpers d'affichage qui rendent un statut dans un gabarit Jinja2.

Le fichier de code correspondant est `forge_mvc_workflow/jinja.py`.

## 1. À quoi sert ce module ?

Afficher un statut dans une page revient souvent à répéter le même HTML (un badge coloré).
Ces helpers produisent ce rendu sans accéder à la base ni déclencher de transition : ils ne font que **présenter** un statut.

## 2. L'injection automatique

Les helpers sont injectés **automatiquement** dans tout `Jinja2Renderer` via `make_workflow_jinja_helpers()`.
Aucune configuration supplémentaire n'est requise dans les gabarits.

## 3. Usage dans un gabarit

```jinja
{# Libellé seul #}
{{ workflow_status_label(demande.statut) }}

{# Classes CSS pour un <span> personnalisé #}
<span class="{{ workflow_status_badge_class(demande.statut) }}">
  {{ workflow_status_label(demande.statut) }}
</span>

{# Badge HTML complet, auto-échappé #}
{{ workflow_status_badge(demande.statut) }}
```

## 4. Les fonctions

| Fonction | Comportement |
|---|---|
| `workflow_status_label(status)` | `status.label`, ou `status.name` si vide ; `""` pour `None` |
| `workflow_status_color(status)` | `status.color`, ou `"gray"` si absent ou non listé |
| `workflow_status_badge_class(status)` | les classes Tailwind complètes du badge |
| `workflow_status_badge(status)` | un `Markup` HTML `<span>` prêt à l'emploi, auto-échappé |
| `make_workflow_jinja_helpers()` | le dict des quatre helpers (injection manuelle possible) |

## 5. Les couleurs prises en charge

| `color` | Palette Tailwind |
|---|---|
| `gray` (défaut) | `bg-gray-100 text-gray-700` |
| `blue` | `bg-blue-100 text-blue-700` |
| `green` | `bg-green-100 text-green-700` |
| `yellow` | `bg-yellow-100 text-yellow-700` |
| `red` | `bg-red-100 text-red-700` |
| `purple` | `bg-purple-100 text-purple-700` |

Une couleur absente ou non listée retombe sur la palette `gray`.
Les classes de base communes sont `inline-flex items-center rounded-full px-2 py-1 text-xs font-medium`.

## 6. Contextes d'utilisation

- **Liste admin** : `workflow_status_badge(...)` pour un badge prêt à l'emploi.
- **Mise en forme sur mesure** : `workflow_status_badge_class(...)` sur votre propre balise.
- **Texte simple** : `workflow_status_label(...)`.

## 7. Voir aussi

- [Les statuts](status.md) : l'objet rendu par ces helpers.
- [Les transitions](transitions.md) : la logique d'évolution du statut.
