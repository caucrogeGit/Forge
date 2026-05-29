# Clôture Forge 1.0.0-beta.12

> Ticket : `BETA12-CLOSING-SUMMARY-001`. Document de **clôture** de toute la
> séquence `1.0.0-beta.12` — **documentaire uniquement, aucun code
> fonctionnel**. Repères : release `ac7f07b`, tag `v1.0.0-beta.12`, audit
> post-publication `77266b5`, landing canonique `c69fbe8`, site officiel
> `10caaff` puis sync landing `0283e91`.

## Verdict

**Forge 1.0.0-beta.12 est publiée, vérifiée et visible publiquement.**

**GO — beta.12 clôturée.**

## Résumé exécutif

La beta.12 boucle deux chantiers majeurs (Forge IoT et les **opt-ins** projet)
et les amène jusqu'à la publication PyPI, la vérification post-publication
depuis un environnement utilisateur, et la mise à jour du **site officiel**
`forgemvc.com` (docs + landing publique). La suite complète est revenue à
`0 failed` avant la release, et le smoke test post-publication confirme un
parcours utilisateur fonctionnel de bout en bout. Le **core reste indépendant**
de l'opt-in IoT.

## Ce que beta.12 apporte

- `forge-mvc-iot` **publié sur PyPI** (première fois) ;
- parcours **MQTT → `iot_events` → API HTTP JSON** ;
- commandes `forge iot:doctor` / `iot:init` / `iot:listen` / `iot:simulate` ;
- **TLS MQTT** (configuration et clients) ;
- **Bearer token optionnel** pour l'API HTTP IoT ;
- diagnostic base / schéma via `forge iot:doctor --db` ;
- documentation **Mosquitto** / **ESP32** / **Arduino R4** / **BTS CIEL** ;
- structure **`optins/`** (couche de branchement explicite côté projet) ;
- `forge optin:enable iot` (dry-run par défaut, `--apply` pour écrire) ;
- `forge optin:list` (lecture seule, états absent / partiel / activé) ;
- starter **`welcome-iot`** (Bonjour IoT, sans broker ni base requis).

## Forge IoT

Forge IoT (`forge-mvc-iot`) ingère des relevés MQTT conformes au contrat
`forge/{site}/{device_id}/telemetry`, les stocke dans la table `iot_events` et
les expose via une API HTTP JSON (lecture, avec Bearer token optionnel). Le
flux local complet est : `forge iot:doctor` (statique) → `--mqtt` (broker) →
`forge iot:init` + `forge migration:apply` → `--db` (table) → `forge iot:listen`
(subscriber) ⟷ `forge iot:simulate` (capteurs simulés) → `curl /api/iot/events`.
La chaîne capteur réel ESP32 → MQTT → Forge est documentée et reproductible.

## Opt-ins projet utilisateur

Les opt-ins sont branchés **explicitement** dans le projet sous `optins/`, via
un registre visible (`optins/registry.py` → `register_optins(router)`) — **pas
de découverte magique**. `forge optin:enable iot` crée `optins/iot/` et branche
`mvc/routes.py` uniquement si la structure est reconnue (`router = Router()`),
sinon WARN + instruction manuelle ; idempotent, pas d'écrasement silencieux.
`forge optin:list` reste **lecture seule**.

## Commandes ajoutées ou stabilisées

- `forge iot:doctor` (+ options `--db`, `--mqtt`) ;
- `forge iot:init` ;
- `forge iot:listen` ;
- `forge iot:simulate` ;
- `forge optin:enable iot` (dry-run / `--apply`) ;
- `forge optin:list`.

## Publication PyPI

- **7 paquets publiés** en `1.0.0b12` :
  `forge-mvc`, `forge-mvc-iot`, `forge-mvc-rbac`, `forge-mvc-workflow`,
  `forge-mvc-stats`, `forge-mvc-mfa`, `forge-mvc-media` ;
- **14 distributions** uploadées (wheel + sdist par paquet) ;
- `forge-mvc-iot` **inclus pour la première fois**, classé **Alpha**
  (`Development Status :: 3 - Alpha`) ;
- **installation propre testée depuis PyPI** (`pip install --pre`) dans un venv
  neuf, hors dépôt de développement.

## Site officiel

- `forgemvc.com` **déployé en beta.12** (depuis `~/Projets/Forge-official-site`,
  jamais depuis le dépôt Forge) ;
- **docs publiques à jour** (import IoT + opt-ins + audits beta.12) ;
- landing enrichie avec la section **« Forge IoT et opt-ins explicites »** ;
- la **référence CLI publique** expose `iot:*` et `optin:*`.

## Landing publique

La landing canonique (`mvc/views/landing/index.html`, commit `c69fbe8`) annonce
beta.12 dès le hero et présente une section dédiée Forge IoT + opt-ins, avec
l'installation core-autonome / IoT-opt-in et une preuve qualité sobre. La même
landing a été synchronisée vers le site officiel (`0283e91`, liens relatifs) et
est en ligne sur `forgemvc.com`.

## Qualité et validations

- **suite complète revenue à `0 failed`** avant la release ;
- `pytest` complet validé ; `compileall` OK ; `ruff` OK ;
  `mkdocs build --strict` OK ; `twine check` OK ;
- **smoke test post-publication OK** (depuis PyPI, parcours IoT + opt-ins).

Chiffres connus (runs différents, avant/après release) :

- `16612 passed / 8 skipped / 0 failed` ;
- `16613 passed / 7 skipped / 0 failed`.

Ces deux totaux proviennent de runs distincts (l'ajout du garde-fou
post-publication décale le compte) ; le point important est **`0 failed`** dans
les deux cas.

## Incidents traités

- un **rsync de déploiement a été lancé par erreur depuis `~/Projets/Forge`**
  (mauvais `dist/`, qui contient des artefacts PyPI) au lieu de
  `~/Projets/Forge-official-site` ; détecté avant tout dommage durable ;
- **rollback** disponible via les backups datés `/srv/forge-web/backups/` ;
- **redéploiement correct depuis `~/Projets/Forge-official-site/dist/`** ;
- **site public vérifié OK** (HTTP 200, contenu beta.12, aucun artefact PyPI).

> Variante du même type d'incident côté import : un `import_forge_docs.py`
> lancé avec un `--source` à la racine du dépôt au lieu de `.../Forge/docs`
> avait vidé `docs/forge/` ; détecté immédiatement et réparé par un réimport
> déterministe (aucun fichier perdu). Trace conservée, sans dramatiser.

## Limites restantes

- `forge-mvc-iot` reste **Alpha** ;
- MQTT réel / MariaDB réels **non imposés** dans tous les smoke tests ;
- `requirements-dev.txt` **n'intègre pas encore** `forge-mvc-iot` ;
- `optin:enable` ne supporte **encore que `iot`** ;
- **pas de `optin:disable`** ;
- **pas de `optin:list --json`** ;
- pas encore de **généralisation RBAC / media / workflow / stats** des opt-ins.

## Prochains chantiers possibles

- `REQUIREMENTS-DEV-IOT-ALIGN-001` ;
- `OPTINS-CLI-ENABLE-RBAC-AUDIT-001` ;
- `OPTINS-CLI-DISABLE-AUDIT-001` ;
- `IOT-RETENTION-001` ;
- `FORGE-DESIGN-IOT-BRIDGE-001` ;
- `BETA13-ROADMAP-OPEN-001`.

## Décision de clôture

**GO — beta.12 clôturée.** La release `1.0.0-beta.12` est publiée sur PyPI,
vérifiée post-publication, et visible publiquement sur `forgemvc.com` (docs +
landing). Les chantiers Forge IoT et opt-ins sont clos pour leur périmètre
`iot`. Les ajustements restants sont reportés à une phase propre — prochain
ticket recommandé : `BETA13-ROADMAP-OPEN-001`. Ce ticket est tracé dans la
**roadmap** Forge.
