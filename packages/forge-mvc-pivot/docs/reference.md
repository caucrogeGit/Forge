# Pivot advanced : référence

## 1. Objectif

Un pivot advanced est une table pivot `many_to_many` qui porte des attributs métier propres à la relation : `position`, `note`, `role`, `joined_at`, etc.

Ces attributs ne sont ni des colonnes de l'entité source ni de l'entité cible : ils appartiennent à l'**association elle-même**.
Le CRUD standard (`make:crud`) ne peut pas les gérer, car il synchronise uniquement des paires d'IDs.

Forge fournit deux briques :

- [`PivotAdvancedService`](references/service.md) : le service de persistance des associations ;
- [`make:pivot-crud`](references/make_pivot_crud.md) : le générateur opt-in d'un contrôleur et de gabarits dédiés.

## 2. Quand utiliser Pivot advanced ?

| Cas | Recommandation |
|---|---|
| `pivot.fields[]` vide | `make:crud` suffit (`<select multiple>` d'IDs) |
| `pivot.fields[]` tous nullables et non requis | `make:crud` suffit ; attributs ignorés |
| `pivot.fields[]` avec au moins un `required: true` ou `nullable: false` | `make:pivot-crud` obligatoire (`make:crud` est bloqué par le garde-fou) |
| `pivot.fields[]` avec attributs métier significatifs | `make:pivot-crud` recommandé |

L'exemple fil rouge est `Article` ↔ `article_tag` ↔ `Tag`, où chaque association porte `position` et `note`.

## 3. Référence par module

| Module | Page | Contenu |
|---|---|---|
| `service.py` | [Le service pivot](references/service.md) | `PivotAdvancedService`, contraintes, erreurs UX |
| `make_pivot_crud.py` | [Le générateur de sous-CRUD](references/make_pivot_crud.md) | `relations.json`, `make:pivot-crud`, fichiers générés |

## 4. Ce que Pivot advanced ne fait pas

- Il ne modifie pas `make:crud` : le CRUD d'entité classique reste **neutre** et inchangé.
- Il ne branche pas les routes **automatiquement** dans `mvc/routes.py`.
- Il ne génère pas de JavaScript avancé (drag & drop, ordre dynamique).
- Il n'intègre pas de logique RBAC.
- Les gabarits générés sont minimaux, conçus pour être adaptés.
- Une relation sans `pivot.fields[]` non vide n'a pas besoin de Pivot advanced.

## 5. Limites actuelles

- Pivot advanced est **opt-in** : rien n'est généré automatiquement.
- `make:crud` reste **neutre** : il ne lit pas `pivot.fields[]`.
- Les routes du sous-CRUD ne sont **pas branchées automatiquement** : elles sont documentées dans la sortie de `make:pivot-crud`.
- Les gabarits générés (`index.html`, `form.html`) sont **minimaux**.
- La synchronisation globale destructive (remplacer toutes les associations d'une source) n'est pas encore couverte : utilisez `detach` puis `attach`.
- L'accès par `id_field` est optionnel et doit être configuré explicitement.

Pour les tables pivot simples (sans attributs métier), voir Tables pivot many-to-many.
