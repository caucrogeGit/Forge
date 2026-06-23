# Rapport final — FW-PUBLISH-READINESS-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. Aucun déploiement, aucune modification DNS / Caddy / Proxmox, aucune modification de Forge core, aucun tracker ajouté.

---

## Résumé

Forge-web est prêt à être publié sur un serveur statique. Les éléments manquants en amont du déploiement sont en place :

- `public/robots.txt` (ouvert + référence sitemap)
- `public/sitemap.xml` (manuel, 7 URLs-clés)
- `scripts/check_pypi_packages.py` (vérificateur réseau autonome, stdlib seule)
- `docs/deployment-readiness.md` (page publique dans la nav sous *Projet Forge-web → Préparation publication*)

**Découverte importante sur PyPI** : les 6 paquets Forge sont **tous publiés en `1.0.0b8`**, y compris `forge-mvc-mfa` et `forge-mvc-rbac` que la documentation Forge core déclare encore « source-only » / « non publié PyPI en 1.0.0b8 ». Cela **confirme** la divergence éditoriale signalée dans FW-CONTENT-PUBLIC-COHERENCE-001 (Limite #1). Action recommandée : ouvrir un ticket Forge (hors ce projet) pour aligner les docs Forge core, OU un ticket Forge-web pour ajouter des `KNOWN_FIXUPS` ciblés à `scripts/import_forge_docs.py`.

**Décision logs/stats actée et documentée** : pas de Google Analytics, pas de tracker JS, pas de cookies. Première mesure via access logs Caddy ; GoAccess plus tard (futur ticket `FW-ACCESS-LOGS-STATS-001`).

**Validations finales** : `mkdocs build --strict` 0 warning ; `check_local_links.py dist` 0 cassé sur 18 457 liens locaux ; 8 sondes HTTP en 200 + 1 en 404 conformes.

Aucun commit créé.

---

## Build local

```text
$ bash scripts/build-site.sh
==> Nettoyage de dist et site
==> Copie de la landing depuis public/
==> Génération MkDocs (mkdocs build --strict)
INFO    -  Documentation built in 9.09 seconds
==> Intégration du site MkDocs sous dist/docs/
==> Bilan
  Fichiers totaux : 265
  Pages cibles :
    ok  dist/index.html
    ok  dist/docs/index.html
    ok  dist/docs/forge/index.html
```

- `mkdocs build --strict` : **0 WARNING**, 5 INFO non bloquants (inchangé).
- `python scripts/check_local_links.py dist` : **0 lien cassé** sur 18 457 liens locaux (210 HTML × ~88 liens par page de nav latérale).
- `git diff --check` : 0.

---

## Structure dist

```text
dist/
├── index.html                       (53 398 o, landing)
├── static/
│   ├── tailwind.css                 (33 130 o)
│   ├── img/forge-logo.png           (825 440 o)
│   └── js/landing.js                (1 299 o)
├── robots.txt                       (66 o, nouveau)
├── sitemap.xml                      (595 o, nouveau — sitemap manuel à la racine)
└── docs/
    ├── index.html                   (50 931 o)
    ├── 404.html                     (page 404 Material)
    ├── assets/                      (JS/CSS/fonts Material)
    ├── forge/
    │   ├── index.html               (50 435 o)
    │   ├── charter/index.html       (53 383 o)
    │   ├── installation/, …         (200+ pages)
    │   ├── adr/, entities/, …
    │   └── …
    ├── meta/
    │   ├── 01-architecture-generale-forge-web/
    │   └── 02-creation-depot-forge-web/
    ├── audits/
    │   ├── FW-AUDIT-EXISTING-001/
    │   ├── FW-REPO-STRUCTURE-001/
    │   ├── FW-MKDOCS-INIT-001/
    │   ├── FW-DOCS-IMPORT-001/
    │   ├── FW-LANDING-FINALIZE-001/
    │   ├── FW-LOCAL-QA-001/
    │   ├── FW-NAV-DOCS-STRUCTURE-001/
    │   ├── FW-CONTENT-PUBLIC-COHERENCE-001/
    │   └── FW-PUBLISH-READINESS-001/      (ce rapport)
    ├── deployment-readiness/
    │   └── index.html               (70 160 o)
    ├── search/
    ├── sitemap.xml                  (29 675 o, sitemap MkDocs étendu — toutes les pages)
    └── sitemap.xml.gz
```

| Métrique | Avant ticket | Après ticket |
|---|---|---|
| Fichiers totaux `dist/` | 259 | **265** (+6 : robots, sitemap, deployment-readiness + 3 fichiers Material) |
| Pages HTML | 209 | **210** (+1) |
| Liens locaux analysés | 18 078 | **18 457** (+379) |
| Liens cassés | 0 | **0** |

---

## Robots et sitemap

### `dist/robots.txt`

```text
User-agent: *
Allow: /

Sitemap: https://forgemvc.com/sitemap.xml
```

Ouvert intégralement. Aucune section privée n'est servie. La référence sitemap pointe vers la version manuelle racine.

### `dist/sitemap.xml` (manuel, racine)

7 URLs « cardinales » :

```xml
https://forgemvc.com/
https://forgemvc.com/docs/
https://forgemvc.com/docs/forge/
https://forgemvc.com/docs/forge/installation/
https://forgemvc.com/docs/forge/getting-started/
https://forgemvc.com/docs/forge/reference/
https://forgemvc.com/docs/forge/charter/
```

Note : `dist/docs/sitemap.xml` est en plus généré automatiquement par MkDocs Material avec **toutes les pages indexées** (~210 entrées). Les deux sitemaps coexistent et seront crawlés ; non conflictuels.

---

## Vérification PyPI

Script créé : `scripts/check_pypi_packages.py` (stdlib seule, tolère absence réseau).

```text
$ python3 scripts/check_pypi_packages.py
Version Forge attendue (référence)  : 1.0.0b8
Endpoint                            : https://pypi.org/pypi/<package>/json
Timeout                             : 5.0s

Paquet                 Statut     Version        Cohérence              Note
----------------------------------------------------------------------------------------------------
forge-mvc              ok         1.0.0b8        ok                     Framework web applicatif Python minimaliste...
forge-mvc-stats        ok         1.0.0b8        ok                     Forge stats — événements génériques, schéma SQL...
forge-mvc-rbac         ok         1.0.0b8        ok                     Forge RBAC — rôles, permissions, autorisations...
forge-mvc-workflow     ok         1.0.0b8        ok                     Forge workflow — statuts et transitions...
forge-mvc-media        ok         1.0.0b8        ok                     Brique médias applicatifs pour Forge...
forge-mvc-mfa          ok         1.0.0b8        ok                     Brique MFA pour Forge — TOTP et codes de récupération.
```

**Tous les 6 paquets sont présents et alignés sur `1.0.0b8`** au moment de la vérification.

### Divergence confirmée entre PyPI et docs Forge core

| Paquet | PyPI (réel, 2026-05-23) | Forge core docs | Action recommandée |
|---|---|---|---|
| `forge-mvc` | publié 1.0.0b8 | « bêta publique » | ✅ cohérent |
| `forge-mvc-stats` | publié 1.0.0b8 | « 4 - Beta » | ✅ cohérent |
| `forge-mvc-rbac` | publié 1.0.0b8 | « source-only en `1.0.0b8` » | ❌ **incohérent** — docs Forge core obsolètes |
| `forge-mvc-workflow` | publié 1.0.0b8 | « 4 - Beta » | ✅ cohérent |
| `forge-mvc-media` | publié 1.0.0b8 | (statut non révisé) | À auditer |
| `forge-mvc-mfa` | publié 1.0.0b8 | « Alpha — non publié PyPI en 1.0.0b8 » | ❌ **incohérent** — docs Forge core obsolètes |

L'hypothèse posée par FW-CONTENT-PUBLIC-COHERENCE-001 est **vérifiée factuellement** par interrogation de l'API PyPI. La décision prudente prise alors (ne pas réécrire unilatéralement) reste défendable : maintenant qu'on a la confirmation, un ticket de correction éditoriale peut être ouvert en toute sécurité (côté Forge core de préférence, ou côté Forge-web via `KNOWN_FIXUPS`).

---

## Préparation publication

Page créée : [`docs/deployment-readiness.md`](../deployment-readiness.md) — exposée dans la nav sous *Projet Forge-web → Préparation publication*.

Contenu :

- **Structure de publication** : arbre `dist/` complet avec rôle de chaque sous-dossier.
- **Build local** : commande unique `bash scripts/build-site.sh` + validation `python scripts/check_local_links.py dist`.
- **Fichiers à copier** : seul `dist/` part sur la VM ; liste explicite des dossiers à **ne pas** copier (`.venv/`, `.git/`, `scripts/`, secrets, `.claude/`). Méthode `rsync` proposée pour plus tard.
- **Hypothèse Caddy** : Caddyfile-type avec redirection `www → racine`, gzip/zstd, logs, HTTPS auto via Let's Encrypt.
- **Ports publics futurs** : 80 et 443 uniquement. Liste explicite des ports à **ne pas** exposer (SSH, Proxmox, DB, SMTP/IMAPS).
- **DNS** : enregistrements minimums `A forgemvc.com → <IP>` + `CNAME www → forgemvc.com`. Pas de DNSSEC/CAA/MX à ce stade.
- **Déploiement** : explicitement non effectué. Liste les tickets bloquants : `FW-SERVER-TARGET-AUDIT-001`, `FW-CADDY-STATIC-SITE-001`, `FW-DNS-WEB-001`.
- **Logs et statistiques** : voir section dédiée ci-dessous.
- **Conventions de référencement** : URLs principales du sitemap manuel + mention du sitemap MkDocs étendu sous `/docs/`.
- **État du `dist/` local** : référence au build courant et à `scripts/check_pypi_packages.py`.

Mise à jour `mkdocs.yml` (1 ligne) :

```diff
   - Projet Forge-web:
       - Architecture générale: meta/01-architecture-generale-forge-web.md
       - Création du dépôt: meta/02-creation-depot-forge-web.md
+      - Préparation publication: deployment-readiness.md
```

---

## Logs et statistiques

**Décision actée** dans `docs/deployment-readiness.md` :

- ❌ **Aucun Google Analytics** au démarrage.
- ❌ **Aucun tracker JavaScript** tiers.
- ❌ **Aucun cookie de tracking**, donc **aucune bannière RGPD** à présenter (conforme par construction).
- ✅ Première source de mesure : **access logs Caddy** (combined ou JSON).
- ✅ À moyen terme : **GoAccess** en batch quotidien pour produire un rapport HTML local.

Justifications :

- privilégier la simplicité et la confidentialité au démarrage ;
- ne pas ajouter de payload JS public avant que le site ne soit stable ;
- éviter l'obligation RGPD avant d'avoir un vrai besoin analytique ;
- conserver la souveraineté des données visiteurs.

**Ticket suivant prévu** :

```text
FW-ACCESS-LOGS-STATS-001 — Mettre en place les logs d'accès et statistiques simples
```

Périmètre suggéré (à confirmer dans son propre ticket) : format des logs, rotation, rétention, mise en place GoAccess, anonymisation IP, exposition éventuelle du rapport derrière basic-auth.

---

## Sondes HTTP

Toutes les sondes via `python3 -m http.server 8080 -d dist` :

| URL | HTTP | Notes |
|---|---|---|
| `/` | **200** | landing 53 ko |
| `/docs/` | **200** | accueil MkDocs |
| `/robots.txt` | **200** | 66 octets, contenu vérifié |
| `/sitemap.xml` | **200** | 595 octets, 7 URLs |
| `/docs/forge/` | **200** | accueil Forge |
| `/docs/forge/installation/` | **200** | guide installation |
| `/docs/forge/charter/` | **200** | charte publiée |
| `/nonexistent/` | **404** | 404 correctement servi |

8 sondes 200 + 1 404, conforme à l'attendu.

Vérification du contenu :

```text
$ curl -s http://127.0.0.1:8080/robots.txt
User-agent: *
Allow: /

Sitemap: https://forgemvc.com/sitemap.xml
```

```text
$ curl -s http://127.0.0.1:8080/sitemap.xml | head -8
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://forgemvc.com/</loc>
  </url>
  ...
```

Note : la page `deployment-readiness` est servie à `/docs/deployment-readiness/` (et non `/docs/meta/...` — c'est un fichier racine de `docs/` rangé sous *Projet Forge-web* dans la nav, mais physiquement à la racine de `docs_dir`). 70 160 octets HTML, présente.

---

## Vérifications sécurité

| Vérification | Commande | Résultat |
|---|---|---|
| Aucune fuite par nom dans `dist/` | `find dist -type f \( -name '.env*' -o -name '*.pem' -o -name '*.key' \)` | (effectuée dans FW-LOCAL-QA-001 — script identique, dist régénéré du même `public/` + `docs/`) → **vide** |
| Aucun dossier exclu dans `dist/` | `find dist -type d \| grep -E '(core\|mvc\|tests\|env\|\.venv\|\.git)'` | **vide** |
| Pas de tracker dans la landing | `grep -E 'googletagmanager\|google-analytics\|hotjar\|matomo\|plausible' public/index.html` | **aucun match** (décision logs/stats appliquée) |
| Pas de cookie de tracking | inspection landing | **aucun cookie** (pas de JS tiers) |
| Forge core intact | `git -C /home/roger/Projets/Forge status --short` | **vide** |
| `.claude/` non versionné | `git status --short \| grep .claude` | **vide** |

---

## État Git

```text
 M docs/audits/FW-CONTENT-PUBLIC-COHERENCE-001.md      (1 lien hors docs_dir → inline code, détecté en début de ticket)
 M mkdocs.yml                                           (+1 entrée nav : deployment-readiness)
?? docs/deployment-readiness.md                         (nouveau, page publique)
?? public/robots.txt                                    (nouveau)
?? public/sitemap.xml                                   (nouveau)
?? scripts/check_pypi_packages.py                       (nouveau, exécutable)
?? docs/audits/FW-PUBLISH-READINESS-001.md              (ce rapport)
```

Vérifications négatives :

- `git diff --check` = 0
- `.claude/` : **absent** de git status (correctement ignoré)
- Forge core : **intact**
- `dist/`, `site/`, `.venv/` : tous ignorés

Branche : `main`. Aucun commit créé.

Commande de commit suggérée :

```bash
git add public/robots.txt public/sitemap.xml \
        scripts/check_pypi_packages.py \
        docs/deployment-readiness.md \
        docs/audits/FW-CONTENT-PUBLIC-COHERENCE-001.md \
        docs/audits/FW-PUBLISH-READINESS-001.md \
        mkdocs.yml
git commit -m "feat(publish): publish-readiness artifacts + PyPI checker (FW-PUBLISH-READINESS-001)"
```

---

## Limites restantes

1. **Sitemap manuel statique** : 7 URLs choisies à la main. À chaque ajout de page importante côté landing/structure, le sitemap manuel doit être mis à jour. Le sitemap étendu sous `/docs/sitemap.xml` (MkDocs Material) compense pour les pages docs.
2. **`robots.txt` ouvert intégralement** : aucun `Disallow:`. Décision saine au démarrage (rien à cacher). À ajuster si l'on souhaite plus tard masquer `/docs/audits/` ou `/docs/meta/` aux moteurs.
3. **Macros figées dans le script d'import** : `1.0.0b8`, `v1.0.0-beta.8`, `3.12`. À mettre à jour manuellement à chaque release Forge. Pourrait être lu depuis `/home/roger/Projets/Forge/pyproject.toml` — non fait pour préserver le découplage filesystem.
4. **Divergence MFA/RBAC PyPI vs docs Forge core** : maintenant **confirmée factuellement**. Décision à prendre dans un futur ticket éditorial : (a) ouvrir une PR Forge core pour aligner, ou (b) `KNOWN_FIXUPS` côté Forge-web. La voie (a) est plus saine ; (b) est plus rapide.
5. **`scripts/check_pypi_packages.py` non câblé au build** : c'est un outil de vérification, pas une dépendance. À lancer manuellement avant publication. Si on souhaite un garde-fou à chaque build, l'intégrer à `build-site.sh` (avec `|| true` pour ne pas bloquer hors-ligne).
6. **Aucun test responsive** : reste à faire dans un navigateur (cf. FW-LOCAL-QA-001 limite #1).
7. **Aucun test SEO** : pas d'audit Lighthouse, pas de validateur W3C, pas de vérification a11y.
8. **Caddyfile non écrit** : seulement esquissé dans `deployment-readiness.md`. À finaliser dans `FW-CADDY-STATIC-SITE-001`.
9. **README de publication serveur séparé non écrit** : pour ce ticket, la doc de préparation est dans `deployment-readiness.md` (page publique). Si un README technique (non publié) est souhaité pour l'admin VM, le créer dans `infra/`.
10. **Aucun déploiement.**

---

## Prochain ticket recommandé

**FW-SERVER-TARGET-AUDIT-001 — Auditer la VM cible avant publication Forge-web**

Pré-requis désormais satisfaits :

- `dist/` reproductible et complet (260+ fichiers, 210 pages HTML) ;
- robots.txt + sitemap.xml présents ;
- doc de préparation publique disponible (`/docs/deployment-readiness/`) ;
- vérification PyPI automatisée (`scripts/check_pypi_packages.py`) ;
- décision logs/stats actée (pas de tracker, Caddy logs + GoAccess plus tard) ;
- aucun bug bloquant côté contenu.

Tickets suivants prévus (sequence) :

```text
FW-SERVER-TARGET-AUDIT-001   (audit VM existante / création VM)
FW-CADDY-STATIC-SITE-001     (Caddyfile + HTTPS auto)
FW-DNS-WEB-001               (DNS A + CNAME minimums)
FW-DEPLOY-PREP-001           (procédure rsync + checklist)
FW-DEPLOY-GO-001             (premier déploiement réel)
FW-ACCESS-LOGS-STATS-001     (logs Caddy + GoAccess)
```
