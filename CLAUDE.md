# CLAUDE.md — Briefing pour agents IA travaillant sur Forge

Ce fichier briefe les agents IA (Claude Code, etc.) sur les conventions et
l'architecture de Forge. Il est conçu pour rester valide sur la durée d'une
version majeure.

**Mise à jour** : ce fichier est refondu à chaque tag majeur (3.0, 4.0…).
Pour les informations volatiles (version exacte, tickets en cours, compteur
de tests), voir les sources canoniques — section 8.

---

## 1. Identité du projet

Forge est un framework web Python **explicite, pédagogique, testable et durable**.
Il conserve un runtime Python volontairement limité : MariaDB, python-dotenv,
Jinja2, Argon2, jsonschema (PyOTP côté opt-in MFA ; Pillow côté opt-in images —
ADR-018).

**Type** : framework MVC Python, distribué en plusieurs paquets PyPI :

- `forge-mvc` (core)
- `forge-mvc-mfa` (authentification multi-facteur)
- `forge-mvc-rbac` (contrôle d'accès basé sur les rôles)
- `forge-mvc-workflow` (transitions de statut)
- `forge-mvc-stats` (agrégats statistiques)
- `forge-mvc-files` (upload générique : écriture sécurisée, storage, service de fichiers — extrait du core, ADR-019)
- `forge-mvc-images` (traitement et gestion applicative des images, Pillow ; ADR-018 ; porte un shim de compatibilité réexportant l'ancien `forge-mvc-media`, supprimé)
- `forge-mvc-iot` (réception/exposition de données IoT via MQTT)
- `forge-mvc-video` (upload, transcodage MP4 et lecture vidéo en streaming)
- `forge-mvc-audio` (upload, sondage, transcodage MP3 et lecture audio en streaming, sans état)
- `forge-mvc-mail` (envoi d'emails, transports interchangeables ; extrait du core, ADR-022)
- `forge-mvc-pivot` (tables pivot enrichies `many_to_many` ; extrait du core, ADR-021)
- `forge-mvc-i18n` (internationalisation par catalogues JSON, helper `trans()` ; extrait du core, ADR-027)

**Python** : 3.12+ minimum (ADR-006).

**Statut** : version courante dans `pyproject.toml`. Trajectoire publique
1.0, actuellement en **bêta publique** (`1.0.0-beta.x`) ; consolidation
bêta en cours. Voir `CHANGELOG.md` et `docs/roadmap/` pour l'avancement
détaillé.

---

## 2. Charte philosophique v2 — 11 principes

La charte v2 est le **document non négociable** de Forge. Lire `CHARTE_DOC.md`
intégralement avant toute proposition d'évolution. Les ADR s'y rattachent tous.

Les 11 principes (résumé — la formulation canonique est dans `CHARTE_DOC.md`) :

1. **Séparer framework et application métier**
2. **Petits tickets, une responsabilité**
3. **Refuser la magie cachée**
4. **Préserver le code utilisateur**
5. **Garder SQL visible**
6. **Tester avant d'élargir**
7. **Sécuriser par défaut**
8. **Noyau minimal, briques opt-in**
9. **Pas d'écriture invisible dans le code utilisateur**
10. **Une API publique est un contrat de complétude**
11. **Une seule façon officielle de faire chaque chose**

**Règles d'évolution A–D** (résumé) :

- A — Retirer la cause, pas le symptôme
- B — Révéler avant de corriger
- C — Toute rupture d'API publique passe par une release majeure
- D — Les tests testent le code, pas la documentation

## 2.1 Directive de style francophone pour la documentation

Claude doit appliquer systématiquement un style documentaire français
sur toute documentation Forge.

- Langue : rédiger l'intégralité du texte en français, sauf citations,
noms de commandes, symboles de code ou termes techniques indispensables.
- Formulations : employer des tournures françaises claires et directes,
  éviter les anglicismes inutiles, privilégier le vocabulaire français
  adapté au contexte technique.
- Caractères : utiliser la typographie française correcte ; éviter le
  tiret cadratin (U+2014) dans la documentation, ainsi que les formules de style
  typographiquement anglo-saxonnes. Préférer la virgule, le point-virgule,
  les deux-points, ou le trait d'union court si nécessaire.
- Ponctuation : respecter les espaces insécables avant `;`, `:`, `?`, `!`
  et les guillemets français `« »` lorsque cela est pertinent.
- Portée : cette directive concerne tous les fichiers de documentation,
  les guides, les pages MkDocs, les README, les tickets de documentation,
  et toutes les propositions d'édition produites par Claude.

Claude doit toujours relire la documentation produite pour vérifier que
la langue, les formulations et les caractères sont conformes à ce style
francophone.

**Note** : cette règle est contraignante pour les corrections de contenu
et pour la génération de nouveaux documents, pas uniquement pour les
exemples de code ou les notes internes.

**Note pré-1.0** (convention pratique, pas dans la charte formelle) : avant le
tag 1.0.0 stable (phase bêta en cours), les ruptures internes (suppressions,
renommages) se font sans aliases dépréciés ni guide de migration formel — pas
d'utilisateurs externes ni de code applicatif externe à protéger.

---

## 3. Architecture

**Core minimal** (`core/`) :

- HTTP (`Request`, `Response`, middlewares)
- Routing et application principale
- Configuration et variables d'environnement
- Templating (Jinja2)
- Accès base de données minimal (pas d'ORM)
- Sessions et cookies
- Sécurité de base (CSRF, headers, hachage)
- CLI de génération (`forge_cli/`) — outils non destructifs

**Modules officiels** (installables séparément via pip, dans `packages/`) :

- `forge-mvc-mfa` — facteurs TOTP, codes de récupération, challenge, revalidation
- `forge-mvc-rbac` — permissions déclaratives, contrôle par rôle
- `forge-mvc-workflow` — états, transitions, historique
- `forge-mvc-stats` — agrégats, compteurs, fenêtres temporelles
- `forge-mvc-files` — upload générique extrait du core (ADR-019) : `save_upload`, storage anti-traversal, `serve_media_file` (HTTP Range), rate-limit. La **validation** pure (extension/MIME/taille) reste dans le core (`core/forms`)
- `forge-mvc-images` — traitement d'image (Pillow, extrait du core) + couche applicative médias (repository, galerie, couverture) ; dépend de `forge-mvc-files` ; ADR-018
- `forge-mvc-iot` — subscriber MQTT, stockage `iot_events`, API HTTP JSON, CLI `iot:*`
- `forge-mvc-video` — upload, transcodage MP4 (H.264/AAC), lecture HTTP Range, CLI `video:*`
- `forge-mvc-audio` — upload, sondage (`ffprobe`), transcodage MP3 (`ffmpeg`), lecture HTTP Range, CLI `audio:doctor` ; sans état
- `forge-mvc-mail` : envoi d'emails, transports interchangeables (console, SMTP, log), templates Jinja, CLI `mail:*` ; extrait du core (ADR-022)
- `forge-mvc-pivot` : tables pivot enrichies (`many_to_many` avec attributs), `make:pivot-crud` ; extrait du core (ADR-021)
- `forge-mvc-i18n` : internationalisation par catalogues JSON, locale et fallback, helper `trans()`, repli no-op du noyau ; extrait du core (ADR-027)

**Hors scope Forge** (à charge de l'application) :

- Persistance des audits auth (Forge fournit le logging Python — voir ADR-008)
- OIDC / OAuth (retiré du dépôt — voir ADR-004)
- Multi-tenant, paiement, SPA frontend
- ORM complet, marketplace plugins

---

## 4. ADR — Décisions architecturales

Chaque ADR est dans `docs/adr/` et a **force décisionnelle**. À lire avant toute
proposition qui le concerne. Un nouvel ADR est requis pour toute décision
structurante.

| Numéro | Fichier | Sujet résumé |
|---|---|---|
| ADR-001 | `001-auth-strategy.md` | Stratégie d'authentification Forge |
| ADR-002 | `002-session-strategy.md` | Stockage de session |
| ADR-003 | `003-language-convention.md` | API publique en anglais |
| ADR-004 | `004-core-perimeter.md` | Périmètre du core minimal strict |
| ADR-005 | `005-packaging.md` | Packaging hybride monorepo + multi-distributions PyPI |
| ADR-006 | `006-python-version.md` | Python 3.12+ minimum |
| ADR-007 | `007-charter-v2-adoption.md` | Adoption formelle de la charte v2 |
| ADR-008 | `008-auth-audit-architecture.md` | Audit auth : logging fourni, persistance applicative |
| ADR-009 | `009-stability-policy-terrain.md` | Politique de stabilité : audits, bêta consolidée, tests terrain |
| ADR-010 | `010-auth-session-canonical-api.md` | API canonique auth/session |
| ADR-011 | `011-auth-audit-vocab-perimeter.md` | Périmètre du vocabulaire d'audit auth |
| ADR-012 | `012-legacy-format-deprecation-policy.md` | Politique de dépréciation du format legacy |
| ADR-013 | `013-nullable-required-contract-policy.md` | Politique nullable / required des contrats |
| ADR-014 | `014-rbac-contract-location.md` | Emplacement du contrat RBAC |
| ADR-015 | `015-dev-tls-handshake-per-thread.md` | Handshake TLS par thread (dev-server) |
| ADR-016 | `016-opt-in-unification.md` | Unification du modèle opt-in (cycle install/enable, 4 verbes) |
| ADR-017 | `017-slug-type.md` | Type `slug` et module URL-slug canonique |
| ADR-018 | `018-image-module-extraction.md` | Extraction du traitement d'image : `forge-mvc-images` |
| ADR-019 | `019-upload-extraction.md` | Extraction de l'upload générique : `forge-mvc-files` |
| ADR-020 | `020-files-media-storage-primitives.md` | Périmètre de `forge-mvc-files` (primitives de stockage) |
| ADR-021 | `021-pivot-extraction.md` | Extraction de pivot advanced : `forge-mvc-pivot` |
| ADR-022 | `022-mail-extraction.md` | Extraction de l'email : `forge-mvc-mail` |
| ADR-023 | `023-starter-build-canonical.md` | `starter:build` canonique ; `forge new` produit un projet nu |
| ADR-024 | `024-skeleton-bootstrap.md` | Bootstrap par squelette dédié, dépendance core via pip |
| ADR-025 | `025-welcome-forge-continuous-tutorial.md` | welcome-forge : tutoriel continu manuel |
| ADR-026 | `026-request-param-naming.md` | Accesseurs de `Request` nommés par leur source (`query`, `route`) |
| ADR-027 | `027-i18n-extraction.md` | Extraction de l'i18n : `forge-mvc-i18n`, repli no-op du noyau |
| ADR-028 | `028-welcome-forge-tutorial-per-level.md` | welcome-forge : un mini-projet par niveau |
| ADR-029 | `029-route-naming-convention.md` | Convention de route : chemin `/contrôleur/méthode`, nom `contrôleur-méthode` |
| ADR-030 | `030-explicit-route-injection.md` | Injection de routes par commande explicite et portée de la règle 4.3 (proposé) |

Pour créer un nouvel ADR : `docs/adr/<numéro>-<sujet>.md`, suivre le format existant.

---

## 5. Convention de tickets

### Étape 0 — Vérifier le dépôt canonique

Avant tout ticket Forge, vérifier impérativement que le dépôt courant
est bien le dépôt canonique :

- chemin = `/home/roger/Projets/Forge` ;
- branche = `main` ou une branche ticket issue de `main` ;
- remote `origin` = `git@github.com:caucrogeGit/Forge.git` ;
- working tree propre.

Commandes de contrôle :

```bash
pwd
git status --short
git branch --show-current
git remote -v
git log -3 --oneline
```

Si **l'un** de ces critères n'est pas rempli, **arrêter immédiatement**.
Ne pas continuer un ticket Forge depuis un projet généré
(`forge-test-*`, dossier `mvc/` isolé), un clone temporaire ou une
branche `master`. Procédure officielle de portage par patchs et liste
complète des signaux d'un mauvais dépôt :
[`docs/contributing/canonical-repo.md`](docs/contributing/canonical-repo.md).

**Format** : `DOMAINE-SUJET-NUMÉRO` (ex : `MFA-EXTRACT-001`, `LANG-MIGRATION-001`).

**Un ticket = une responsabilité.** Chaque spec doit indiquer :

- Ce qu'il fait / ce qu'il ne fait pas
- Les fichiers concernés
- La stratégie d'implémentation étape par étape
- Les validations attendues
- Les limites restantes
- La charte appliquée

**Workflow attendu** :

1. Spec rédigée (en dialogue dans le chat web)
2. Exécution par Claude Code
3. Rapport : commit hash, fichiers créés/modifiés, tests qui passent,
   écarts vs spec, limites découvertes
4. Validation, puis ticket suivant

**Format de commit** :

```
<type>: <message court> (<TICKET-CODE>)
```

Types : `feat`, `refactor`, `fix`, `docs`, `test`. Message en français,
impératif, sans majuscule ni point final.

---

## 6. Convention de tests

- pytest, tous les tests dans `tests/`
- `tests/test_<TICKET>_001.py` pour les garde-fous liés à un ticket structurant
- Les tests d'absence (`assert not Path("x.py").exists()`, `assert X not in content`)
  sont la norme après suppressions et renommages
- Tests paramétrés via `@pytest.mark.parametrize` pour les contrats à plusieurs valeurs
- Pour inspecter le code source d'un module : `Path(module.__file__).read_text()`
  plutôt qu'un chemin codé en dur

**Validations attendues avant chaque commit** :

```bash
python -m pytest -x -q          # complet, 0 régression
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

---

## 7. Modes d'action de Forge (principe 9)

Forge suit trois modes :

- **Forge génère** — crée des fichiers nouveaux (write-if-new)
- **Forge affiche** — montre du code à copier-coller
- **Forge lit** — lit des fichiers existants pour analyse

Forge **ne réécrit jamais silencieusement** un fichier applicatif.
Si un ticket pourrait modifier `mvc/routes.py`, `mvc/controllers/*.py` ou tout
fichier sous contrôle utilisateur — **arrêter et proposer une alternative**.

---

## 8. Sources canoniques pour les informations volatiles

Ne pas se fier à ce fichier pour les informations qui changent entre tickets.
Consulter directement :

| Information | Source canonique |
|---|---|
| Version courante | `pyproject.toml` → `[project].version` |
| Compteur de tests | `python -m pytest --collect-only -q \| tail -3` |
| Tickets livrés | `CHANGELOG.md` + `git log --oneline` |
| Tickets en cours / à venir | `docs/roadmap/forge-roadmap.md` |
| Modules officiels disponibles | `packages/` (un sous-dossier = un module) |
| API publique d'un module | `<module>/__init__.py` |
| Principes et règles détaillés | `CHARTE_DOC.md` |
| Décisions d'architecture | `docs/adr/` |

---

## 9. Patterns émergents (Forge 3.x consolidation)

Les conventions opérationnelles de Forge sont consolidées dans
`docs/contributing/conventions.md` (18 patterns en 4 sections) :

- **A. Audit avant action** : audit 5 racines, `.gitignore`, historique git,
  production interne, doc référencée par les tests
- **B. Tests** : helpers locaux pour formats legacy, `module.__file__`,
  `PROJECT_ROOT` partagé, classification sémantique des `_001`,
  généralisation plutôt que suppression, cohérence des noms de tests
- **C. Code** : lock + delegate, `register_<module>_routes`, note
  « Module extrait », garde-fous documentaires, word boundaries
- **D. Documentation** : MkDocs strict + liens hors `docs/`,
  `docs/history/` comme mémoire brute, section « Historique » dans la nav

Note sur `packages/` : 12 sous-dossiers maintenus (`forge-mvc-mfa`,
`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-files`,
`forge-mvc-images`, `forge-mvc-iot`, `forge-mvc-video`, `forge-mvc-audio`,
`forge-mvc-mail` (ADR-022), `forge-mvc-pivot` (ADR-021), `forge-mvc-i18n` (ADR-027)),
chacun avec son propre `pyproject.toml`. Le paquet `forge-mvc-media` a été
supprimé ; son shim de compatibilité est réexporté par `forge-mvc-images`
(ADR-018). Le `pyproject.toml` racine est la source de vérité pour `forge-mvc`
(résolu en T2 + T2b, consolidation bêta 1.0).

---

## 10. Engagement de mise à jour

Ce fichier a été resynchronisé pour la **bêta publique 1.0** (`1.0.0-beta.x`)
— ticket `GOV-CLAUDE-MD-1.0-RESYNC-001` (alignement après le renumérotage de
la trajectoire publique vers 1.0).

Il est conçu pour rester valide sans modification pendant toute la série 1.x.
Les informations volatiles ne sont pas ici — voir section 8.

**Prochaine refonte prévue** : tag majeur 2.0 (ou refonte intermédiaire si
un changement architectural important le justifie).
**Dernière refonte** : 2026-05 (resync bêta 1.0, `GOV-CLAUDE-MD-1.0-RESYNC-001`)

---

## 11. Configuration Claude Code (`.claude/settings.json`)

Le fichier `.claude/settings.json` est commité dans le dépôt et définit la
politique de permissions partagée pour tous les contributeurs.

**Commandes pré-autorisées** (sans prompt) :

```
pytest / python -m pytest    — suite de tests
python -m compileall         — vérification syntaxe
ruff check / ruff format     — linting et formatage
mkdocs build / mkdocs serve  — documentation
forge                        — CLI Forge
git status / diff / log / show / branch / add
```

**Commandes bloquées** (deny explicite) :

```
git push --force / git push -f
git reset --hard
git tag -d / git push --delete
rm -rf / rm -fr
```

Les overrides personnels vont dans `.claude/settings.local.json` (non commité,
ignoré par `.gitignore`). Ne pas modifier `settings.json` pour des préférences
individuelles.

---

## 12. Fichiers protégés — hook PreToolUse

Le script `.claude/hooks/forge-write-if-new.sh` est branché sur `Edit`,
`Write` et `MultiEdit`. Il applique automatiquement les règles §4 et §9 de la
charte avant chaque écriture.

**Règles dans l'ordre (premier match gagne) :**

| # | Condition | Résultat |
|---|---|---|
| 1 | Le fichier n'existe pas encore | Autorisé (write-if-new) |
| 2 | Le nom se termine par `_base.py` | Autorisé (régénérable) |
| 3 | Fichier structurant (liste ci-dessous) | **Bloqué §9** |
| 4 | Chemin sous `starters/**` ou `examples/**`, fichier existant | **Bloqué §4** |
| 5 | Tout le reste | Autorisé par défaut |

**Fichiers toujours bloqués (règle 3) :**

```
charte_philosophique_forge_v2.md
CLAUDE.md
.claude/settings.json
.claude/hooks/**
pyproject.toml
.env  /  .env.*  /  **/.env  /  **/.env.*
env/*    — fichiers d'environnement Forge (env/dev, env/test, env/prod,
           env/*.local) ; protégés même quand le fichier n'existe pas
           encore (le check passe avant la règle 1 « write-if-new »)
```

**Zone code-utilisateur bloquée (règle 4) :**

```
starters/**     — starters Forge distribués
examples/**     — exemples du framework
```

### Cas particulier : `CHANGELOG.md`

`CHANGELOG.md` est **modifiable** par les agents lorsqu'un ticket le demande
explicitement (ticket `AGENTS-CHANGELOG-WRITE-ALLOW-001`).

Raison : le changelog fait partie du flux normal de release, d'audit et de
clôture Forge. Il ne doit plus être traité comme un fichier structurel
toujours bloqué.

Les agents doivent toutefois limiter leurs modifications à la section
concernée par le ticket en cours, sans toucher aux entrées historiques
d'autres tickets ou d'autres versions.

Si Claude Code est bloqué sur un fichier qu'il devrait pouvoir modifier,
vérifier que le chemin ne matche pas l'une de ces règles et ajuster le ticket
en conséquence.

### Validations : pas d’attente passive

Les agents ne doivent pas lancer les validations Forge en arrière-plan.

Interdit :
- lancer `pytest`, `mkdocs`, `ruff`, `compileall` en tâche de fond ;
- répondre “j’attends la fin” ;
- masquer une validation finale avec `tail`, `head` ou une sortie tronquée ;
- considérer une commande réussie sans exit code ou résumé complet.

Attendu :
- lancer les validations en foreground ;
- afficher le résultat utile complet ;
- donner le code retour si disponible ;
- en cas d’échec, afficher l’erreur complète ;
- si une commande est trop longue pour l’outil, demander à l’utilisateur de la lancer et de coller le résultat.

### Gestion des phrases
- Phrases : rédiger une phrase par ligne dans la source Markdown. Après le
  point final d'une phrase, la phrase suivante commence sur une nouvelle ligne.
  L'extension nl2br est activée : chaque retour de ligne simple devient un saut
  de ligne au rendu, donc une phrase par ligne s'affiche ligne à ligne.
