# Bilan : le système de design

Vous savez maintenant utiliser le système de design livré avec votre projet.

## Ce que vous avez vu

- **La charte graphique** vit dans le bloc `@theme` de `static/src/input.css`.
  Chaque token (couleur, police, rayon) devient un utilitaire Tailwind ;
  recolorer le projet revient à éditer un token.
- **Le gabarit partagé** `mvc/views/layouts/base.html` applique la charte ;
  vos pages l'étendent avec `{% extends %}`.
- **La bibliothèque de composants** (`mvc/views/components/`) fournit des macros
  Jinja réutilisables : `button`, `card`, `badge`, `alert`, et les champs de
  formulaire (`field`, `select_field`, `checkbox`, `submit`).
- **Le mode watch** (`npm run watch:css`) reconstruit le CSS à chaque
  sauvegarde.

## À retenir

- Une seule source de vérité pour l'apparence : le bloc `@theme`.
- Les composants évitent de recopier des classes Tailwind dans chaque page.
- Charte et composants sont **votre code** : étendez-les librement, le noyau
  Forge n'impose aucune apparence.

## Pour aller plus loin

- [Front et CSS](../../features/front.md) : la gestion des assets front du projet.
- [Héritage de gabarit](../welcome-forge/intermediaire/layout-template.md) :
  le principe `{% extends %}` / `{% block %}` appliqué pas à pas.

Réappliquez ce système à toutes vos pages : une charte centrale, un gabarit
partagé, des composants réutilisables.
