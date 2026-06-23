# Audit synchronisation site officiel — Forge 1.0.0-beta.10

Ticket : `FORGE-OFFICIAL-SITE-SYNC-BETA10-001`
Date : 2026-05-25
Dépôt local : `~/Projets/Forge-web` (nom du dépôt non encore renommé en
`Forge-official-site`).

## Source utilisée

- Dépôt source : `~/Projets/Forge` (branche `main`, propre).
- Tag canonique : `v1.0.0-beta.10` → commit `86b90c2`
  (`fix(landing): simplify static contact link`).
- Aucune modification effectuée dans Forge core.

## Fichiers synchronisés

Landing (copie directe depuis la source canonique Forge core) :

- `mvc/views/landing/index.html` → `public/index.html`
- `docs/static/tailwind.css` → `public/static/tailwind.css`
- `docs/static/img/forge-logo.png` → `public/static/img/forge-logo.png`
- `docs/static/js/landing.js` → `public/static/js/landing.js`

Documentation (via `scripts/import_forge_docs.py`, liste blanche stricte) :

- 49 fichiers `.md` à la racine de `docs/`
- 157 fichiers dans les sous-dossiers whitelisted
  (`adr`, `reference`, `starters`, `contributing`, `roadmap`, `history`,
  `testing`, `entities`, `security`, `static`)
- 4 fichiers ignorés (extensions hors whitelist)
- 0 fuite détectée par le garde-fou final

Mise à jour macros dans `scripts/import_forge_docs.py` :

- `{{forge_version}}` : `1.0.0b9` → `1.0.0b10`
- `{{forge_tag}}` : `v1.0.0-beta.9` → `v1.0.0-beta.10`
- 64 fichiers réécrits par la sanitisation `index.html` → `index.md`
- 1 fixup ciblé (`reference.md`)

Corrections locales pour faire passer `mkdocs build --strict` :

- `docs/audits/forge-web-secret-exposure-audit.md` : lien
  `../../scripts/audit-secrets.sh` transformé en code inline (cible hors
  `docs/`, non résolvable par MkDocs strict)
- `docs/security/deployment-secrets.md` : même correction

Ces fichiers étaient déjà présents non versionnés (issus de
`FORGE-WEB-SECRET-EXPOSURE-AUDIT-001`) ; les liens cassaient le build strict.

## Landing beta.10

Vérifications sur `dist/index.html` :

- `1.0.0-beta.10` présent ;
- `forge-mvc==1.0.0b10` présent ;
- `mailto:forgemvc@gmail.com` présent (3 occurrences : intro, footer,
  bouton « Écrire à Forge ») ;
- `Roger Lequette` présent ;
- Aucune occurrence de `1.0.0-beta.9` ou `1.0.0b9` ;
- Aucun formulaire de contact (`Envoyer`, `traitement serveur`, `base SMTP`
  absents).

Note : le `<form action="search/">` présent dans la landing est la barre de
recherche documentaire MkDocs (légitime). Le critère « no form » du ticket
visait explicitement le formulaire contact ; l'absence de contact form est
confirmée.

## Documentation beta.10

- `mkdocs build --strict` : OK.
- Bilan `dist/` : 288 fichiers, 29 MB.
- Pages cibles présentes : `dist/index.html`, `dist/docs/index.html`,
  `dist/docs/forge/index.html`.
- Pages clés vérifiées (HTTP 200 après déploiement) :
  - `/docs/forge/installation/` (affiche `1.0.0-beta.10` et `1.0.0b10`) ;
  - `/docs/forge/production-security/` ;
  - `/docs/forge/release-policy/` ;
  - `/docs/forge/wsgi-deployment/`.

Les occurrences résiduelles de `1.0.0-beta.9` dans la doc sont toutes
historiques (release-policy, roadmap, audits, changelog des phases B9) —
légitimes.

## Build local

```bash
bash scripts/build-site.sh
# → Documentation built in 9.98 seconds
# → Fichiers totaux : 288
# → ok dist/index.html, dist/docs/index.html, dist/docs/forge/index.html
```

`git diff --check` : aucun whitespace problématique.

## Audit secrets

```bash
bash scripts/audit-secrets.sh
# → 7 sections, toutes OK
# → GO — aucun secret de déploiement détecté dans le dépôt.
```

## Déploiement

- Staging via `DRY_RUN=0 bash scripts/deploy-to-forge-web.sh`
  (rsync 4,4 MB envoyés, 27,8 MB total avec speedup 6.32×).
- Cible SSH : `roger@192.168.1.98`.
- Staging distant : `/tmp/forge-web-deploy-staging/` (vérifié : `index.html`
  beta.10 et `docs/index.html` présents).
- Bascule prod manuelle sur la VM (sudo) :
  - Backup : `/srv/forge-web/backups/current-20260525-183311` ;
  - `rsync -a --delete` staging → `/srv/forge-web/current/` ;
  - Vérification post-bascule : `1.0.0-beta.10` dans
    `/srv/forge-web/current/index.html`.

## Vérification publique

```text
curl -sI https://forgemvc.com/        → HTTP/2 200
curl -sI https://forgemvc.com/docs/   → HTTP/2 200
curl -sI https://forgemvc.com/docs/forge/  → HTTP/2 200
```

Marqueurs publics retrouvés sur `https://forgemvc.com/` :

- `1.0.0-beta.10`
- `forge-mvc==1.0.0b10`
- `forgemvc@gmail.com`
- `Roger Lequette`
- `Écrire à Forge`

Aucune occurrence de `1.0.0-beta.9` ou `1.0.0b9` sur la landing publique.

## Résultat final

**GO — forgemvc.com publie Forge 1.0.0-beta.10**

Tous les critères d'acceptation sont remplis :

- landing publique affiche `1.0.0-beta.10` ;
- contact public : `Roger Lequette` + `forgemvc@gmail.com` ;
- bouton « Écrire à Forge » : `mailto:` fonctionnel ;
- aucun formulaire contact fragile ;
- documentation publique = Forge beta.10 ;
- liens PyPI vers `forge-mvc==1.0.0b10` ;
- `mkdocs build --strict` : OK ;
- aucun secret de déploiement ajouté ;
- site déployé sur `forgemvc.com` ;
- vérifications curl publiques confirment beta.10.

Rollback disponible :

```bash
sudo rsync -a --delete /srv/forge-web/backups/current-20260525-183311/ \
                       /srv/forge-web/current/
```
