# Bilan : contenu et formulaires

Votre page showcase a maintenant du contenu et une saisie soignée.

## Ce que vous avez vu

- **Présentation** : `button` (trois variantes), `card`, `badge` (tons),
  `stat`, `alert`, `empty_state`.
- **Saisie** : `field`, `select_field`, `radio_group`, `checkbox`, `file_field`,
  `fieldset`, `submit`, avec le jeton CSRF inclus à la main.
- **Validation** : état d'erreur au champ (`error=...`), résumé `form_errors`,
  succès via `flash_messages`.

## À retenir

- Les composants couvrent la présentation et la saisie sans recopier de classes.
- La validation visuelle (champ rouge, résumé, flash) prolonge la validation
  serveur de Forge.

## Et ensuite

Il reste à afficher des listes de données et à ajouter de l'interactivité.

Le niveau avancé ajoute le tableau paginé, puis l'accordéon, le menu et la
modale, le tout sans framework JavaScript.

[Niveau avancé : Tableaux et pagination](../avance/tableaux.md)
