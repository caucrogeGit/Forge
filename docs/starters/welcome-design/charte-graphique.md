# Charte graphique : « Accessible chaleureux »

Document de référence de l'identité visuelle du squelette : palette, typographie,
rayons et règles d'usage. La source unique de ces valeurs est le bloc `@theme`
de `static/src/input.css` ; cette page en explique le **sens**.

Pour apprendre à modifier la charte pas à pas, voir le palier
[La charte graphique](debutant/charte.md).

## Esprit

Une interface **chaleureuse et lisible** : fonds crème plutôt que blanc pur,
la couleur primaire **orange Forge** (signature de la marque), un accent ocre
ponctuel, et une hiérarchie de texte nette. L'objectif est un service clair, à
fort contraste, sans surcharge.

## Palette

Chaque couleur est un token `--color-<nom>` qui génère les utilitaires Tailwind
`bg-<nom>`, `text-<nom>`, `border-<nom>`.

### Primaire et accent

| Aperçu | Token | Hex | Rôle |
|---|---|---|---|
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#E8651A;border:1px solid #0003"></span> | `forge` | `#E8651A` | couleur primaire, orange Forge : actions, liens, éléments actifs |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#c2540f;border:1px solid #0003"></span> | `forge-dark` | `#c2540f` | survol et état pressé de la primaire |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#fff3ea;border:1px solid #0003"></span> | `forge-soft` | `#fff3ea` | fonds doux : badges, boutons secondaires |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#f6d3bf;border:1px solid #0003"></span> | `forge-border` | `#f6d3bf` | bordures douces sur fond forge-soft |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#d98a2b;border:1px solid #0003"></span> | `ocre` | `#d98a2b` | accent ponctuel : indicateur requis, avertissements |

### Texte

| Aperçu | Token | Hex | Rôle |
|---|---|---|---|
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#211f1a;border:1px solid #0003"></span> | `ink` | `#211f1a` | texte principal et titres |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#403b32;border:1px solid #0003"></span> | `subtle` | `#403b32` | libellés de formulaire |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#5d574c;border:1px solid #0003"></span> | `muted` | `#5d574c` | texte secondaire, descriptions |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#a39b8c;border:1px solid #0003"></span> | `faint` | `#a39b8c` | méta, aides discrètes, états désactivés |

### Fonds et lignes

| Aperçu | Token | Hex | Rôle |
|---|---|---|---|
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#faf8f4;border:1px solid #0003"></span> | `cream` | `#faf8f4` | fond de page |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#fffdf9;border:1px solid #0003"></span> | `surface` | `#fffdf9` | surfaces surélevées : cartes, en-tête |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#ece6dc;border:1px solid #0003"></span> | `line` | `#ece6dc` | bordures et séparateurs |
| <span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:4px;background:#ddd6ca;border:1px solid #0003"></span> | `field` | `#ddd6ca` | bordures de champs de formulaire |

## Typographie

| Usage | Token | Police | Utilitaire |
|---|---|---|---|
| Corps et titres | `--font-sans` | Figtree | `font-sans` |
| Code et données techniques | `--font-mono` | JetBrains Mono | `font-mono` |

Graisses employées : `font-medium` (texte courant accentué), `font-semibold`
(libellés, liens), `font-bold` et `font-extrabold` (titres). Les polices sont
chargées dans `layouts/base.html` ; en repli, la pile `system-ui` prend le
relais.

## Formes

| Token | Valeur | Utilitaire | Usage |
|---|---|---|---|
| `--radius-card` | `16px` | `rounded-card` | cartes, panneaux, modale |

Les boutons et champs utilisent un rayon plus serré (`rounded-[10px]`) pour
contraster avec les cartes.

## Règles d'usage

- **Primaire avec parcimonie** : `forge` (orange Forge) signale l'action principale et les liens.
  Évitez de le multiplier sur une même vue.
- **Ocre = accent, pas décor** : réservé aux signaux (champ requis, attention).
- **Hiérarchie du texte** : `ink` pour le contenu fort, `muted` pour le
  secondaire, `subtle` pour les libellés, `faint` pour la méta. Ne sautez pas
  d'un titre `ink` directement à `faint`.
- **Profondeur sobre** : `cream` pour la page, `surface` pour ce qui est posé
  dessus (cartes, en-tête), `line` pour délimiter. Pas d'ombres lourdes.
- **Contraste** : la charte vise un bon contraste (esprit RGAA) ; vérifiez-le si
  vous changez les tokens.

## Personnaliser

Modifiez les valeurs dans le bloc `@theme` de `static/src/input.css`, puis
reconstruisez le CSS (`npm run build:css` ou `npm run watch:css`). Tout ce qui
utilise les utilitaires correspondants suit, sans toucher aux templates.

Voir aussi : [Récapitulatif des composants](recapitulatif.md).
