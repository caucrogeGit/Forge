# Modèle de starter Forge : la référence « welcome »

> **Document de référence.** Le starter **Bonjour Forge** (la progression
> `welcome-forge`) est le **modèle canonique** de tout travail sur les starters
> Forge : tout futur starter de progression se calque sur son **organisation**
> (sous-dossiers par niveau de difficulté `debutant/` `intermediaire/` `avance/`,
> bilan par niveau, récapitulatif racine), son **formalisme** (structure des
> pages) et son **fonctionnement** (paliers à responsabilité unique, navigation
> palier → bilan du niveau → niveau suivant ou récapitulatif).
>
> **Audience** : contributeurs (humains et agents IA) qui créent ou modifient
> un starter. Cette page est volontairement opérationnelle : copiez le
> pattern, suivez les checklists.
>
> Complète la [charte philosophique](../philosophy/charter.md) (principes 2,
> 5, 8, 10, 11) et les [conventions internes](conventions.md).

## Exemples canoniques à copier

| Besoin | Fichier(s) de référence |
|--------|-------------------------|
| Palier minimal (1 route, réponse texte) | [welcome.md](../starters/welcome-forge/debutant/welcome.md) |
| Palier avec vue HTML + formulaire | [form-post.md](../starters/welcome-forge/debutant/form-post.md) |
| Palier « concept » (explication + formulaire illustratif) | [csrf.md](../starters/welcome-forge/debutant/csrf.md) |
| Palier SQL visible (lecture / écriture) | [first-sql.md](../starters/welcome-forge/debutant/first-sql.md), [first-sql-write.md](../starters/welcome-forge/debutant/first-sql-write.md) |
| Dernier palier du niveau → bilan du niveau | [first-sql-write.md](../starters/welcome-forge/debutant/first-sql-write.md) |
| Bilan d'un niveau (dans le dossier du niveau) | [debutant/bilan.md](../starters/welcome-forge/debutant/bilan.md) |
| Page bilan / aide-mémoire de fin | [bilan.md](../starters/welcome-forge/debutant/bilan.md), [recapitulatif.md](../starters/welcome-forge/recapitulatif.md) |

Côté code (non liés ici car hors `docs/`) :
`cli/starters/data/welcome/`.

---

## Conventions de nommage des starters

Tout starter porte un **nom anglais**. Le nom encode **d'où vient la capacité
démontrée** via un token central :

| Famille | Schéma | Exemples |
|---------|--------|----------|
| Progression de découverte | `welcome` + nom de concept | `welcome`, `query-params`, `first-html-view`, `first-sql`… |
| Capstone CRUD | `first-crud[-variante]` | `first-crud` (à la main), `first-crud-generated` (généré) |
| Starter d'**opt-in** | `welcome-optin-<module>` | `welcome-optin-iot`, `welcome-optin-mfa` |
| Starter d'**API cœur** | `<sujet>-core-<api>` | `users-core-auth` |

Le token central (`optin` / `core`) signale d'où vient la capacité.

**Organisation par niveau de difficulté (modèle de référence)** : la doc d'un
starter de progression est rangée en **sous-dossiers de niveau** sous le dossier
du starter. Le modèle canonique est `welcome-forge` :

```text
docs/starters/welcome-forge/
├── recapitulatif.md          ← aide-mémoire global (racine du starter)
├── debutant/                 ← niveau 1
│   ├── <paliers>.md          (welcome → first-sql-write…)
│   └── bilan.md              ← bilan DU niveau (page sœur des paliers)
├── intermediaire/            ← niveau 2 (à venir : mêmes règles)
│   ├── <paliers>.md
│   └── bilan.md
└── avance/                   ← niveau 3 (à venir)
    ├── <paliers>.md
    └── bilan.md
```

Règles **non négociables** de cette organisation :

- **Niveaux** : `debutant/`, `intermediaire/`, `avance/`. Un niveau n'est créé
  qu'avec son contenu (pas de dossier vide).
- **Un `bilan.md` par niveau**, **dans le dossier du niveau** (pas à la racine).
- **Un seul `recapitulatif.md`**, **à la racine** du starter, transversal aux
  niveaux.
- **data à plat** : `cli/starters/data/<id>/` (un dossier par starter
  buildable) ; le `doc_url` pointe vers le chemin-niveau
  (`/starters/<starter>/<niveau>/<id>/`).

> Les starters d'**opt-in** (`welcome-optin-<module>`) et d'**API cœur**
> (`<sujet>-core-<api>`) gardent leur dossier-sujet propre
> (`docs/starters/optin-iot/`…) ; l'organisation par niveau ci-dessus est le
> modèle des **progressions** calquées sur `welcome-forge`.

Une **application métier** (multi-entités, domaine réel) **n'est pas un starter** :
elle est archivée sous `docs/starters/old/` et retirée du registry.

> Détail et phasage : [roadmap de réorganisation des starters](../roadmap/starter-reorg-roadmap.md).

---

## 1. Principe directeur : un palier = une responsabilité

Chaque palier introduit **une seule notion nouvelle**. Aucune notion qui
appartient à un palier ultérieur ne doit apparaître avant.

- Le palier 1 (`welcome`) ne montre **que** `Response.text(...)`, pas de
  `request.query(...)` (c'est le palier 2 `query-params`).
- Le palier CSRF explique le jeton **sans** traiter le POST (c'est le palier
  `form-post`).
- Chaque page liste explicitement **ce qu'elle ne fait pas** (« Aucune base
  de données. Aucun CRUD. ») pour cadrer le périmètre.

C'est l'application directe du **principe 2 de la charte** (« petits tickets,
une responsabilité ») au niveau pédagogique.

**Conséquence pratique** : si en rédigeant un palier vous devez utiliser une
API non encore introduite, c'est le signe qu'il manque un palier intermédiaire, ne la glissez pas « en passant ».

---

## 2. Anatomie d'une page de palier (formalisme)

Une page de palier vit dans `docs/starters/<starter>/<niveau>/<id>.md`
(ex. `docs/starters/welcome-forge/debutant/welcome.md`) et suit **toujours**
cet ordre de sections. Les liens de référence partent d'un dossier de niveau :
deux remontées (`../../`) atteignent la vue d'ensemble du starter, trois
(`../../../`) atteignent `reference/`, `features/`, etc. :

````markdown
# <Nom lisible du palier>

Objectif : <une phrase - ce que le palier réalise>.

**Ce que vous allez apprendre :** <2-3 phrases sur la notion ciblée et l'API
concernée>.

Palier <N> de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [<palier précédent>](<precedent>.md).

*Prérequis : <ligne légère si le palier en suppose un>.*   ← optionnel

## Ce que ce starter montre
- <route / concept 1>
- <route / concept 2>

Aucune <hors-périmètre 1>.
Aucune <hors-périmètre 2>.

## Pourquoi <concept> ?         ← optionnel, pour un palier « concept » (ex. CSRF)
<explication pédagogique>

## Classes Forge utilisées
| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request`  | … | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | … | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | … | [BaseController](../../../core-mvc/base_controller.md#coremvccontroller) |

## Tester
```bash
forge run
```
Ouvrez `https://localhost:8000/<route>` → <résultat attendu>.

## Les routes
```python
# mvc/routes.py
…
```

## Le contrôleur
```python
# mvc/controllers/<x>_controller.py
…
```
### Comprendre ce code
- <bullets expliquant chaque ligne clé>

## La vue          ← si vue HTML
```html
<!-- mvc/views/<x>/index.html -->
…
```
### Comprendre ce code
- <bullets>

## À retenir
- <points-clés réutilisables>

## Après ce starter
<voir section 3>
````

**Règles de forme non négociables :**

- **HTTPS**, jamais `http://`, dans toutes les URL d'exemple.
- Le **code montré est complet et vérifié**, pas d'extrait partiel, pas de
  `...` à la place d'une ligne réelle. Ce qui est affiché doit fonctionner tel
  quel une fois le starter généré.
- Liens de référence vers `../../../reference/http.md`, `../../../reference/api.md`,
  `../../../features/migrations.md` (db), vérifier l'ancre.
- Pas de commande d'installation/création dans la page d'un palier
  (`forge new …`, `forge starter:build …`, `cd …`, `source .venv/...`) : la
  page suppose qu'on est déjà dans un projet généré. Ces commandes vivent dans
  la doc globale.
- Pas d'étiquette « Starter N » dans le texte pédagogique (le numéro reste
  dans `starter.json` et les tests techniques).

---

## 3. Navigation par niveau : palier → bilan du niveau → suite

La progression est rythmée par niveau. Le chaînage **canonique** (modèle
`welcome-forge`) est :

```text
palier 1 → palier 2 → … → dernier palier du niveau → bilan DU niveau
                                                         │
                              premier palier du niveau suivant s'il existe
                                                         │  sinon
                                       recapitulatif.md (racine du starter)
```

**Palier intermédiaire**, lien vers le palier suivant (fichier frère du
même niveau) :

```markdown
## Après ce starter

Passez au palier suivant : **<Nom>** - <ce qu'on y apprend>.

[Continuer avec <Nom>](<slug-suivant>.md)
```

**Dernier palier d'un niveau**, lien vers le **bilan du niveau** (page sœur
`bilan.md`, dans le dossier du niveau) :

```markdown
## Après ce starter

C'est le **dernier palier** du niveau **<niveau>** du starter <Nom>.
<Phrase de synthèse.>

[Bilan du niveau <niveau>](bilan.md)
```

**Bilan du niveau** (`<niveau>/bilan.md`), récapitule ce qui a été validé,
puis renvoie au **premier palier du niveau suivant s'il existe**, sinon au
**récapitulatif** à la racine du starter :

```markdown
## Et ensuite

[Niveau intermédiaire : <premier palier>](../intermediaire/<slug>.md)
<!-- ou, tant que le niveau suivant n'existe pas : -->
[Récapitulatif de la progression](../recapitulatif.md)
```

- Un **`bilan.md` par niveau**, **dans le dossier du niveau**.
- Un seul **`recapitulatif.md`** (aide-mémoire global) **à la racine** du
  starter : il rassemble les API (réponses, requête, base, sécurité) et oriente
  vers les starters autonomes.
- Ce chaînage (palier → suivant ; dernier palier → bilan du niveau ; bilan →
  niveau suivant **ou** récapitulatif) est **verrouillé par test**
  (`tests/meta/test_starter_sequential_nav_001.py`).

---

## 4. Le code du starter (`cli/starters/data/<id>/`)

### `starter.json`

Modèle (skeleton), aligné sur `welcome` / `first-crud` :

```json
{
  "id": "<id>",
  "number": <N>,
  "name": "<Nom lisible>",
  "kind": "skeleton",
  "aliases": ["<id>", "<N>"],
  "description": "<description ; sans préfixe « Starter N »>",
  "status": "available",
  "requires_db": <true|false>,
  "supports_public": true,
  "home_route": "/<route>",
  "routes_marker": "<id>",
  "routes_snippet": "routes.py.snippet",
  "open_url": "https://localhost:8000/<route>",
  "doc_url": "https://forgemvc.com/docs/forge/starters/<starter>/<niveau>/<id>/",
  "check_paths": ["mvc/controllers/<x>_controller.py"]
}
```

- **`number` contiguë** : l'ensemble des starters est numéroté `1..N` sans
  trou (invariant vérifié par `tests/test_starter_cli.py`). Ajouter un starter
  = prendre le numéro suivant.
- `doc_url` pointe vers le slug réel : `/starters/<starter>/<niveau>/<id>/` pour
  un palier d'une progression par niveau (ex.
  `/starters/welcome-forge/debutant/welcome/`), `/starters/<id>/` pour un
  starter autonome.

### `routes.py.snippet`

Toujours encadré par les marqueurs `# forge-starter:<id>:start|:end` :

```python
# forge-starter:<id>:start
from mvc.controllers.<x>_controller import <X>Controller

with router.group("", public=True) as public:
    public.add("GET", "/<route>", <X>Controller.index, name="<x>_index")
# forge-starter:<id>:end
```

### Contrôleur (`files/mvc/controllers/<x>_controller.py`)

- Hérite de `BaseController` ; chaque action est `@staticmethod` et a la
  signature unique `(request: Request) -> Response`.
- **SQL visible** (principe 5) : requêtes nommées en constantes de module en
  haut du fichier (`SELECT_ALL = "SELECT …"`), **paramétrées** (`?`), jamais
  concaténées. Pas d'ORM, pas de génération qui masque le SQL.
- Lecture des entrées, bien distinguer :
    - `request.query("k", default=…)` → query string (`?k=`) ;
    - `request.route("k")` → segment d'URL (`/x/{k}`) ;
    - `request.form("k", default=…)` → corps d'un POST.
- **Pas de redirection** dans l'API `Response` : après une écriture
  (`POST`), on **relit la base et on ré-affiche** (cf. `first-crud`), en
  notant que dans une vraie app on ferait un *POST-Redirect-GET*.
- Validation **avant** écriture ; refus → `Response.text(..., status=422)`.

### Vue (`files/mvc/views/<x>/index.html`)

- Document HTML complet (pas de `{% extends %}` ni layout pour un palier).
- Tout formulaire `POST` embarque le champ caché `{{ csrf_token }}`.
- **Formulaire illustratif** : si le palier n'a **pas** de handler POST (ex.
  palier CSRF), le `<form>` n'a **ni `method="post"` ni `action` ni bouton
  submit**, sinon l'utilisateur déclenche un `405`. On illustre, on ne
  soumet pas.

---

## 5. Règles de fonctionnement (transverses)

- **Neutralité métier pour les fondamentaux** : un starter de découverte
  manipule une entité neutre (`message` sur la table `first_sql_messages`),
  jamais une notion métier. Les exemples métier (Contacts…) sont des starters
  **autonomes avancés**, après la progression.
- **Dossier = nom du starter, sous-dossiers = niveaux** (sans préfixe
  numérique) : `docs/starters/<starter>/<niveau>/` (ex.
  `docs/starters/welcome-forge/debutant/`). Le `recapitulatif.md` reste à la
  racine du starter.
- **Périmètre explicite** : chaque palier déclare ce qu'il ne fait pas
  (principe 8, noyau minimal, briques opt-in).
- **Sécurité par défaut** (principe 7) : CSRF sur les POST, validation serveur,
  statuts HTTP honnêtes (`422`, `404`).

---

## 6. Garde-fous attendus (tests)

Tout nouveau palier/starter doit livrer un test `tests/test_starter_<id>_001.py`
(« contrat public minimum », ~15 cas) couvrant :

- résolution du starter (`resolve("<id>")` → `id`, `number`, `kind`,
  `status`) ;
- routes déclarées par le snippet (`routes_from_snippet`) + marqueur ;
- imports du contrôleur (`Request` / `Response` / `BaseController` + API db si
  besoin) et présence des actions ;
- vue minimale (DOCTYPE, `method="post"`, `name="csrf_token"`,
  `{{ csrf_token }}`) ; absence de bruit hors périmètre (`tailwind`,
  `<script`, `{% extends %}`…) ;
- absence des fichiers hors périmètre (`.sql`, `models/`, `entities/` si non
  concerné) ;
- doc présente, **sans** motif interdit (`Starter N`, `forge starter:build`,
  `forge new mon-projet`, `cd mon-projet`, `source .venv/...`) ;
- progression : le palier est marqué « livré » au bon rang dans
  `docs/starters/index.md`.

Tests transverses à mettre à jour quand on touche la progression :
`tests/meta/test_starter_progression_001.py` (liste + numéros),
`tests/meta/test_starter_sequential_nav_001.py` (chaînage),
`tests/test_starter_cli.py` (numérotation contiguë).

**Charte règle D** : les tests testent le **code**, pas cette page. Ce document
est un guide, pas un contrat verrouillé par test.

---

## 7. Checklist : créer un nouveau palier / starter

1. **Responsabilité unique** : une seule notion nouvelle ; vérifier qu'aucune
   API d'un palier ultérieur n'est utilisée.
2. **Numéro** : prendre le `number` contigu suivant ; ajuster les tests de
   numérotation.
3. **Data** : `starter.json` + `routes.py.snippet` (marqueurs) +
   `files/mvc/...` (contrôleur SQL visible, vue HTML complète).
4. **Doc** : page `docs/starters/<starter>/<niveau>/<id>.md` suivant l'anatomie
   §2 ; chaîner depuis le palier précédent et vers le suivant ; le dernier
   palier du niveau renvoie au `bilan.md` du niveau (§3).
5. **Nav + index** : ajouter à `mkdocs.yml` et à la progression de
   `docs/starters/index.md` (« livré, ticket … »).
6. **Garde-fou** : `tests/test_starter_<id>_001.py` (§6) + mise à jour des
   tests transverses.
7. **Valider** : `python -m pytest -q`, `ruff check .`,
   `python -m compileall -q .`, `mkdocs build --strict`, `git diff --check`.
8. **Commit** : `<type>: <message> (<TICKET-CODE>)`, français, impératif,
   sans trailer.

---

## En résumé

Le starter `welcome` est la **vérité terrain** : avant d'écrire ou de modifier
un starter, ouvrez le palier le plus proche du besoin (tableau en tête de page)
et **calquez-en la forme et l'esprit**. Un palier doit pouvoir se résumer en
une phrase ; s'il en faut deux, il faut probablement deux paliers.
