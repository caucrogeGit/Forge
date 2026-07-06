# La charte graphique

**Objectif** : comprendre où sont définies les couleurs, la police et les rayons, et recolorer toute l'application en un seul endroit.

**Ce que vous allez apprendre :** la charte vit dans un bloc `@theme` (Tailwind v4) au sein de `static/src/input.css`.
Chaque token y devient un utilitaire Tailwind (`bg-teal`, `text-ink`, `rounded-card`...).

## La source unique

Ouvrez `static/src/input.css` :

```css
@import "tailwindcss";
@source "../../mvc/views";

@theme {
  --color-teal:        #0f7d6d;   /* couleur primaire */
  --color-teal-dark:   #0a5d51;
  --color-teal-soft:   #e7f1ee;
  --color-ocre:        #d98a2b;   /* accent */
  --color-ink:         #211f1a;   /* texte */
  --color-muted:       #5d574c;
  --color-cream:       #faf8f4;   /* fond */
  --color-surface:     #fffdf9;
  --color-line:        #ece6dc;

  --font-sans:   "Figtree", system-ui, sans-serif;
  --radius-card: 16px;
}
```

## Du token à l'utilitaire

Tailwind génère un utilitaire pour chaque token :

| Token | Utilitaires |
|---|---|
| `--color-teal` | `bg-teal`, `text-teal`, `border-teal` |
| `--color-ink` | `text-ink`, `bg-ink` |
| `--font-sans` | `font-sans` |
| `--radius-card` | `rounded-card` |

Les modificateurs d'opacité fonctionnent aussi : `bg-teal/15`, `text-ink/70`.

## Essayez : recolorez le projet

Avec `npm run watch:css` qui tourne, changez la primaire :

```css
@theme {
  --color-teal: #1d4ed8;   /* la primaire passe au bleu */
}
```

Sauvegardez, rafraîchissez `/showcase` : l'en-tête et tout ce qui utilise `teal` suivent, sans toucher un seul template.
Remettez la valeur d'origine ensuite.

??? note "À retenir"
    - Une seule source de vérité : le bloc `@theme` de `static/src/input.css`.
    - Chaque token devient un utilitaire Tailwind réutilisable partout.
    - Recolorer = éditer un token, pas chercher dans les templates.

Au palier suivant, nous habillons la page avec l'en-tête et la navigation.

[Continuer avec La mise en page](mise-en-page.md)
