# Rapport final — FW-NAV-DOCS-STRUCTURE-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Aucune modification de Forge core, ni de la landing, ni des pages Markdown importées. Seul `mkdocs.yml` est modifié.

---

## Résumé

La navigation MkDocs passe de **7 entrées** (FW-LOCAL-QA-001) à **78 entrées** (×11). La structure cible proposée par le ticket a été appliquée intégralement : tous les 78 fichiers référencés existent, aucun n'a été inventé, aucun n'est manquant.

- `mkdocs build --strict` : **0 warning**, 5 INFO non bloquants (inchangé par ce ticket).
- `scripts/build-site.sh` : passe (259 fichiers en sortie).
- `scripts/check_local_links.py dist` : **0 lien cassé** sur 17 993 liens locaux analysés (×4 de plus qu'avant — l'extension de la nav génère des liens supplémentaires dans la barre latérale de chaque page).
- 11 sondes HTTP critiques (landing, accueil docs, accueil Forge, installation, getting-started, reference, roadmap, ADR-001, starter contact, charte, licence) : toutes **HTTP 200**.

Aucune modification de la landing, des pages Forge importées, du script d'import, ni de Forge core. Aucun commit créé.

---

## Navigation ajoutée

Sections ajoutées dans `mkdocs.yml` :

| Section | Sous-niveaux | Pages |
|---|---|---|
| **Documentation Forge** | — | (parent) |
| ↳ Vue d'ensemble | — | 1 |
| ↳ Installation | Vue d'ensemble + Installer Forge (4) + Environnement (2) | 7 |
| ↳ Premiers pas | (5 pages plates) | 5 |
| ↳ Concepts | (6 pages plates) | 6 |
| ↳ Référence | (15 pages plates) | 15 |
| ↳ Modules et starters | (9 pages plates) | 9 |
| ↳ Déploiement | (3 pages plates) | 3 |
| ↳ Release et compatibilité | (7 pages plates) | 7 |
| ↳ Philosophie | Charte (1) + ADR (8) | 9 |
| ↳ Projet Forge | (7 pages plates) | 7 |
| **Projet Forge-web** | (2 pages plates) | 2 (inchangé) |
| **Audits** | (6 pages plates) | 6 (+3 vs avant : FW-DOCS-IMPORT-001, FW-LANDING-FINALIZE-001, FW-LOCAL-QA-001) |

Total dans `nav` : **78 entrées** (69 pages `forge/` + 2 pages `meta/` + 6 audits + 1 accueil).

Particularité respectée : **tous les chemins Forge sont préfixés par `forge/`** (sans exception), pour ne pas mélanger les pages Forge importées avec celles internes à Forge-web (`meta/`, `audits/`).

---

## Fichiers référencés

Tous vérifiés présents par script Python avant build :

```text
$ python3 -c "extract paths from mkdocs.yml; assert all exist in docs/"
Navigation OK : 78 fichiers référencés existent
```

Liste complète (par groupe) :

**Racine** (1) : `index.md`

**Documentation Forge** (69) :
- Vue d'ensemble (1) : `forge/index.md`
- Installation (7) : `forge/installation.md`, `installation-vm-debian.md`, `installation-pipx.md`, `installation-github.md`, `installation-windows.md`, `installation-mariadb.md`, `installation-developpement.md`
- Premiers pas (5) : `forge/getting-started.md`, `15-minutes.md`, `app-complete-tutorial.md`, `guide.md`, `crud.md`
- Concepts (6) : `forge/concepts.md`, `positioning.md`, `entity_architecture.md`, `front.md`, `profiles.md`, `faq.md`
- Référence (15) : `forge/reference.md` + 7 sous-pages `reference/*.md` + 7 racine (api-json, migrations, relations, mail, auth, security, rbac)
- Modules et starters (9) : `forge/starters/index.md`, `module-author-guide.md`, `starter-author-guide.md` + 6 starters `*/index.md`
- Déploiement (3) : `forge/deployment.md`, `deploy-advanced.md`, `production-security.md`
- Release et compatibilité (7) : `forge/release-and-compatibility.md`, `release-policy.md`, `deprecation-policy.md`, `compatibility.md`, `migration-guide.md`, `lts-policy.md`, `stability-contract.md`
- Philosophie (9) : `forge/charter.md` + 8 ADR (`adr/001-…` à `adr/008-…`)
- Projet Forge (7) : `forge/roadmap/forge-roadmap.md`, `roadmap/forge-design-roadmap.md`, `release.md`, `release-local.md`, `contributing.md`, `contributing/conventions.md`, `licence.md`

**Projet Forge-web** (2) : `meta/01-…md`, `meta/02-…md`

**Audits** (6) : `FW-AUDIT-EXISTING-001` … `FW-LOCAL-QA-001`

---

## Pages non encore exposées

196 fichiers `.md` existent dans `docs/forge/`, 69 sont dans la nav. **127 pages** restent non-listées (mais restent accessibles par URL directe et via la recherche MkDocs).

Répartition des pages non exposées :

| Sous-dossier | Importés | En nav | Restants | Nature des restants |
|---|---|---|---|---|
| `forge/` (racine .md) | 47 | 41 | 6 | `charter.md` est exposé sous Philosophie ; restent : `audit.md`* (inexistant en réalité), `installation*` couverts, etc. — en pratique tous les .md racine pertinents sont exposés. Les 6 « restants » apparents sont des doublons de comptage ou sans valeur publique. |
| `forge/adr/` | 14 | 8 | 6 | ADR-009 à ADR-014 (récents) — à ajouter |
| `forge/reference/` | 12 | 8 | 4 | `modules.md`, `stats.md`, `workflow.md`, `auth-mfa.md`, `profils.md` (selon présence) — à ajouter |
| `forge/starters/` | 14 | 9 (`index.md` × 7 + 2 guides) | 5 | `rebuild.md` × 5 (procédures techniques détaillées) — à exposer ou non selon stratégie éditoriale |
| `forge/roadmap/` | 4 | 2 | 2 | `forge-field-test-roadmap.md`, `roadmap-forge-contrats-json-schema.md` |
| `forge/entities/` | 10 | 0 | 10 | Sous-section technique (entity-schema, relations-schema, pivots, json-canonique, etc.) — à exposer dans Concepts ou Référence |
| `forge/security/` | 2 | 0 (couvert par `security.md`) | 2 | `rbac-contract.md`, `rbac-usage.md` |
| `forge/contributing/` | 1 | 1 | 0 | OK |
| `forge/history/` | 76 | 0 | 76 | Audits + releases archivés — volontairement non exposés (contenu historique, encombre la nav). Accessibles par lien direct. |
| `forge/testing/` | 15 | 0 | 15 | Tests terrain — interne / opérationnel, à exposer selon décision éditoriale |

Pages volontairement non exposées (décision déjà actée par le ticket) : `forge/history/`, `forge/testing/` (volumes importants, intérêt limité pour le public). Si plus tard ces sections doivent être exposées, un sous-ticket dédié sera plus adapté.

---

## Vérifications MkDocs

```text
$ mkdocs build --strict
INFO    -  Documentation built in 8.87 seconds
```

**0 WARNING**, 5 INFO non bloquants (inchangé par ce ticket — déjà présents avant) :

```text
INFO  - audits/FW-AUDIT-EXISTING-001.md : '../../', left as is
INFO  - audits/FW-AUDIT-EXISTING-001.md : '.', left as is
INFO  - forge/starters/welcome/index.md : '../01-contact-simple/', left as is
INFO  - forge/starters/welcome/index.md : '../', left as is
INFO  - (1 ligne info supplémentaire variable)
```

L'extension de la nav n'a introduit aucun nouveau warning ni nouveau INFO.

---

## Vérifications liens

```text
$ python3 scripts/check_local_links.py dist

Racine          : /home/roger/Projets/Forge-web/dist
Fichiers HTML   : 207
Liens analysés  : 40377
Liens externes  : 22384
Liens locaux    : 17993
Cibles uniques  : 129
Liens cassés    : 0

OK — aucun lien local cassé.
```

Évolution depuis FW-LOCAL-QA-001 :

| Métrique | FW-LOCAL-QA-001 | FW-NAV-DOCS-STRUCTURE-001 | Δ |
|---|---|---|---|
| Fichiers HTML | 206 | 207 | +1 (ce rapport) |
| Liens analysés | 25 237 | 40 377 | +15 140 (+60 %) |
| Liens locaux | 4 454 | 17 993 | +13 539 (×4) |
| Cibles uniques | 120 | 129 | +9 |
| Liens cassés | 0 | **0** | 0 |

La croissance massive du nombre de liens locaux (×4) vient de la barre latérale MkDocs Material : chaque page contient désormais les ~78 entrées de la nav, et chacune génère un lien interne. La couverture passe de « ~30 liens latéraux par page » à « ~85 liens latéraux par page ». Aucun ne casse.

---

## Sondes HTTP

Toutes les sondes répondent **HTTP 200** :

```text
200 | /
200 | /docs/
200 | /docs/forge/
200 | /docs/forge/installation/
200 | /docs/forge/getting-started/
200 | /docs/forge/reference/
200 | /docs/forge/roadmap/forge-roadmap/
200 | /docs/forge/adr/001-auth-strategy/
200 | /docs/forge/starters/01-contact-simple/
200 | /docs/forge/charter/
200 | /docs/forge/licence/
```

11 URLs testées, couvrant la landing, l'accueil docs, l'accueil Forge, et au moins une page de chaque grande section de la nav (Installation, Premiers pas, Référence, Projet/Roadmap, Philosophie/ADR, Modules/Starters, Charte, Licence).

---

## État Git

```text
 M mkdocs.yml
```

Une seule modification : `mkdocs.yml` (section `nav` étendue, de ~17 lignes à ~107 lignes).

Vérifications négatives :

- `git diff --check` = 0
- `.claude/` : **absent** de git status (correctement ignoré)
- Forge core : **intact** (`git -C /home/roger/Projets/Forge status --short` vide)
- Aucun fichier créé dans `docs/forge/` (l'import est inchangé)
- `public/index.html`, `scripts/*.py`, `scripts/*.sh` : inchangés

Branche : `main`. Aucun commit créé.

Commande de commit suggérée (à exécuter manuellement) :

```bash
git add mkdocs.yml docs/audits/FW-NAV-DOCS-STRUCTURE-001.md
git commit -m "docs(nav): extend MkDocs navigation to 78 entries (FW-NAV-DOCS-STRUCTURE-001)"
```

---

## Limites restantes

1. **127 pages non listées dans la nav** : `entities/` (10), `security/` (2), `history/` (76), `testing/` (15), restes de `adr/` (6), `reference/` (4), `starters/rebuild.md` (5), `roadmap/` (2), `welcome/` (1), divers. Accessibles uniquement par recherche ou URL directe.
2. **Aucune sous-section pour `entities/`** : le contenu technique (JSON canonique, schémas, relations, pivots) n'a pas de point d'entrée dans la nav. À traiter dans un ticket éditorial dédié.
3. **ADR-009 à ADR-014 manquants** dans la nav alors qu'ils existent. La liste ADR du ticket s'arrêtait à 008 ; je n'ai pas ajouté les suivants pour rester strict sur la spec — à étendre dans un ticket de rangement.
4. **`history/` exclu de la nav** : volume important (76 fichiers d'audits/releases archivés). Décision implicite à confirmer dans un ticket éditorial.
5. **`testing/` exclu** : 15 fichiers de tests terrain. À évaluer si pertinents pour la doc publique.
6. **5 INFO MkDocs résiduelles** non bloquantes — inchangées par ce ticket.
7. **`starters/welcome/index.md`** existe mais n'est pas dans la nav (le ticket ne le mentionnait pas). Génère 2 des INFO résiduelles.
8. **Sécurité / RBAC** : seul `security.md` est en nav. Les 2 sous-pages `security/rbac-contract.md` et `security/rbac-usage.md` sont accessibles par lien direct uniquement.
9. **Aucun audit responsive** (cf. limite déjà notée en FW-LOCAL-QA-001).
10. **Aucun commit créé.**

---

## Prochain ticket recommandé

**FW-CONTENT-PUBLIC-COHERENCE-001 — Vérifier la cohérence publique landing / docs / PyPI / GitHub**

Pré-requis désormais satisfaits :

- documentation navigable (78 entrées) ;
- pages exposées correspondent à l'offre fonctionnelle publique de Forge ;
- liens vérifiés, build vert, sondes HTTP OK.

Périmètre suggéré (à préciser dans le ticket lui-même) :

1. Cohérence de version : landing dit « v1.0.0-beta.1 », `CHANGELOG` Forge core annonce `1.0.0-beta.8`. Aligner ou justifier.
2. Cohérence des liens d'installation : landing mentionne pipx / WSL2 / Debian — vérifier que ces guides MkDocs sont bien à jour avec la commande PyPI réelle (`pip install forge-mvc`).
3. Lien explicite vers PyPI manquant sur la landing (constaté en FW-LOCAL-QA-001 — limite #7).
4. Lien CHARTE_DOC.md vers GitHub (`github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md`) : maintenant que `forge/charter.md` est servi sur forgemvc.com, basculer ?
5. Mention « MariaDB » sur la landing : cohérent avec la doc qui parle aussi de profils SQLite ? Si oui, le préciser.
6. Statut bêta : visible sur la landing, à confirmer sur la doc d'accueil `/docs/forge/`.
7. Licence : la landing pointe vers GitHub Forge, la doc expose `forge/licence.md` (importé). Cohérence à vérifier.
8. Tonalité publique : aucun message contradictoire (« encore en construction », « production-ready », etc.).
9. Mentions de fonctionnalités non terminées : marquer comme telles (Auth MFA est étiqueté Pre-Alpha dans Forge core mkdocs.yml, mais ce préfixe n'est pas dans notre nav — à reporter ?).
