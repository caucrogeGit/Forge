# Audit ultra complet — Forge 1.0.0b12

**Version auditée** : `1.0.0b12` / `1.0.0-beta.12`  
**Source auditée** : archive fournie `Forge-main (1).zip`  
**Date de l'audit** : 2026-05-30  
**Statut de l'audit** : audit source + packaging local + vérification PyPI publique ciblée

---

## 1. Verdict exécutif

Forge `1.0.0b12` est une version **solide pour une bêta publique**, surtout sur l'axe qui a motivé beta.12 : **Forge IoT opt-in + structure `optins/` + commandes de branchement explicites**.

Le cœur du framework reste cohérent avec la doctrine Forge : explicite, MVC serveur, SQL visible, générateurs prudents, séparation nette entre core et modules opt-in.

Le verdict n'est pas “stable production”. Il est :

> **GO bêta publique / terrain pédagogique / tests IoT locaux.**  
> **NO-GO stable / production publique sérieuse sans durcissement complémentaire.**

Les principaux problèmes restants ne sont pas des bugs fonctionnels lourds ; ce sont surtout des **désynchronisations de documentation, de métadonnées PyPI et de politique packaging** autour de l'arrivée de `forge-mvc-iot`.

Priorité absolue : corriger les incohérences publiques autour de `forge-mvc-iot`, car PyPI et le README publié disent encore par endroits que le package IoT est un squelette sans implémentation alors que beta.12 contient justement l'implémentation fonctionnelle.

---

## 2. Périmètre et limites de l'audit

### Inclus

- Inspection de l'archive source fournie.
- Vérification des versions dans les fichiers clés.
- Audit structurel du core, de la CLI, des starters, des schémas JSON, des opt-ins et de Forge IoT.
- Exécution de commandes locales possibles dans l'environnement sandbox.
- Construction locale de wheels ciblées (`forge-mvc`, `forge-mvc-iot`, `forge-mvc-media`).
- Vérification publique ciblée de PyPI pour `forge-mvc==1.0.0b12` et `forge-mvc-iot==1.0.0b12`.

### Non vérifiable depuis l'archive seule

L'archive ZIP ne contient pas le dossier `.git`. Donc impossible de vérifier réellement :

- `git status --short` ;
- le commit exact ;
- le tag local `v1.0.0-beta.12` ;
- `git diff --check` sur un working tree ;
- l'historique réel des commits.

Ces points doivent être vérifiés dans le dépôt Git local ou GitHub, pas dans le ZIP.

### Limites de l'environnement sandbox

Certains outils n'étaient pas installés localement :

- `ruff` absent ;
- `mkdocs` absent ;
- `build` absent ;
- `twine` absent ;
- `mariadb` Python absent ;
- `paho-mqtt` absent ;
- `pyotp` absent.

Conséquence : je n'ai pas pu refaire une validation release complète identique à celle du dépôt mainteneur. Les résultats locaux sont donc un **audit indépendant partiel**, pas une reproduction stricte de la CI/release.

---

## 3. Inventaire du dépôt fourni

| Élément | Résultat |
|---|---:|
| Fichiers totaux | 1 347 |
| Fichiers Python | 894 |
| Fichiers Markdown | 252 |
| Fichiers de tests `test_*.py` | 622 |
| Pages docs Markdown sous `docs/` | 237 |
| Packages opt-in sous `packages/` | 6 |
| Starters détectés | 15 |
| Schémas JSON racine | 7 |
| Schémas JSON packagés CLI | 7 |

Packages opt-in présents :

- `forge-mvc-rbac`
- `forge-mvc-workflow`
- `forge-mvc-stats`
- `forge-mvc-mfa`
- `forge-mvc-media`
- `forge-mvc-iot`

Starters présents :

1. `auth-mfa`
2. `carnet-contacts`
3. `communes-sejours`
4. `contact-simple`
5. `dynamic-route`
6. `first-html-view`
7. `first-sql`
8. `form-post`
9. `query-params`
10. `request-debug`
11. `server-validation`
12. `suivi-comportement-eleves`
13. `utilisateurs-auth`
14. `welcome`
15. `welcome-iot`

---

## 4. Cohérence de version

### Points verts

Les fichiers centraux sont alignés sur `1.0.0b12` / `1.0.0-beta.12` :

| Fichier | État |
|---|---|
| `pyproject.toml` | `version = "1.0.0b12"` |
| `core/__init__.py` | `__version__ = "1.0.0b12"` |
| `forge.py` | `_FORGE_VERSION = "1.0.0b12"` |
| `forge.py` | `_FORGE_DEFAULT_REF = "v1.0.0-beta.12"` |
| `package.json` | `1.0.0-beta.12` |
| `package-lock.json` | `1.0.0-beta.12` |
| `README.md` | annonce `Forge 1.0.0-beta.12` |
| `CHANGELOG.md` | section `1.0.0-beta.12` présente |
| `docs/roadmap/forge-roadmap.md` | état courant `Forge 1.0.0-beta.12` |
| `mvc/views/landing/index.html` | mention `v1.0.0-beta.12` |

Les six opt-ins portent aussi `1.0.0b12` dans leur `pyproject.toml` et leurs `__init__.py`.

### Réserve importante

Le ZIP ne permet pas de vérifier le tag Git. La roadmap annonce `Tag courant : v1.0.0-beta.12`, mais ce point doit être contrôlé dans le dépôt Git réel.

---

## 5. Vérification PyPI publique

### `forge-mvc==1.0.0b12`

PyPI annonce bien :

- `forge-mvc 1.0.0b12` ;
- publication le 29 mai 2026 ;
- statut `Development Status :: 4 - Beta` ;
- Python `>=3.12` ;
- extras exposés : `rbac`, `workflow`, `stats`, `all`.

### `forge-mvc-iot==1.0.0b12`

PyPI annonce bien :

- `forge-mvc-iot 1.0.0b12` ;
- publication le 29 mai 2026 ;
- statut `Development Status :: 3 - Alpha` ;
- Python `>=3.12` ;
- wheel et sdist présents.

### Problème PyPI critique

La page PyPI de `forge-mvc-iot` affiche encore une description de **squelette initial sans implémentation** :

- “Aucune logique fonctionnelle n'est encore implémentée” ;
- “pas de subscriber MQTT” ;
- “pas de dépendance `paho-mqtt`” ;
- “pas de stockage SQL” ;
- “pas de routes HTTP” ;
- “pas de commande CLI `forge iot:*`”.

C'est faux pour beta.12. Le package contient désormais le subscriber, le stockage, l'API HTTP, les commandes CLI et la dépendance `paho-mqtt`.

**Impact** : très mauvais signal public. Un utilisateur PyPI peut croire que l'IoT n'est pas utilisable alors que c'est précisément l'apport principal de beta.12.

---

## 6. Packaging local

### Builds locaux réussis

Builds via `pip wheel --no-deps --no-build-isolation` :

| Package | Résultat | Taille locale constatée |
|---|---:|---:|
| `forge-mvc` | OK | ~425 Ko |
| `forge-mvc-iot` | OK | ~44 Ko |
| `forge-mvc-media` | OK | ~6,3 Ko |

### Contenu de la wheel core `forge-mvc`

La wheel core contient :

- `forge.py` ;
- `core*` ;
- `forge_cli*` ;
- `integrations*` ;
- les starters packagés sous `forge_cli/starters/data/**` ;
- les schémas JSON sous `forge_cli/schemas/*.schema.json`.

Point positif : les schémas utiles à la CLI sont bien packagés dans la wheel core.

### Contenu de la wheel IoT

La wheel `forge-mvc-iot` contient :

- le package `forge_mvc_iot` ;
- la migration SQL `forge_mvc_iot/migrations/20260528120000_create_iot_events.sql` ;
- le fichier `migrations/__init__.py`.

Point positif : la migration IoT voyage bien avec le package. C'était une dette connue et elle est corrigée.

---

## 7. Problèmes packaging et métadonnées

### P1 — `pyproject.toml` core : URL de documentation obsolète

Dans `pyproject.toml`, `project.urls.Documentation` pointe encore vers :

```text
https://caucrogegit.github.io/Forge/
```

Alors que le README et le site officiel utilisent maintenant :

```text
https://forgemvc.com/docs/forge/
```

Impact : PyPI affiche encore un lien “Documentation” vers l'ancien GitHub Pages dans les détails projet. C'est incohérent avec la stratégie `forgemvc.com`.

### P2 — README core : `forge-mvc-iot` absent de la liste des modules officiels

Dans `README.md`, la section “Modules officiels opt-in” liste :

- `forge-mvc-rbac`
- `forge-mvc-workflow`
- `forge-mvc-stats`
- `forge-mvc-mfa`
- `forge-mvc-media`

Mais pas `forge-mvc-iot`.

Impact : le README publié sur PyPI ne reflète pas l'apport principal de beta.12.

### P3 — `requirements-dev.txt` n'inclut pas `forge-mvc-iot`

Le fichier installe en editable :

- MFA ;
- RBAC ;
- Workflow ;
- Stats ;
- Media.

Mais il n'installe pas :

```text
-e ./packages/forge-mvc-iot
```

Le commentaire parle encore d'opt-ins “pas encore publiés sur PyPI”. Ce commentaire est obsolète et ne tient pas compte d'IoT.

Impact : un contributeur qui suit `README.md` puis `pip install -r requirements-dev.txt` n'obtient pas forcément l'environnement complet beta.12 pour les tests IoT.

### P4 — Extras `forge-mvc[all]` ambigus

`forge-mvc[all]` inclut seulement :

- RBAC ;
- Workflow ;
- Stats.

Il exclut :

- MFA ;
- Media ;
- IoT.

L'exclusion MFA/Media est documentée dans certains passages. L'exclusion IoT n'est pas encore cadrée partout. Il faut décider explicitement :

- soit `iot` reste exclu de `[all]` car Alpha/pédagogique/dépendance MQTT ;
- soit un extra dédié `iot = ["forge-mvc-iot>=..."]` est ajouté ;
- soit les docs expliquent clairement que `forge-mvc[all]` ne signifie pas “tous les packages publiés”.

### P5 — `packages/forge-mvc-iot/pyproject.toml` : description fausse

La description dit :

```text
Squelette initial sans implémentation.
```

C'est faux pour beta.12.

### P6 — README PyPI IoT obsolète

Le README du package IoT publié décrit encore un package vide. Il doit être remplacé par un README beta.12 réel :

- installation ;
- config MQTT ;
- `iot:doctor` ;
- `iot:init` ;
- `iot:listen` ;
- `iot:simulate` ;
- API HTTP ;
- sécurité Bearer token ;
- TLS MQTT ;
- limites Alpha.

### P7 — `docs/release-policy.md` partiellement désynchronisé

La page a été partiellement mise à jour : `forge-mvc-iot` apparaît bien dans le tableau des statuts vers le début. Mais plus bas, plusieurs passages parlent encore des “cinq opt-ins officiels” et listent seulement RBAC/Workflow/Stats/MFA/Media.

Impact : la doctrine de publication opt-in est devenue confuse.

---

## 8. CLI et expérience développeur

### Points verts

`python forge.py --version` renvoie :

```text
Forge 1.0.0b12
```

`python forge.py help` expose bien les commandes ajoutées :

- `iot:doctor`
- `iot:init`
- `iot:simulate`
- `iot:listen`
- `optin:enable`
- `optin:list`

`forge update --help` est présent et répond à une vraie douleur terrain : mettre à jour une installation existante, notamment venv/pipx.

### Problème CLI mineur mais public

Le bloc final de l'aide CLI affiche encore :

```text
Documentation : https://github.com/caucrogeGit/Forge
```

Il faudrait plutôt :

```text
Documentation : https://forgemvc.com/docs/forge/
```

ou éventuellement :

```text
Documentation : https://forgemvc.com/docs/forge/
Dépôt : https://github.com/caucrogeGit/Forge
```

---

## 9. Schémas JSON et contrats d'entités

### Commandes exécutées

```bash
python forge.py schema:list
python forge.py schema:doctor
python forge.py entity:validate
python forge.py entity:validate --json
```

### Résultats

`schema:list` : OK, 6 schémas listés.

Schémas reconnus :

- `common`
- `field`
- `entity`
- `pivot`
- `relations`
- `rbac`

`schema:doctor` : OK, 6 schémas, 0 erreur.

`entity:validate` : OK.

Résultat JSON :

```json
{
  "valid": true,
  "files_checked": 2,
  "files_valid": 2,
  "errors_count": 0,
  "warnings_count": 0,
  "errors": [],
  "warnings": []
}
```

### Évaluation

Très bon point. La couche JSON Schema est stable, exploitable par la CLI, documentée et déjà utile pour une future intégration Forge Design.

C'est exactement dans la ligne Forge : JSON canonique, SQL visible, validation explicite, erreurs exploitables.

---

## 10. Forge IoT

### Fonctionnalités présentes

Le package `forge-mvc-iot` contient les briques attendues pour beta.12 :

- configuration IoT via variables d'environnement ;
- contrat MQTT ;
- subscriber MQTT via `paho-mqtt` ;
- stockage `iot_events` ;
- migration SQL packagée ;
- repository ;
- API HTTP JSON en lecture ;
- Bearer token optionnel ;
- TLS MQTT ;
- commandes CLI :
  - `forge iot:doctor`
  - `forge iot:init`
  - `forge iot:listen`
  - `forge iot:simulate`
- profils simulateur : température, humidité, présence, énergie ;
- documentation IoT pédagogique ;
- starter `welcome-iot`.

### Architecture

L'architecture IoT est bonne :

```text
capteur / simulateur
        ↓ MQTT
Mosquitto / broker MQTT
        ↓ subscription
forge iot:listen / MqttSubscriber
        ↓ validation contrat
IotEventRepository
        ↓ SQL visible
iot_events
        ↓ API HTTP Forge
Forge Design IoT / client HTTP
```

C'est la bonne séparation : Forge IoT reçoit et expose les données ; Forge Design consomme l'API HTTP et ne va pas parler directement au broker MQTT.

### Points forts

- Le core Forge ne dépend pas d'IoT.
- IoT dépend du core Forge, ce qui est normal.
- MQTT est bien traité comme protocole d'entrée, pas comme API front.
- L'API HTTP est en lecture seule.
- Le Bearer token est optionnel mais comparé avec `secrets.compare_digest`.
- Le TLS MQTT est centralisé dans un helper séparé.
- La migration reste SQL visible.
- La commande `iot:init` copie la migration sans l'appliquer automatiquement.
- Le mode local pédagogique reste simple.

### Dettes IoT

#### IOT-D1 — Documentation PyPI IoT obsolète

Dette prioritaire. Voir section packaging.

#### IOT-D2 — Commentaires internes obsolètes dans `config.py`

`IotConfig` contient encore des commentaires disant que `mqtt_tls_enabled` / `mqtt_tls_ca_file` “ne sont pas encore branchés dans les clients MQTT”, alors qu'un ticket ultérieur a branché `configure_tls`.

Ce n'est pas un bug runtime, mais c'est une dette de lisibilité.

#### IOT-D3 — API ouverte par défaut

C'est acceptable en atelier local. Ce n'est pas acceptable en production publique sérieuse.

Recommandation : en `APP_ENV=prod`, `iot:doctor` devrait émettre un `WARN` fort si :

- `FORGE_IOT_API_TOKEN` est absent ;
- MQTT est en clair ;
- aucun username/password MQTT n'est configuré ;
- TLS MQTT est désactivé alors que le broker n'est pas localhost.

#### IOT-D4 — Pas encore de stratégie device-level

L'API Bearer token est globale. Suffisant pour beta.12. Insuffisant à long terme si plusieurs établissements, classes, sites ou groupes de capteurs doivent être isolés.

Futures pistes :

- token par site ;
- token par device ;
- scopes lecture/écriture ;
- filtrage API par site autorisé ;
- rotation de clés.

#### IOT-D5 — Pas de politique de rétention/agrégation

La table `iot_events` peut grossir vite. Pour beta.12 ce n'est pas bloquant, mais il faut prévoir :

- purge ;
- archivage ;
- agrégats horaires/journaliers ;
- limites API ;
- index complémentaires selon usages réels.

---

## 11. Opt-ins côté projet utilisateur

### Points verts

La structure `optins/` est une bonne évolution : elle évite de mélanger le package distribué et le câblage local du projet.

Le modèle obtenu est clair :

```text
packages/forge-mvc-iot/      # code distribué
optins/iot/                  # branchement local du projet utilisateur
mvc/routes.py                # appel explicite register_optins(router)
```

Les commandes `optin:enable` et `optin:list` respectent la doctrine Forge :

- dry-run par défaut ;
- `--apply` explicite ;
- pas de découverte magique ;
- pas d'écrasement silencieux ;
- idempotence ;
- un seul opt-in supporté pour l'instant : `iot`.

### Point à surveiller

La commande `optin:enable` n'est pas encore généralisée aux autres opt-ins. C'est une bonne chose : ne pas généraliser trop vite.

À terme, chaque opt-in devra être audité séparément avant d'être activable :

- RBAC ;
- Media ;
- Workflow ;
- Stats ;
- MFA.

---

## 12. Starters

### Points verts

Le dépôt contient 15 starters, dont `welcome-iot`.

Le starter `welcome-iot` est important parce qu'il rend l'IoT testable sans imposer Forge Design ni une application métier complète.

Le découpage est cohérent avec la doctrine : les starters démontrent Forge, ils ne deviennent pas le cœur du framework.

### Point à vérifier dans un environnement complet

Il faut relancer régulièrement tous les starters en génération réelle :

```bash
forge starter:list
forge starter:build <starter>
python -m compileall -q .
forge project:check
```

L'audit source ne remplace pas ce smoke test terrain.

---

## 13. Sécurité

### Points solides

Forge beta.12 présente un socle de sécurité nettement supérieur à un framework pédagogique naïf :

- CSRF automatique sur méthodes unsafe selon configuration route ;
- sessions avec rotation et token CSRF ;
- cookie `__Host-` documenté dans les tickets précédents ;
- Argon2id pour les mots de passe ;
- compatibilité legacy PBKDF2 seulement pour migration ;
- MFA opt-in avec TOTP et chiffrement du secret ;
- `secrets.compare_digest` pour comparaisons de tokens sensibles ;
- upload avec garde-fous path traversal ;
- headers de sécurité ;
- Jinja2 autoescape ;
- API IoT read-only ;
- Bearer token IoT optionnel ;
- TLS MQTT supporté.

### Risques restants

#### SEC-D1 — Production publique encore encadrée

La documentation dit déjà que Forge beta.12 n'est pas une stable finale. C'est correct.

Pour une production publique sérieuse, il manque encore :

- stratégie complète reverse proxy + WSGI validée terrain ;
- stockage sessions non mémoire obligatoire ;
- rate-limit distribué ;
- politique de logs/audit plus formelle ;
- gestion des secrets production plus stricte ;
- monitoring ;
- backup/restore documenté par profil.

#### SEC-D2 — IoT ouvert par défaut

Le mode ouvert par défaut est bon pédagogiquement mais risqué en production. Il faut un warning prod fort.

#### SEC-D3 — MQTT local clair par défaut

Acceptable pour Mosquitto local en lycée/lab. À refuser ou alerter en prod.

#### SEC-D4 — Dépendances à surveiller

Le dépôt pinne certaines dépendances, mais l'audit sandbox n'a pas pu exécuter `pip-audit`. À refaire en environnement complet.

---

## 14. Documentation

### Points forts

La documentation est très riche : 237 pages Markdown dans `docs/`, dont :

- installation ;
- WSL ;
- CLI ;
- entités ;
- JSON Schema ;
- migrations ;
- sécurité ;
- production limits ;
- IoT ;
- opt-ins ;
- starters ;
- audits historiques ;
- ADR.

C'est un point fort du projet, surtout dans un contexte pédagogique.

### Problèmes documentaires actifs

#### DOC-D1 — README core incomplet sur IoT

Le README ne mentionne pas `forge-mvc-iot` dans les modules opt-in.

#### DOC-D2 — README IoT PyPI faux

Le README du package IoT publié est antérieur à l'implémentation.

#### DOC-D3 — Release policy partiellement ancienne

Des sections parlent encore de “cinq opt-ins” au lieu de six.

#### DOC-D4 — Aide CLI renvoie vers GitHub au lieu de la doc officielle

La doc officielle est maintenant `forgemvc.com/docs/forge/`.

#### DOC-D5 — Le ZIP ne contient pas l'audit post-publication beta.12 ni l'audit de clôture beta.12

Dans l'archive auditée, je trouve :

- `docs/history/audits/audit-pre-release-beta12.md`

Je ne trouve pas :

- audit post-publication beta.12 ;
- audit de clôture beta.12 ;
- page release historique beta.12 sous `docs/history/releases/`.

Si ces fichiers existent dans ton dépôt local réel après le ZIP, alors l'archive n'est pas exactement l'état final. Sinon, il faut ajouter ces documents pour fermer proprement la version.

---

## 15. Tests et validations exécutées localement

### Validations OK

```text
python -m compileall -q .
→ OK
```

```text
python forge.py --version
→ Forge 1.0.0b12
```

```text
python forge.py schema:list
→ OK — 6 schémas
```

```text
python forge.py schema:doctor
→ OK — 6 schémas, 0 erreur
```

```text
python forge.py entity:validate
→ OK — 2 fichiers valides, 0 erreur
```

```text
python forge.py entity:validate --json
→ valid: true
```

```text
python forge.py rbac:validate
→ OK — aucun contrat RBAC trouvé, RBAC optionnel
```

Tests ciblés exécutés avec succès :

```text
tests/test_iot_config_001.py
→ 44 passed
```

```text
tests/test_iot_config_tls_001.py
→ 38 passed
```

```text
tests/test_iot_http_api_auth_001.py
→ 27 passed
```

```text
tests/meta/test_pre_release_beta12_audit_001.py
→ 16 passed
```

### Validations non reproductibles dans le sandbox

`mkdocs` absent : les tests qui lancent `mkdocs build --strict` échouent mécaniquement avec `FileNotFoundError: mkdocs`.

`ruff` absent : impossible de relancer `ruff check .`.

`git diff --check` impossible : pas de `.git` dans le ZIP.

`pytest` complet non relancé : environnement incomplet et trop coûteux ici.

### Test opt-ins non concluant dans le sandbox

Un lancement ciblé de `tests/test_optins_cli_enable_iot_001.py` n'a pas terminé dans la limite d'exécution du sandbox. Je ne conclus pas à un bug Forge sur ce point, car :

- le test est annoncé vert dans la roadmap du dépôt ;
- l'environnement sandbox est incomplet ;
- l'audit source montre une commande bien structurée ;
- il faudrait reproduire dans ton vrai `.venv` Forge.

À vérifier localement :

```bash
python -m pytest tests/test_optins_cli_enable_iot_001.py -q
```

---

## 16. Qualité du code

### Points positifs

- Bonne modularité générale.
- Beaucoup de tests ciblés.
- Commandes CLI séparées par domaine.
- Forte couverture méta sur docs, packaging et contrats.
- Architecture IoT découpée proprement : config, mqtt, storage, http, cli.
- Les helpers TLS et auth évitent les duplications.
- Le mode opt-in évite d'alourdir le core.

### Points faibles

- Trop de documentation historique et active cohabite : le risque de désynchronisation augmente.
- Certains commentaires internes sont obsolètes après tickets successifs.
- Les garde-fous méta sont nombreux mais peuvent devenir bruyants si les sources de vérité ne sont pas centralisées.
- Le README public simplifié est bon pour PyPI, mais il doit rester synchronisé avec les apports majeurs de chaque beta.
- La politique “all extras” n'est pas assez claire depuis l'ajout d'IoT.

---

## 17. Trailing whitespace / hygiène fichiers

J'ai détecté 22 fichiers avec espaces en fin de ligne sur les types textuels inspectés.

La majorité est dans `docs/history/`, donc probablement historique et peu grave. Mais comme Forge impose régulièrement `git diff --check`, il faut éviter que ces fichiers soient retouchés sans nettoyage ou que la vérification soit relancée sur un patch les incluant.

Exemples :

- `docs/adr/010-auth-session-canonical-api.md`
- `docs/history/charte-v1.md`
- `docs/testing/field-test-charter.md`
- plusieurs audits historiques sous `docs/history/audits/`

Priorité basse, sauf si ces fichiers sont modifiés.

---

## 18. Cohérence avec la philosophie Forge

### Respect très bon

Forge beta.12 respecte globalement les principes :

- core générique ;
- opt-ins séparés ;
- SQL visible ;
- migrations explicites ;
- pas d'ORM imposé ;
- pas de magie de discovery ;
- dry-run par défaut sur `optin:enable` ;
- documentation des limites ;
- tests nombreux.

### Risque de dérive maîtrisé mais réel

L'IoT peut devenir gros. La bonne décision a été de le garder opt-in.

Il faut maintenir cette limite :

- pas d'IoT dans le core ;
- pas de dépendance MQTT dans `forge-mvc` ;
- pas de Forge Design obligatoire ;
- pas de dashboard intégré prématuré ;
- pas de stockage magique ou de règles métier lycée codées dans le framework.

---

## 19. Matrice des constats

| ID | Gravité | Domaine | Constat | Action recommandée |
|---|---|---|---|---|
| B12-AUDIT-01 | Haute | PyPI IoT | README/description IoT publié faux : dit “squelette sans implémentation” | Corriger `packages/forge-mvc-iot/README.md` + `pyproject.description`, republier en prochaine version |
| B12-AUDIT-02 | Haute | README core | `forge-mvc-iot` absent des modules opt-in | Ajouter IoT à la table modules + section docs |
| B12-AUDIT-03 | Moyenne | Packaging | `project.urls.Documentation` pointe vers GitHub Pages | Remplacer par `https://forgemvc.com/docs/forge/` |
| B12-AUDIT-04 | Moyenne | CLI | Aide CLI finale pointe vers GitHub | Pointer vers doc officielle + dépôt séparé |
| B12-AUDIT-05 | Moyenne | Dev env | `requirements-dev.txt` n'installe pas `forge-mvc-iot` | Ajouter `-e ./packages/forge-mvc-iot` ou documenter l'exclusion |
| B12-AUDIT-06 | Moyenne | Release policy | “cinq opt-ins” encore présent | Passer à six opt-ins et clarifier IoT Alpha |
| B12-AUDIT-07 | Moyenne | Extras | `forge-mvc[all]` ambigu | Clarifier ou ajouter extra `iot` |
| B12-AUDIT-08 | Basse | Code comments | Commentaires TLS IoT obsolètes | Nettoyer `config.py` |
| B12-AUDIT-09 | Basse | Docs release | Pas de post-publish/closing audit beta.12 dans le ZIP | Ajouter ou vérifier que l'archive est à jour |
| B12-AUDIT-10 | Basse | Hygiene | Trailing whitespace historiques | Nettoyage opportuniste si fichiers retouchés |
| B12-AUDIT-11 | Moyenne | Sécurité IoT | API ouverte par défaut OK local, risquée prod | Ajouter warnings prod dans `iot:doctor` |
| B12-AUDIT-12 | Moyenne | Production | Pas encore stable production publique | Garder documentation “production encadrée” |

---

## 20. Tickets recommandés

### 1. `BETA12-PUBLIC-METADATA-SYNC-001`

Objectif : synchroniser toutes les métadonnées publiques beta.12.

Périmètre :

- `pyproject.toml` core URL documentation ;
- `forge_cli/help.py` URL documentation ;
- `README.md` core : ajouter `forge-mvc-iot` ;
- `docs/release-policy.md` : cinq → six opt-ins ;
- `requirements-dev.txt` : ajouter `forge-mvc-iot` ou documenter l'exclusion ;
- tests méta associés.

Validation :

```bash
python -m pytest tests/meta -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

### 2. `IOT-PYPI-README-REFRESH-001`

Objectif : remplacer le README PyPI IoT obsolète.

Périmètre :

- `packages/forge-mvc-iot/README.md` ;
- `packages/forge-mvc-iot/pyproject.toml` description ;
- mention claire du statut Alpha ;
- installation ;
- commandes ;
- API ;
- sécurité ;
- limites.

Validation :

```bash
python -m pip wheel packages/forge-mvc-iot --no-deps --no-build-isolation -w /tmp/forge-wheel-check
python -m pytest tests/test_iot_* tests/meta/test_iot_* -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

### 3. `IOT-PROD-WARNINGS-001`

Objectif : ajouter des warnings forts pour usage IoT dangereux en production.

Checks :

- `APP_ENV=prod` + API token absent → WARN ;
- MQTT host non-local + TLS désactivé → WARN ;
- MQTT auth absente + host non-local → WARN ;
- doc production IoT mise à jour.

### 4. `BETA12-POST-PUBLISH-AUDIT-DOCS-001`

Objectif : si absent du dépôt réel, ajouter un audit post-publication beta.12.

Contenu :

- PyPI core OK ;
- PyPI IoT OK ;
- site officiel OK ;
- README PyPI incohérences listées ;
- limites restantes ;
- prochain ticket beta.13.

### 5. `OPTINS-CLI-LIST-JSON-001`

Objectif : ajouter une sortie machine à `forge optin:list`.

Intérêt : utile pour Forge Design et pour scripts CI.

### 6. `IOT-RETENTION-POLICY-AUDIT-001`

Objectif : auditer la croissance de `iot_events`.

Sortie attendue : politique de rétention, purge, index et agrégats éventuels.

---

## 21. Conclusion

Forge `1.0.0b12` marque une étape importante : le framework passe d'un MVC pédagogique généraliste à un socle capable de recevoir un module IoT réel, sans casser la séparation core/opt-in.

L'architecture est saine. La démarche est cohérente. La version est publiable et déjà publiée. Le principal danger n'est pas technique : c'est la **désynchronisation publique**. Le code dit “Forge IoT existe”, mais certains README/métadonnées disent encore “Forge IoT est un squelette vide”.

À corriger rapidement, car c'est le premier contact d'un utilisateur PyPI avec beta.12.

Verdict final :

```text
Forge 1.0.0b12 : bonne bêta publique.
Priorité : synchronisation documentation / PyPI / release policy autour de IoT.
Ne pas ouvrir beta.13 fonctionnelle avant d'avoir nettoyé ces incohérences publiques.
```
