# FW-CONTENT-SYNC-FORGE-CURRENT-001 — Resynchroniser le contenu public Forge-web avec Forge actuel

## Objectif

Resynchroniser le contenu publié sur `forgemvc.com` à partir de la documentation
actuelle du dépôt Forge, sans modifier le cœur Forge et sans intervention directe
sur la VM. Distinguer clairement la version publique installable et les travaux
en cours non publiés.

## Sources utilisées

- Dépôt Forge (lecture seule) : `/home/roger/Projets/Forge`
  - branche `main`, HEAD `5ebc978` (au moment de l'import : `0374ada`)
  - `pyproject.toml` : `version = "1.0.0b8"`
  - dernier tag : `v1.0.0-beta.8`
- Dépôt Forge-web (modifiable) : `/home/roger/Projets/Forge-web`
  - branche `main`, base `4278b9c`

Vérification PyPI (`scripts/check_pypi_packages.py`) au 2026-05-24 :

| Paquet | Statut PyPI | Version | Cohérence |
|---|---|---|---|
| `forge-mvc` | publié | `1.0.0b8` | ok |
| `forge-mvc-rbac` | publié | `1.0.0b8` | ok |
| `forge-mvc-workflow` | publié | `1.0.0b8` | ok |
| `forge-mvc-stats` | publié | `1.0.0b8` | ok |
| `forge-mvc-media` | publié | `1.0.0b8` | ok (Alpha) |
| `forge-mvc-mfa` | publié | `1.0.0b8` | ok (Alpha) |

Tous les opt-ins ont été publiés en 1.0.0b8 (cf. `docs/forge/history/audits/audit-post-publication-beta8.md`).

## Distinction version publique / travaux en cours

| Élément | Valeur |
|---|---|
| Version publique installable (PyPI) | `forge-mvc==1.0.0b8` (et les 5 opt-ins à la même version) |
| Tag Git correspondant | `v1.0.0-beta.8` |
| HEAD `main` Forge au moment de l'import | `0374ada` (post-tag) |
| Travaux en cours | bêta 9 — non publiée, aucun tag, aucun package PyPI |

Le site ne référence ni « beta 9 » ni « 3.0 » comme version installable.

## Travail réalisé

### 1. Audit initial

Recherche des mentions obsolètes listées dans le ticket sur l'ensemble du contenu
public :

| Motif | Occurrences avant | Localisation |
|---|---|---|
| `3.0.6` | 0 | — |
| `Forge 2.0` | nombreuses | uniquement dans `docs/forge/history/`, `docs/forge/adr/`, `docs/forge/roadmap/`, `docs/forge/deprecation-policy.md` (contexte historique légitime) |
| `github.io` | 31 dans le site bâti | uniquement dans des pages historiques, des blocs de code d'exemple (`starters/welcome/index.md`), `search_index.json`, et les anciens audits FW-* |
| `source-only` | nombreuses | uniquement dans contextes historiques ou descriptions d'opt-ins (état pré-publication PyPI) |
| `Pre-Alpha` | 20 | descriptions historiques du module MFA (requalifié Alpha en `MFA-PYPI-READY-001`) |
| `1.0.0-beta.1` | 12 | baselines d'audits historiques |
| `1.0.0b7` | 3 | notes de release historiques |
| `1.0.0b8` | 87 | version courante — mention légitime |

### 2. Réimport contrôlé

Exécuté : `python scripts/import_forge_docs.py`

Résultat :

```
Destination vidée (58 entrées supprimées)
Markdown racine importés : 47
Sous-dossiers OK : adr (14), reference (12), starters (14), contributing (1),
                   roadmap (4), history (77), testing (15), entities (10),
                   security (2), static (4 copiés / 4 ignorés)
Sanitisation index.html → index.md : 65 fichiers réécrits
Fixups ciblés appliqués : 1
Total : 47 .md racine + 153 sous-dossiers (4 ignorés non-Markdown, 0 fuite)
```

Différentiel vs état précédent :

- `docs/forge/15-minutes.md` — ajout d'un paragraphe sur `scripts/dev-server.sh`
- `docs/forge/reference/cli-commands.md` — enrichissement (commandes CLI)
- `docs/forge/history/audits/cli-help-flags-audit-001.md` — nouveau fichier importé

### 3. Macros et substitutions

`scripts/import_forge_docs.py` continue de substituer :

- `{{forge_version}}` → `1.0.0b8`
- `{{forge_tag}}` → `v1.0.0-beta.8`
- `{{python_min}}` → `3.12`

Aucune modification du script n'a été nécessaire : la valeur cible est inchangée.

### 4. Mentions obsolètes traitées

Dans `public/index.html` (corrections directes — landing maintenue côté Forge-web) :

| Avant | Après | Motif |
|---|---|---|
| « Après 3.0 — Stabilisation » | « Travaux en cours — Stabilisation 1.0 » | « 3.0 » n'est pas le numéro de la prochaine version |
| « 4 modules officiels (MFA, RBAC, Workflow, Stats) » | « 5 modules officiels (RBAC, Workflow, Stats, Media, MFA) » | Media présent dans le catalogue |
| « Les modules opt-in s'installent depuis GitHub via `requirements-dev.txt` » | « Les 5 modules opt-in sont publiés sur PyPI à la même version » | Contradiction avec l'état PyPI réel |
| Bloc Modules : « Installer via … ou via extras `forge-mvc[mfa]` » | Bloc Modules : « Distribués sur PyPI à 1.0.0b8 — `pip install --pre forge-mvc-<module>` » | Les extras `[mfa]` ne sont pas exposés en 1.0.0b8 |

Aucune modification dans `docs/forge/` : le contenu importé est conservé tel quel
(la macro `{{forge_version}}` couvre le besoin de substitution).

### 5. Mentions volontairement conservées

| Catégorie | Justification |
|---|---|
| Références « Forge 2.0 » dans `docs/forge/history/` | Documents historiques figés (audits, roadmap post-2.0, etc.) |
| Références « Forge 2.0 » dans `roadmap/forge-roadmap.md`, ADR 001/002, `deprecation-policy.md` (exemples) | Cœur Forge en amont — hors périmètre |
| `source-only` dans contextes historiques (`release-policy.md` rétro, history/) | Décrit un état révolu, légitime |
| `Pre-Alpha` (20 occurrences) | Documente historiquement le statut du module MFA |
| `caucrogegit.github.io` dans `starters/welcome/index.md` | Inclus dans un bloc de code HTML servant d'exemple |
| `caucrogegit.github.io` dans `docs/audits/FW-*.md` | Audits historiques du projet Forge-web |

Aucune de ces mentions n'apparaît dans la landing publique ni dans la navigation
principale MkDocs.

## Validations exécutées

| Validation | Commande | Résultat |
|---|---|---|
| Build MkDocs strict | `mkdocs build --strict` | exit 0 (uniquement des INFO orphelines tolérées) |
| Build site complet | `bash scripts/build-site.sh` | 279 fichiers, 3 pages cibles OK |
| Liens locaux | `python scripts/check_local_links.py dist` | 42 929 liens analysés, **0 lien cassé** |
| Cohérence PyPI | `python scripts/check_pypi_packages.py` | 6 paquets `1.0.0b8` cohérents |
| Diff propre | `git diff --check` | aucun warning |
| Source Forge intacte | `git -C /home/roger/Projets/Forge status docs/` | aucune modification |

## Limites restantes

1. **Contradiction interne du cœur Forge sur le statut PyPI de Media et MFA** :
   `docs/forge/release-policy.md` (importé depuis amont) déclare encore Media et
   MFA « non publié en `1.0.0b8` » à plusieurs endroits, tandis que
   `docs/forge/history/audits/audit-post-publication-beta8.md` (importé du même
   amont) confirme leur publication. PyPI confirme le second. Correction à
   pousser dans le cœur Forge — hors périmètre de ce ticket.

2. **Pages orphelines** : ~150 fichiers importés (history/, testing/, reference
   secondaires, ADR récents 009-014, entities/) ne sont pas inscrits dans la
   navigation `mkdocs.yml`. Elles restent accessibles par URL directe mais ne
   sont pas surfacées. Non bloquant pour la résynchronisation ; à arbitrer dans
   un ticket dédié à la structure de navigation si souhaité.

3. **Avertissement Material for MkDocs 2.0** : le thème affiche un message
   d'avertissement sur la disparition future du système de plugins. Information
   d'éditeur, sans impact immédiat.

4. **Lien « `forge-mvc[mfa]` extras »** : le site ne référence plus cette
   syntaxe. Si Forge expose les extras dans une future bêta, mettre à jour la
   landing en conséquence.

## Aucune intervention serveur

- Aucune modification de `/srv/forge-web/current`.
- Aucune modification de Caddy, DNS, Proxmox ou pare-feu.
- Aucun déploiement n'a été lancé. La distribution `dist/` est prête pour un
  prochain `scripts/deploy-to-forge-web.sh` lorsque l'opérateur le décidera.

## Fichiers modifiés (Forge-web)

```
 M docs/forge/15-minutes.md
 M docs/forge/reference/cli-commands.md
 M public/index.html
?? docs/forge/history/audits/cli-help-flags-audit-001.md
?? docs/audits/FW-CONTENT-SYNC-FORGE-CURRENT-001.md
```

## Prochain ticket recommandé

`FW-DEPLOY-CONTENT-SYNC-001` — déployer la résynchronisation contrôlée vers
`/srv/forge-web/current` après validation visuelle locale de la landing et de
deux pages clés (`/docs/forge/release-policy/`, `/docs/forge/installation/`).

Alternatives complémentaires si pertinent :

- `FW-NAV-ORPHANS-001` — décider quelles pages orphelines surfacer dans le nav
  MkDocs (history, testing, ADR 009-014, entities/).
- `FORGE-RELEASE-POLICY-PYPI-COHERENCE-001` (ticket côté cœur Forge, hors
  Forge-web) — aligner `release-policy.md` avec l'état PyPI réel des modules.
