# Parcours welcome-outils

Ce parcours montre comment construire des **outils interactifs** dans une application Forge, proprement et sous CSP stricte.
Il s'adresse à un projet pédagogique qui veut offrir un bac à sable d'outils aux élèves, sans SPA, sans CDN, sans JavaScript imposé.

La politique et le motif sont posés dans le guide [Outils interactifs](../../features/outils-interactifs.md).
Ce parcours les met en pratique sur deux outils, un par famille.

## Ce que vous allez construire

Deux outils, du plus simple au plus riche :

1. **Calculateur de sous-réseau** : un outil **SSR pur**, sans JavaScript.
   Un formulaire, un POST protégé par CSRF, un service Python testable, un rendu Jinja.
   C'est le motif idiomatique de Forge, à préférer chaque fois qu'il suffit.
   [Suivre](subnet-calculator.md)

2. **Oscilloscope** : un outil **temps réel**, avec du JavaScript **local**.
   Un canvas animé piloté par un module servi depuis `static/js/`, autorisé par `script-src 'self'` sans nonce.
   [Suivre](oscilloscope.md)

Un [bilan](bilan.md) referme le parcours et renvoie au guide de référence.

## Prérequis

- Un projet Forge fonctionnel, avec la protection CSRF active (parcours cœur [welcome-forge](../welcome-forge/debutant/welcome.md) jusqu'au palier CSRF).
- Le socle front standard : `static/js/` et le bloc `{% block scripts %}` des layouts (voir [Front et CSS](../../features/front.md)).

## Principe directeur

Avant d'écrire une seule ligne de JavaScript, posez-vous la question : **l'outil peut-il se contenter du SSR pur ?**
La moitié des outils courants (calculateurs, convertisseurs) tombent dans cette famille et ne demandent aucun JavaScript.
Le JavaScript local reste réservé aux outils réellement temps réel : animation, curseurs en direct, canvas.

[Commencer avec le calculateur de sous-réseau](subnet-calculator.md)
