# Audit CRUD-EXPORT-AUDIT-001 — Export CSV CRUD

## Objectif

Déterminer comment Forge peut ajouter un export CSV aux listes CRUD générées, sans créer de faille de sécurité ni de comportement ambigu.

---

## État actuel du CRUD

L'audit porte sur les fichiers générés par `forge make:crud`. Aucune fonctionnalité d'export n'existe à ce jour.

Les mécanismes de sécurité suivants sont déjà en place dans le modèle généré :

| Mécanisme | Rôle |
|---|---|
| `_ALLOWED_SORT` | Whitelist des colonnes triables ; empêche toute injection via `sort` |
| `_ALLOWED_FILTERS` | Whitelist des colonnes filtrables ; empêche toute injection via les paramètres de filtre |
| `_SEARCH_COLS` | Liste des colonnes textuelles pour `LIKE` ; construite à la génération |
| Placeholders `?` | Tous les paramètres utilisateur sont transmis comme valeurs liées, jamais concaténés |

La fonction `find_{plural}_paginated(q, sort, direction, limit, offset, filters)` centralise déjà toute la logique de liste sécurisée. Un export peut la réutiliser.

Les actions RBAC déclarées sont : `index`, `show`, `create`, `store`, `edit`, `update`, `delete`. Il n'existe pas encore d'action `export`.

---

## Besoin fonctionnel

Un utilisateur qui filtre une liste CRUD veut pouvoir télécharger le résultat sous forme de fichier CSV. L'export doit refléter exactement ce que la liste montre (même filtres, même tri), sans limite de pagination.

---

## Scénarios possibles

**Scénario A — Export de la page courante uniquement**

- Volume limité, simple à implémenter.
- Peu utile : l'utilisateur exporte 20 lignes alors qu'il y en a 500 qui correspondent à ses critères.
- **Rejeté.**

**Scénario B — Export de tous les résultats filtrés**

- Respecte `q`, filtres et tri.
- Ignore la pagination : exporte l'ensemble des lignes correspondant aux critères.
- Applique une limite maximale de sécurité (voir § Volume).
- **Retenu.**

---

## Route d'export

**Route recommandée :**

```
GET /{plural}/export.csv
```

Exemples :

```
GET /contacts/export.csv
GET /contacts/export.csv?q=roger&statut=actif&sort=nom&direction=asc
```

L'extension `.csv` signale au navigateur et aux proxies que la réponse est un fichier téléchargeable. Certains navigateurs ouvrent automatiquement un gestionnaire de téléchargement.

**Alternative écartée : `GET /{plural}/export`** — moins explicite sur le format, peut prêter à confusion si d'autres formats sont ajoutés plus tard. L'extension `.csv` est préférable.

---

## Données exportées

- Exporter **tous les résultats correspondant aux critères** (`q`, filtres, tri), sans limite de pagination.
- Appliquer une **limite maximale de 1 000 lignes** par défaut (voir § Volume).
- Ne pas exporter les colonnes PK si elles ne sont pas affichées dans la liste — à confirmer à l'implémentation.
- Exporter les mêmes colonnes non-PK que la vue `index`. Pour les relations `many_to_one`, exporter le libellé (`*_label`) si disponible, sinon la clé étrangère brute.

---

## Compatibilité q / filtres / tri

L'export doit respecter **tous les paramètres de liste actifs** :

| Paramètre | Comportement attendu |
|---|---|
| `q` | Appliqué (`LIKE %q%` sur `_SEARCH_COLS`) |
| filtres | Appliqués (via `_ALLOWED_FILTERS`) |
| `sort` | Appliqué (via `_ALLOWED_SORT`) |
| `direction` | Appliqué (`asc` / `desc`) |
| `page` | **Ignoré** — l'export couvre l'ensemble filtré |

Le lien d'export dans la liste transmet les paramètres courants dans l'URL :

```html
<a href="/contacts/export.csv?q={{ pagination.q | urlencode }}&sort={{ pagination.sort }}...">
    Exporter CSV
</a>
```

---

## Pagination et volume

La pagination est ignorée pour l'export. La limite est une contrainte de sécurité indépendante.

**Limite recommandée : 1 000 lignes.**

Justification :
- Au-delà, le temps de génération devient perceptible côté serveur.
- Un CSV de 1 000 lignes reste exploitable dans un tableur.
- Si la limite est atteinte, le fichier doit l'indiquer (nom de fichier, en-tête de commentaire ou en-tête HTTP `X-Export-Truncated: true`).

Constante générée :

```python
_EXPORT_LIMIT = 1000
```

---

## Colonnes exportables

**Convention recommandée pour ce ticket :**

Exporter les colonnes non-PK affichées dans la vue `index`, dans le même ordre. Aucune annotation `list.export: true` n'est nécessaire pour la V1.

Pour les relations `many_to_one` : exporter la colonne `*_label` (alias SQL de la jointure) si présente ; sinon la clé étrangère.

Exemple d'en-têtes CSV générés pour une entité `Contact(nom, email, statut)` :

```
Nom,Email,Statut
```

**Évolution future possible :**

```json
{ "name": "email", "list": { "export": false } }
```

Pour exclure certaines colonnes sensibles (mot de passe haché, token interne…). À documenter dans CRUD-EXPORT-CSV-001 si nécessaire.

---

## RBAC

**Recommandation : réutiliser la permission `index` (ou `read`).**

Justification :
- Un utilisateur qui peut voir la liste peut en exporter le contenu — l'export ne révèle pas plus d'informations que la liste.
- Créer une permission dédiée `{entity}.export` est prématuré pour la V1.
- La permission `index` est déjà définie dans le bloc `rbac.permissions` si RBAC est actif.

Comportement attendu :
- Sans RBAC dans la définition : export toujours accessible (comme la liste).
- Avec RBAC : l'export est protégé par `@require_permission("{entity}.index")`.

**Évolution future :** documenter que `{entity}.export` peut remplacer `{entity}.index` pour un contrôle plus fin.

---

## Sécurité CSV

Le format CSV est vulnérable à l'injection de formules dans les tableurs (Excel, LibreOffice). Une valeur comme `=HYPERLINK("http://evil.example.com")` dans une cellule peut être interprétée comme une formule.

**Valeurs dangereuses à neutraliser :**

Toute cellule commençant par `=`, `+`, `-`, `@` doit être préfixée d'une apostrophe `'` pour empêcher l'interprétation comme formule :

```python
DANGEROUS_PREFIXES = ('=', '+', '-', '@')

def _csv_escape(value: str) -> str:
    if value and value[0] in DANGEROUS_PREFIXES:
        return "'" + value
    return value
```

Cette mitigation est recommandée par l'OWASP (CSV Injection).

**Toutes les valeurs doivent également être entourées de guillemets doubles** dans le CSV (`quoting=csv.QUOTE_ALL`) pour neutraliser les injections via les sauts de ligne (`\r\n` dans une valeur).

---

## Headers HTTP

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="contacts.csv"
Cache-Control: no-store
```

- `Content-Type` : signale le format CSV avec encodage UTF-8.
- `Content-Disposition: attachment` : force le téléchargement (empêche l'affichage inline).
- `Cache-Control: no-store` : empêche la mise en cache des données potentiellement sensibles par les proxies ou le navigateur.

Le nom de fichier doit correspondre à l'entité plurielle (`contacts.csv`, `articles.csv`…).

---

## SQL et sécurité

L'export doit **réutiliser les mécanismes existants** du modèle généré :

- `_ALLOWED_SORT.get(sort, _DEFAULT_SORT)` pour la colonne de tri.
- `_ALLOWED_FILTERS.get(key)` pour les filtres.
- Placeholders `?` pour toutes les valeurs liées.
- Aucune concaténation directe de valeurs utilisateur.

**Fonction recommandée :**

```python
def find_{plural}_for_export(q=None, sort=None, direction="asc", filters=None):
    """Retourne au maximum _EXPORT_LIMIT enregistrements pour l'export CSV."""
    return find_{plural}_paginated(
        q=q, sort=sort, direction=direction,
        limit=_EXPORT_LIMIT, offset=0, filters=filters,
    )
```

Cette approche réutilise la fonction existante, garantit les mêmes sécurités et évite toute duplication de logique SQL.

---

## HTMX

L'export CSV **ne doit pas utiliser HTMX**.

Un clic sur le lien d'export déclenche un téléchargement de fichier — HTMX intercepterait la réponse et tenterait de la placer dans `#crud-results`, ce qui serait incorrect.

Le lien d'export doit être un `<a href>` classique :

```html
<a href="/contacts/export.csv?q={{ pagination.q | urlencode }}&sort=...&direction=...{% for key, val in pagination.filters.items() %}{% if val %}&{{ key }}={{ val | urlencode }}{% endif %}{% endfor %}">
    Exporter CSV
</a>
```

Pas de `hx-get`, pas de `hx-target`, pas de `hx-push-url`.

---

## Risques identifiés

| Risque | Niveau | Mitigation recommandée |
|---|---|---|
| Injection CSV (formules) | Élevé | Préfixe `'` sur `=`, `+`, `-`, `@` + `QUOTE_ALL` |
| Export sans RBAC | Élevé | `@require_permission` si `index` configuré |
| Volume illimité (DoS) | Moyen | `_EXPORT_LIMIT = 1000` |
| Mise en cache de données sensibles | Moyen | `Cache-Control: no-store` |
| Injection SQL via `sort`/filtres | Faible (déjà mitigé) | `_ALLOWED_SORT` + `_ALLOWED_FILTERS` existants |
| Encodage incorrect (caractères non-ASCII) | Faible | `charset=utf-8` dans `Content-Type` + BOM optionnel |
| HTMX interceptant la réponse | Faible | Lien `<a href>` sans attributs HTMX |

---

## Recommandation

**Implémenter un export CSV minimal dans le ticket `CRUD-EXPORT-CSV-001`.**

Périmètre recommandé :

- Route `GET /{plural}/export.csv`.
- Paramètres `q`, filtres, `sort`, `direction` respectés.
- Export de **tous les résultats filtrés**, limite `_EXPORT_LIMIT = 1000`.
- Colonnes : non-PK affichées dans `index`, labels relationnels si disponibles.
- RBAC : `@require_permission("{entity}.index")` si configuré.
- Protection CSV injection : préfixe `'` + `QUOTE_ALL`.
- Headers : `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="{plural}.csv"`, `Cache-Control: no-store`.
- Lien d'export dans `_table.html` (ou `index.html`) : `<a href>` classique, pas de HTMX.
- Tests unitaires : whitelist réutilisée, injection neutralisée, headers corrects, limite appliquée.
- Aucun JS, aucune dépendance externe — la bibliothèque standard `csv` de Python suffit.

---

## Ticket suivant proposé

**`CRUD-EXPORT-CSV-001` — Ajouter un export CSV minimal aux listes CRUD générées.**

Livrables :

- `find_{plural}_for_export(...)` dans le modèle généré.
- `export_csv(request)` dans le contrôleur généré.
- Route `GET /{plural}/export.csv` dans `_route_block`.
- Lien d'export dans `_table.html` (hors zone HTMX, avant la table).
- Protection CSV injection via `_csv_escape`.
- Headers HTTP corrects.
- Tests unitaires.
- Documentation dans `reference.md`.
