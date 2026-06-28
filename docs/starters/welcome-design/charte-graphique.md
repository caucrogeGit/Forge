# La charte graphique

**Objectif**{ .intro-label } : comprendre où sont définies les couleurs, la
police et les rayons du projet, et recolorer toute l'application en un seul
endroit.

**Ce que vous allez apprendre :**{ .intro-label } la charte vit dans un bloc
`@theme` (Tailwind v4) au sein de `static/src/input.css`.
Chaque token y devient un utilitaire Tailwind (`bg-teal`, `text-ink`,
`rounded-card`...), donc modifier le token reskinne toute l'application.

## La source unique

Ouvrez `static/src/input.css` :

```css
@import "tailwindcss";

@source "../../mvc/views";

@theme {
  /* Couleur primaire et ses variantes */
  --color-teal:        #0f7d6d;
  --color-teal-dark:   #0a5d51;
  --color-teal-soft:   #e7f1ee;
  --color-teal-border: #cfe5e0;

  /* Accent, texte, fonds, lignes */
  --color-ocre:        #d98a2b;
  --color-ink:         #211f1a;
  --color-muted:       #5d574c;
  --color-cream:       #faf8f4;
  --color-surface:     #fffdf9;
  --color-line:        #ece6dc;

  /* Typographie et rayons */
  --font-sans:   "Figtree", system-ui, sans-serif;
  --radius-card: 16px;
}
```

## Du token à l'utilitaire

Tailwind v4 génère un utilitaire pour chaque token du `@theme` :

| Token | Utilitaires générés |
|---|---|
| `--color-teal` | `bg-teal`, `text-teal`, `border-teal` |
| `--color-teal-soft` | `bg-teal-soft`, ... |
| `--color-ink` | `text-ink`, `bg-ink` |
| `--font-sans` | `font-sans` |
| `--radius-card` | `rounded-card` |

Les modificateurs d'opacité fonctionnent aussi : `bg-teal/15`, `text-ink/70`.

## Recolorer le projet

Changez la couleur primaire et toute l'application suit, sans toucher un seul
template :

```css
@theme {
  --color-teal: #1d4ed8;   /* la primaire passe au bleu */
}
```

Sauvegardez : si `npm run watch:css` tourne, `static/tailwind.css` est
reconstruit aussitôt.
Rafraîchissez le navigateur.

!!! tip "Renommer la charte"
    Les noms de tokens sont libres.
    Vous pouvez remplacer `teal` par `primary` partout (charte et templates)
    si vous préférez des noms sémantiques neutres.

??? note "À retenir"
    - Une seule source de vérité : le bloc `@theme` de `static/src/input.css`.
    - Chaque token devient un utilitaire Tailwind, réutilisable partout.
    - Recolorer = éditer un token, pas chercher dans les templates.

[Continuer avec La bibliothèque de composants](composants.md)
