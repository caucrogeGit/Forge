# Préambule : le système de design du projet

Ce parcours vous apprend à utiliser le **système de design** livré par `forge new` :
une charte graphique centralisée et une bibliothèque de composants réutilisables.

**Ce que vous allez apprendre :**{ .intro-label } où vit la charte, comment la
personnaliser en un seul endroit, comment réutiliser les composants HTML
normalisés dans vos pages, et comment lancer Tailwind en surveillance pour un
confort de développement.

!!! info "Pourquoi côté projet"
    Le noyau Forge reste minimal et n'impose aucune apparence.
    La charte et les composants sont **votre code**, livrés dans le squelette
    pour démarrer cohérent, et entièrement libres d'évolution.

## Là où nous en sommes

Un projet créé par `forge new` contient déjà trois pièces :

| Fichier | Rôle |
|---|---|
| `static/src/input.css` | la charte graphique (bloc `@theme` Tailwind v4) |
| `mvc/views/layouts/base.html` | le gabarit partagé qui applique la charte |
| `mvc/views/components/` | la bibliothèque de composants (macros Jinja) |

La page d'accueil et les pages d'erreur utilisent déjà ce système : ouvrez-les
pour voir les composants en situation.

## Prérequis

- Un projet Forge déjà créé (voir [Parcours Welcome Forge](../welcome-forge/index.md)).
- Node.js installé (les dépendances Tailwind sont posées par `forge new`).

## Le confort : le mode watch

Plutôt que de relancer la compilation du CSS à la main après chaque changement,
ouvrez un second terminal et lancez Tailwind en surveillance :

```bash
npm run watch:css
```

Il reconstruit `static/tailwind.css` à chaque sauvegarde d'un template ou de la
charte.
Il ne vous reste qu'à rafraîchir le navigateur (`Ctrl+Shift+R` si le CSS semble
en cache).

!!! note "Build ponctuel"
    Pour une compilation unique (avant un commit, en production), utilisez
    `npm run build:css` : même sortie, minifiée, sans surveillance.

[Continuer avec La charte graphique](charte-graphique.md)
