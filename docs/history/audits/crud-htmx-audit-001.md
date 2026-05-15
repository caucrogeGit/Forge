# Audit CRUD-HTMX-AUDIT-001

## Résumé

Conclusion : **partiellement prêt — Cas B, préparation nécessaire**.

Forge possède un socle HTMX propre : `forge js:init htmx` prépare la dépendance
officielle, les layouts exposent un bloc `{% block scripts %}`, la
documentation explique l'usage optionnel et les tests garantissent que HTMX
n'est pas chargé automatiquement.

Le CRUD généré reste, lui, un CRUD HTML classique robuste : recherche `q`,
filtres, tri, pagination, états vides et suppression fonctionnent sans
JavaScript. En revanche, `make:crud` ne génère pas encore de fragments ou
partials de liste utilisables par HTMX. Lancer directement la recherche HTMX
risquerait donc de dupliquer le template `index.html` ou d'introduire une
convention implicite.

## État du support HTMX

La commande `forge js:init htmx` existe dans `forge_cli/front.py`.

Comportement observé :

- ajoute la dépendance npm officielle `htmx.org` ;
- prépare `static/vendor/htmx/htmx.min.js` si `node_modules` est disponible ;
- crée ou préserve `static/js/app.js` ;
- n'écrase pas un fichier vendor existant ;
- ne modifie pas les layouts ;
- reste idempotente.

Les commandes voisines `forge js:init alpine` et `forge js:init htmx-alpine`
sont aussi présentes. Les tests `tests/test_front_js_init.py` couvrent les
fichiers créés, la préservation des fichiers existants, les dépendances npm et
l'absence de modification automatique des layouts.

Les layouts standards dans `mvc/views/layouts/` chargent seulement :

```html
<script src="/static/js/app.js" defer></script>
```

Ils exposent aussi :

```jinja
{% block scripts %}{% endblock %}
```

Le test `tests/test_front_layout_contract.py` vérifie que les layouts ne
chargent pas HTMX ou Alpine par défaut et qu'ils ne contiennent pas d'attributs
`hx-*`.

La documentation `docs/front.md` explique :

- l'initialisation par `forge js:init htmx` ;
- le chargement explicite dans `{% block scripts %}` ;
- les attributs HTMX de base ;
- la nécessité de garder les routes et fragments explicites ;
- le fait que `make:crud` ne génère pas encore de recherche, pagination ou
  suppression HTMX.

## État du CRUD HTML classique

Le CRUD généré par `forge make:crud` est actuellement 100 % HTML classique.

Comportement observé :

- recherche `q` via formulaire GET ;
- filtres simples déclaratifs via `list.filter=true` ;
- filtres relationnels `many_to_one` automatiques ;
- tri simple par `sort` et `direction`, sécurisé par allowlist ;
- pagination serveur via `Pagination` ;
- états vides contextuels côté Jinja ;
- suppression via formulaire POST avec confirmation native `confirm()` ;
- relations `many_to_many` côté source dans les formulaires et list/show ;
- aucun `hx-*`, aucun `<script>` et aucune dépendance HTMX dans les templates
  générés.

Les tests récents confirment explicitement l'absence d'HTMX ou de JavaScript
dans la recherche, la pagination, le tri et les états vides.

## État des fragments / partials

Forge possède des composants Jinja génériques dans `mvc/views/components/`,
notamment `table.html` et `pagination.html`, mais ils ne constituent pas encore
une convention de fragments CRUD HTMX.

État observé :

- `make:crud` génère `mvc/views/<entite>/index.html` comme page complète ;
- le tableau, le formulaire de recherche, les filtres, le tri, la pagination et
  l'état vide sont rendus en HTML inline dans `index.html` ;
- seul `components/button.html` est utilisé par les templates CRUD générés ;
- aucun fichier généré du type `_table.html`, `_list.html` ou
  `index_table.html` ;
- aucun contrôleur généré ne choisit entre page complète et fragment ;
- aucune convention de rendu partiel par en-tête HTMX ou endpoint explicite ;
- `BaseController.include()` existe, mais n'est pas utilisé comme convention
  CRUD générée.

Les exemples de `docs/front.md` montrent des fragments manuels comme
`contacts/_liste.html`, mais ce sont des exemples applicatifs, pas une
fonctionnalité générée par `make:crud`.

## Analyse

Peut-on ajouter `CRUD-HTMX-001` sans brique préparatoire ?

Non, pas proprement. Le support HTMX général est prêt, mais les CRUD générés
n'ont pas encore de zone partielle stable à remplacer. Ajouter directement
`hx-get` sur la recherche imposerait de décider en même temps du découpage du
template, de la route fragment, du contexte minimal et du fallback.

Faut-il d'abord créer des partials CRUD ?

Oui. Une petite brique préparatoire doit extraire ou générer un fragment de
liste stable, par exemple pour la table, l'état vide et la pagination. Cette
brique doit rester utile même sans HTMX et éviter la duplication du HTML entre
page complète et réponse partielle.

Le fallback HTML classique est-il garanti ?

Oui dans l'état actuel. Le CRUD généré fonctionne sans JavaScript, avec des
formulaires GET, des liens de pagination, des liens de tri et des formulaires
POST classiques. Les tests vérifient explicitement l'absence de `hx-*`.

HTMX peut-il rester optionnel ?

Oui, à condition de conserver les attributs HTML classiques (`href`, `method`,
`action`) et de charger HTMX uniquement quand l'application le demande. La
future recherche HTMX devra améliorer le comportement existant, pas le
remplacer.

Quels risques ?

- dupliquer le tableau entre page complète et fragment ;
- casser la conservation de `q`, filtres, tri et pagination ;
- rendre HTMX obligatoire par accident ;
- mélanger logique JavaScript et règles serveur ;
- oublier CSRF sur les futurs `hx-post` ou `hx-delete` ;
- créer une mini-SPA au lieu d'une amélioration progressive.

## Conclusion

### Cas B — Préparation nécessaire

Le support HTMX de Forge est prêt côté front, mais le CRUD généré a besoin
d'une convention de partials avant `CRUD-HTMX-001`.

Le prochain ticket recommandé est `CRUD-HTMX-PARTIALS-001` : créer un fragment
CRUD de liste réutilisable par la page complète et par les futures réponses
HTMX, sans ajouter encore de `hx-*`.

## Recommandation

Créer `CRUD-HTMX-PARTIALS-001`.
Il doit définir un fragment de liste CRUD stable, garder le fallback HTML,
préserver `q`/filtres/tri/pagination et éviter toute duplication de template.
Ensuite seulement, lancer `CRUD-HTMX-001` pour la recherche HTMX optionnelle.
