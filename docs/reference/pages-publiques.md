# Pages publiques génériques


Pages publiques séparées du CRUD admin, orientées visiteur. Forge génère
contrôleurs, routes et vues via cinq commandes dédiées. Chaque génération est
non destructive : les fichiers existants sont préservés.

### Pages publiques — Principe général

Les pages publiques et le CRUD admin coexistent dans le même projet mais ne
partagent ni contrôleurs, ni vues, ni routes. Le flux est serveur d'abord :

```
route publique → contrôleur public → lecture données → rendu Jinja → HTML public
```

Règles :

- une page publique ne doit pas exposer un CRUD admin brut aux visiteurs ;
- le SQL reste visible et explicite dans le code généré — pas d'ORM ;
- le HTML classique est la base : HTMX peut améliorer l'expérience sans la remplacer ;
- aucune logique métier spécifique (réservation, paiement, workflow) dans le core.

### Pages publiques — Commandes disponibles

| Commande | Rôle |
|---|---|
| `forge make:public-page <nom>` | Page publique simple sans entité |
| `forge make:public-list <Entite>` | Liste publique depuis une entité |
| `forge make:public-show <Entite>` | Fiche publique depuis une entité |
| `forge make:public-form <Entite>` | Formulaire public de saisie |
| `forge make:public-contact` | Page contact statique |

Toutes les commandes sont non destructives et idempotentes.
→ Voir les sections détaillées dans `### Pages publiques simples`, `### Listes publiques simples`, `### Fiches publiques simples`, `### Formulaires publics` et `### Page contact publique`.

### Pages publiques — Templates et layout public

Convention de fichiers :

```text
mvc/views/layouts/public.html   # layout visiteur
mvc/views/public/               # pages et vues publiques générées
mvc/views/components/           # composants Jinja réutilisables
```

Le layout public (`layouts/public.html`) expose les blocs `title`, `content` et
`scripts`. Il charge Tailwind et reste indépendant de HTMX et Alpine.js. Tous
les templates générés étendent ce layout.

### Pages publiques — Compatibilité i18n

Les générateurs utilisent des clés i18n standards si i18n est activé. Clés
prédéfinies dans `translations/fr.json` :

| Clé | Valeur par défaut |
|---|---|
| `public.page.generated` | Page publique générée par Forge. |
| `public.list.empty` | Aucun élément public à afficher. |
| `public.show.back` | Retour |
| `public.show.not_found` | Élément public introuvable. |
| `public.form.submit` | Envoyer |
| `public.form.success` | Votre demande a été envoyée. |
| `public.contact.title` | Contact |
| `public.contact.intro` | Vous pouvez nous contacter... |
| `public.contact.coordinates` | Coordonnées |
| `public.contact.address` | Adresse |
| `public.contact.email_label` | Email |
| `public.contact.phone` | Téléphone |

Pas de traduction automatique, pas de routes traduites, pas de détection de
langue imposée.

### Pages publiques — Médias publics

Les listes et fiches publiques générées intègrent les médias déclarés dans
l'entité en lecture seule. Aucun upload, aucune suppression, aucune
réorganisation n'est possible côté public.
→ Voir `### Médias dans les pages publiques` pour le comportement détaillé.

Le mécanisme de position des médias (`media_order`) est propre au système média
et ne dépend pas du champ `order_column` des relations `many_to_many`.

### Limites actuelles

- Pas de CMS complet ni d'éditeur visuel ;
- pas de constructeur de page ou de thème graphique avancé ;
- pas de gestion SEO avancée (méta dynamiques, sitemap) ;
- pas de recherche publique avancée ni de filtres publics complexes ;
- pas de pagination publique générée automatiquement ;
- pas d'envoi d'email depuis les formulaires publics générés ;
- pas de captcha ni de protection anti-spam intégré ;
- pas de workflow, réservation ou paiement dans le core ;
- pas de SPA, pas de React/Vue/Svelte ;
- pas de logique métier Communes & Séjours dans le core ;
- pas de génération automatique d'un site complet sans intervention développeur ;
- pas de modification automatique des pages publiques existantes.

