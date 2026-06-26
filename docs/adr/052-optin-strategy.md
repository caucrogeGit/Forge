# ADR-052 : Stratégie et critères des opt-ins Forge

## Statut

Proposé, Forge 1.0.0-beta.17 (ticket `ADR-OPTIN-STRATEGY-001`).
Décision de périmètre et d'ordonnancement des opt-ins ; relève du mainteneur.

---

## Date

2026-06-26

---

## Contexte

Une liste de candidats opt-ins a été proposée pour la suite de Forge : `cache`,
`jobs`, `events`, `search`, `notifications`, `admin`, `qrcode`, `import-export`,
`audit`, `settings`, `webhooks`, `i18n`, `realtime`, `api`.

Aucun cadre documenté ne dit lesquels entrent dans la trajectoire, dans quel
ordre, ni lesquels sont exclus. En l'absence de critères, chaque idée d'opt-in
se discute au cas par cas, ce qui contredit le principe 8 (noyau minimal,
briques opt-in raisonnées) et le principe 11 (une seule façon officielle).

Deux réalités structurelles contraignent la réponse :

1. Le runtime de Forge est **synchrone (WSGI, Gunicorn)** : pas de boucle async,
   pas de worker, pas de broker. Voir le guide de déploiement WSGI.
2. La charte interdit la **magie cachée** (principe 3), impose **une seule façon
   officielle** (principe 11), le **SQL visible** (principe 5), un **noyau
   minimal** (principe 8) et un **contrat de complétude** des API publiques
   (principe 10).

Plusieurs candidats proposés **doublonnent des fonctionnalités déjà livrées** :
l'internationalisation existe (`forge-mvc-i18n`, ADR-027) ; l'export CSV, la
recherche `LIKE` et la pagination sont déjà produits par le CRUD généré
(`_CSV_COLS`, `find_*_for_export`, `_SEARCH_COLS`) ; `forge-mvc-qrcode` est livré
(ADR-050) ; `forge-mvc-admin` est amorcé (scaffold, `forge-admin-roadmap.md`) ;
`forge-mvc-mail` et `forge-mvc-stats` sont livrés.

---

## Décision

### Deux filtres d'admission (un opt-in doit passer les DEUX)

**Filtre A, runtime.** L'opt-in fonctionne dans le modèle WSGI synchrone, ou
fournit son propre mécanisme hors requête qui reste de style Forge : adossé à
MariaDB, piloté par une commande explicite, sans broker ni dépendance lourde.
Tout ce qui exige ASGI ou des connexions persistantes est **hors trajectoire
1.x**.

**Filtre B, charte.** Câblage explicite (pas d'auto-découverte ni de décorateur
magique), une seule façon officielle, SQL visible, périmètre borné, contrat de
complétude. Un opt-in qui réintroduit du couplage implicite est refusé.

### Classification des candidats

**1. Déjà couvert (ne pas refaire).**
`i18n` ; export CSV, recherche `LIKE`, pagination (dans le CRUD généré) ;
`qrcode` ; `mail` ; `stats`. Seuls deltas légitimes restants : l'**import CSV**
(le CRUD ne fait que l'export) et la **recherche plein texte** MariaDB
(`FULLTEXT`), distincte de la recherche `LIKE` déjà fournie.

**2. À livrer en priorité (adossé MariaDB, explicite, sans nouveau runtime).**
Ces opt-ins ne demandent aucun concept d'exécution nouveau et servent
directement une application de gestion :

- **Finir `forge-mvc-admin`** : déjà amorcé, multiplicateur de valeur (back-office
  CRUD lisible). Garder le style « généré mais lisible », ne pas copier EasyAdmin.
- **`forge-mvc-import`** : import CSV vers entités, validation explicite, rapport
  d'erreurs. Comble le vrai manque (l'export existe déjà).
- **`forge-mvc-settings`** : table de paramètres applicatifs (nom d'établissement,
  durée d'une session, mode maintenance), pour éviter de tout mettre dans `.env`.
- **`forge-mvc-audit`** : table d'audit applicatif standard plus helper, **borné**
  (pas un SIEM de cybersécurité). Cohérent avec ADR-008 : Forge fournit la table
  et le helper, la décision de tracer reste applicative.

**3. À construire quand un besoin réel le tire (pas spéculativement).**

- **`forge-mvc-jobs`** : pierre angulaire conditionnelle. Forme imposée : **file
  MariaDB plus commande worker explicite** (`forge jobs:work`), jamais
  Celery/Redis. À construire le jour où un opt-in fait du travail lourd en
  requête (transcodage vidéo, import massif, envoi en nombre), pas avant.
- **`forge-mvc-notifications`** : dépend de `jobs` (et éventuellement d'un
  mécanisme d'événements explicite). À faire après `jobs`.
- **`forge-mvc-cache`** : adossé MariaDB ou fichier, clés et TTL **explicites**,
  seulement quand un chemin chaud est mesuré. L'invalidation implicite est un
  risque vis-à-vis du principe 3, et le piège multi-worker (compteurs en mémoire
  non partagés) s'applique comme pour le rate-limit.

**4. Hors trajectoire 1.x.**

- **`realtime` (WebSocket/SSE)** : exige un modèle d'exécution ASGI, incompatible
  avec le runtime WSGI synchrone actuel. Ce n'est pas « trop tôt », c'est un
  autre modèle.
- **`events` sous forme de bus auto-découvert** : le `@events.on` à découverte
  implicite viole les principes 3 et 11. Si un besoin réel apparaît, seule une
  forme **explicite et minimale** (registre câblé dans un fichier visible, `emit`
  manuel) serait recevable ; le couplage par décorateur est refusé.
- **`api` JSON dédié** : delta faible (Forge renvoie déjà du JSON via `Response`),
  risque de dérive « devenir FastAPI ». Au mieux un mince helper, pas un opt-in
  prioritaire.
- **`webhooks` sortants** : dépendent de `jobs` (réessais, hors requête). Après
  `jobs`.

### Ordre recommandé (application pédagogique de rentrée)

`admin` (finir) puis `import` puis `settings` puis `audit` puis (`jobs` si un
workload réel le réclame) puis `notifications`.

---

## Conséquences

- Tout nouvel opt-in passe les deux filtres avant d'entrer dans la roadmap ; un
  refus est documenté par le filtre qui n'est pas franchi.
- Les redondances avec le CRUD généré (export, recherche `LIKE`, pagination) sont
  explicitement écartées ; on ne reconstruit pas l'existant.
- `jobs` devient une pierre angulaire **conditionnelle**, à bâtir adossée à
  MariaDB et pilotée par une commande, le jour où un besoin réel la tire.
- `events` (bus auto-découvert) et `realtime` sortent de la trajectoire 1.x ;
  leur réintroduction éventuelle passera par un nouvel ADR.

---

## Alternatives écartées

- **Prioriser « cache plus jobs plus events » en premier (proposition initiale).**
  Ce sont les trois candidats les plus risqués vis-à-vis de la charte et du
  runtime : `events` viole l'anti-magie, `cache` est une optimisation prématurée
  pour les usages actuels, `jobs` est le plus gros chantier sans besoin tiré.
  Les livrer d'abord, c'est investir dans l'infrastructure avant la valeur métier.
- **Livrer la liste proposée dans son ordre, sans filtre.** Ignore le runtime
  synchrone (laisse entrer `realtime`) et double-compte l'existant (`i18n`,
  export, recherche `LIKE`).

---

## Référence

- Charte : `CHARTE_DOC.md` (principes 3, 5, 8, 10, 11).
- [ADR-004](004-core-perimeter.md) : périmètre du core minimal.
- [ADR-008](008-auth-audit-architecture.md) : audit auth, persistance applicative.
- [ADR-027](027-i18n-extraction.md) : extraction de l'i18n.
- [ADR-050](050-qrcode-optin.md) : opt-in QR Code.
- Guide de déploiement WSGI (rate-limit en mémoire par worker, runtime synchrone).
