# Bilan du parcours welcome-outils

Vous avez construit deux outils, un par famille, et vu où passe la frontière.

## Ce que vous avez construit

| Outil | Famille | Ce qu'il illustre |
|---|---|---|
| Calculateur de sous-réseau | SSR pur | service Python testable, POST protégé par CSRF, rendu Jinja échappé, zéro JavaScript |
| Oscilloscope | JavaScript-live | module local sous `static/js/`, chargé au `{% block scripts %}`, données par `data-*`, aucun nonce |

## Les règles à retenir

- **SSR pur d'abord** : la moitié des outils (calculateurs, convertisseurs) n'ont besoin d'aucun JavaScript.
- **Le calcul vit en Python**, dans un service testable, jamais dans le navigateur.
- **JavaScript local seulement** : servi depuis `static/js/`, autorisé par `script-src 'self'`, jamais de CDN.
- **Aucun script inline** : les données du serveur passent par des attributs `data-*` ou un bloc `<script type="application/json">`.
- **CSRF sur les formulaires**, **pas de HTML non assaini** : Jinja échappe par défaut, `| safe` uniquement sur du contenu que vous maîtrisez.

## Ce que Forge n'a pas eu à ajouter

Aucun de ces outils n'a demandé une nouvelle brique du framework.
Le service statique, la CSP `script-src 'self'` et le rendu Jinja existaient déjà.
Un bac à sable d'outils est une affaire d'**application**, pas de cœur : Forge fournit le motif et les garanties, le projet porte les outils.

## Pour aller plus loin

- Regroupez vos outils sous une section `/sandbox` avec un index qui les liste.
- Ajoutez d'autres calculateurs SSR purs (loi d'Ohm, code couleur des résistances, base64) sur le même motif que le sous-réseau.
- Rattachez un outil à une activité pédagogique de votre projet : c'est une décision propre à votre application.

## Voir aussi

- [Outils interactifs](../../features/outils-interactifs.md) : le guide de référence complet, avec les anti-patterns à éviter.
- [Front et CSS](../../features/front.md) : le socle front, `static/js/`, les layouts et composants.
