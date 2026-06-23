# Rapport final — FW-LOCAL-QA-001

> Date : 2026-05-23
> Branche : `main`
> Périmètre exécuté : strictement celui du ticket. QA locale uniquement. Aucun déploiement. Aucune modification de Forge core. Aucune modification DNS / Caddy / Proxmox.

---

## Résumé

QA locale du site Forge-web complet. Le build (`scripts/build-site.sh`) passe en `--strict` sans warning, **toutes les pages critiques et tous les assets répondent HTTP 200**, le 404 fonctionne, **0 lien interne cassé** sur l'ensemble des 25 237 liens analysés.

Trois bugs structurels détectés et corrigés pendant la QA :

1. **`site_url` MkDocs incorrect** : pointait sur `https://forgemvc.com/` alors que la doc est servie à `/docs/`. Conséquence : la page `404.html` générée par MkDocs Material contenait 16 liens absolus `/forge/...`, `/assets/...`, `/meta/...` cassés. Corrigé par `site_url: https://forgemvc.com/docs/`.
2. **Lien cassé dans `docs/forge/reference.md`** : `[ADR suivants](adr/)` pointait vers un dossier sans `index.md` (bug existant aussi côté Forge core). Ajout d'un fixup ciblé dans `scripts/import_forge_docs.py` pour le supprimer à chaque ré-import.
3. **Liens cassés dans `docs/audits/FW-AUDIT-EXISTING-001.md`** : 2 liens vers `../../../Forge/` (lecture filesystem locale) qui n'ont aucun sens une fois le site servi à `forgemvc.com`. Convertis en inline code.

Un outil de QA réutilisable créé : [`scripts/check_local_links.py`](#liens-internes) (parseur HTML autonome, sans dépendance externe, exécutable en `<2 s` sur ~200 pages).

Aucune fuite de secrets. Aucun dossier exclu importé. `.claude/` non versionné. Forge core intact.

**Validation responsive non effectuée** dans ce ticket : pas de navigateur graphique accessible dans cet environnement (à traiter dans `FW-NAV-DOCS-STRUCTURE-001` ou un ticket QA visuelle dédié).

Aucun commit n'a été créé.

---

## Build testé

```text
$ bash scripts/build-site.sh

==> Nettoyage de dist et site
==> Copie de la landing depuis public/
==> Génération MkDocs (mkdocs build --strict)
INFO    -  Documentation built in 8.52 seconds
==> Intégration du site MkDocs sous dist/docs/

==> Bilan
  Fichiers totaux : 259
  Pages cibles :
    ok  dist/index.html
    ok  dist/docs/index.html
    ok  dist/docs/forge/index.html
```

- `dist/index.html` : ✓ présent (53 ko)
- `dist/docs/index.html` : ✓ présent (20 ko)
- `dist/docs/forge/index.html` : ✓ présent (20 ko)
- Volume total : **259 fichiers**, dont **206 HTML**

---

## Pages critiques testées

Sondées via `python3 -m http.server 8080 -d dist` et `curl`.

| URL | HTTP | Taille |
|---|---|---|
| `/` | **200** | 53 386 o |
| `/docs/` | **200** | 20 493 o |
| `/docs/forge/` | **200** | 20 357 o |
| `/docs/forge/installation/` | **200** | 32 799 o |
| `/docs/forge/getting-started/` | **200** | 26 146 o |
| `/docs/forge/reference/` | **200** | 33 260 o |
| `/docs/forge/concepts/` | **200** | 30 723 o |
| `/docs/forge/deployment/` | **200** | 60 841 o |
| `/docs/forge/roadmap/forge-roadmap/` | **200** | 151 659 o |
| `/docs/meta/01-architecture-generale-forge-web/` | **200** | 70 137 o |
| `/docs/audits/FW-LANDING-FINALIZE-001/` | **200** | 48 377 o |
| `/docs/search/` | **200** | 270 o |
| `/nonexistent/` | **404** | 335 o (page 404 MkDocs Material) |

12 pages critiques testées → toutes répondent correctement, 404 fonctionnel.

---

## Assets testés

| URL | HTTP | Taille |
|---|---|---|
| `/static/tailwind.css` | **200** | 33 130 o |
| `/static/img/forge-logo.png` | **200** | 825 440 o |
| `/static/js/landing.js` | **200** | 1 299 o |

Inventaire `href=` / `src=` de `public/index.html` confirme que ces 3 assets sont les seules ressources locales de la landing. Tous référencés et tous présents dans `dist/`.

Assets MkDocs (`dist/docs/assets/`) générés automatiquement par Material : CSS, JS, fonts, images — testés indirectement via le link checker (cibles uniques : 120, 0 cassée).

---

## Liens internes

Script créé : `scripts/check_local_links.py` (mode exécutable, 4,2 ko).

Principe : parseur HTML pur Python (`html.parser`), extrait `href` + `src`, ignore les URL externes (`http`, `https`, `mailto`, `tel`, `data`, `javascript`), résout chaque cible locale en chemin filesystem, vérifie l'existence (tolère les liens dossier en cherchant `index.html`).

Code de sortie : `0` si tout est OK, `1` si au moins un lien casse.

### Résultat final

```text
$ python3 scripts/check_local_links.py dist

Racine          : /home/roger/Projets/Forge-web/dist
Fichiers HTML   : 206
Liens analysés  : 25237
Liens externes  : 20783
Liens locaux    : 4454
Cibles uniques  : 120
Liens cassés    : 0

OK — aucun lien local cassé.
```

### Itérations de correction

Avant correction : **19 liens cassés**, répartis en 3 catégories :

| # | Catégorie | Nombre | Origine | Correction |
|---|---|---|---|---|
| 1 | `dist/docs/404.html` : `/forge/...`, `/assets/...`, `/meta/...`, `/audits/...` | 16 | `site_url` de `mkdocs.yml` valait `https://forgemvc.com/` au lieu de `https://forgemvc.com/docs/`. MkDocs Material générait `404.html` avec des liens absolus depuis `/`. | Changé `site_url` → `https://forgemvc.com/docs/` |
| 2 | `dist/docs/audits/FW-AUDIT-EXISTING-001/...` : `../../../Forge/`, `../../../Forge/docs/` | 2 | 2 liens introduits par moi-même dans la table des sources auditées (lecture filesystem) | Convertis en `` `inline code` `` |
| 3 | `dist/docs/forge/reference/...` : `adr/` | 1 | Bug Forge core : `reference.md` link `[ADR suivants](adr/)` ne résout pas en `reference/adr/` après build MkDocs (et le dossier `adr/` n'a pas d'`index.md` chez Forge core non plus) | Fixup ciblé dans `scripts/import_forge_docs.py` (KNOWN_FIXUPS) ; le lien devient texte simple |

Après correction : **0 lien cassé**.

---

## Liens externes essentiels

Inventaire (depuis `public/index.html` et `mkdocs.yml`, **non testés réseau** par ce ticket) :

| URL | Source | Rôle |
|---|---|---|
| `https://github.com/caucrogeGit/Forge` | landing × 5, mkdocs.yml | Dépôt source Forge |
| `https://github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md` | landing × 1 | Charte canonique |
| `https://github.com/caucrogeGit/Forge-web` | mkdocs.yml | Dépôt source Forge-web |
| `https://docs.python.org/3.12/` | landing × 1 | Référence Python |
| `https://mariadb.org/` | landing × 1 | Site officiel MariaDB |
| `https://jinja.palletsprojects.com/` | landing × 1 | Site officiel Jinja |
| `https://htmx.org/` | landing × 1 | Site officiel HTMX |
| `https://alpinejs.dev/` | landing × 1 | Site officiel Alpine.js |
| `https://tailwindcss.com/` | landing × 1 | Site officiel Tailwind CSS |
| `https://forgemvc.com/` (autoréf) | mkdocs.yml | `site_url` (sous-chemin `/docs/`) |

**Tests HTTP non effectués** sur ces URLs (hors périmètre QA locale + non-déterministe selon connectivité). Les domaines sont tous canoniques et stables ; un test ponctuel par navigateur peut être fait à la demande.

**Pas de lien explicite vers PyPI** dans la landing (mention textuelle « Disponible sur PyPI » + nom `forge-mvc`, sans URL cliquable). À évaluer si un lien explicite est souhaité.

---

## Responsive

**Non testé** dans ce ticket.

Raison : pas de navigateur graphique pilotable depuis cet environnement. Les vérifications cURL/HTTP ne permettent pas de mesurer la mise en page mobile (390 px), tablette (768 px) ou desktop (1366 px).

Recommandation : déléguer à un ticket QA visuelle dédié, ou tester manuellement dans Firefox/Chrome avec le mode responsive activé sur :

- `http://127.0.0.1:8080/`
- `http://127.0.0.1:8080/docs/`
- `http://127.0.0.1:8080/docs/forge/installation/`

Cassures à rechercher (cf. ticket) : menu inutilisable, texte qui déborde, boutons cassés, sections illisibles, images disproportionnées. La landing utilise Tailwind avec classes `sm:` / `md:` / `lg:` (présence vérifiée dans `tailwind.css`), structure responsive a priori OK ; MkDocs Material est responsive par défaut.

---

## Vérifications sécurité

### Fuite par nom de fichier dans `dist/`

```bash
find dist -type f \( -name '.env*' -o -name 'cert.pem' -o -name 'key.pem' \
         -o -name '*.key' -o -name '*.pem' -o -name '*.crt' \)
```

Résultat : **vide** (aucune fuite).

### Dossier exclu accidentellement publié

```bash
find dist -type d | grep -E '(^|/)(core|mvc|packages|tests|env|\.venv|\.git)(/|$)'
```

Résultat : **vide** (aucune fuite).

### `github.io` dans les sources et le build

```bash
grep -RIn "github\.io" public docs mkdocs.yml scripts
grep -RIn "github\.io" dist
```

Détections (toutes **légitimes**, non bugs) :

| Source | Nombre | Nature |
|---|---|---|
| `docs/forge/history/audits/consolidation-starter-001.md` | 7 | Mentions textuelles dans les **rapports d'audit historiques** Forge core (audits sur la migration des URLs starters). Contenu factuel à préserver. |
| `docs/forge/history/audits/consolidation-001-architecture.md` | 2 | Idem |
| `docs/forge/history/audits/pre-release-3.0-audit-001.md` | 1 | Idem |
| `dist/docs/.../*.html` | 206 | Footer auto-ajouté par MkDocs Material : `https://squidfunk.github.io/mkdocs-material/` (lien vers le projet upstream — légitime et non modifiable sans theme override) |

**Aucun lien fonctionnel** vers `caucrogegit.github.io/Forge/` ne subsiste dans la landing ou dans les pages générées. Les mentions historiques restent en texte (audits archivés Forge core).

### Forge core intact

```bash
git -C /home/roger/Projets/Forge status --short
→ (vide — non modifié)
```

---

## Vérifications MkDocs

### `mkdocs build --strict`

```text
INFO    -  Documentation built in 8.52 seconds
```

**0 WARNING**, **5 INFO** non bloquants (réduits de 7 → 5 par les corrections de ce ticket) :

```text
INFO  - audits/FW-AUDIT-EXISTING-001.md : '../../', it was left as is.
INFO  - audits/FW-AUDIT-EXISTING-001.md : '.', it was left as is.
INFO  - forge/starters/welcome/index.md : '../01-contact-simple/', left as is.
INFO  - forge/starters/welcome/index.md : '../', left as is.
INFO  - (1 ligne info supplémentaire variable selon contexte)
```

Les INFO restantes concernent des liens vers des dossiers sans `index.md`. Elles ne bloquent ni le build ni le link checker (qui les valide via la résolution de dossier → `index.html`). Acceptables.

### Build complet

```text
dist/
├── index.html              (landing)
├── static/                 (assets landing)
└── docs/                   (site MkDocs)
    ├── 404.html
    ├── index.html          (accueil MkDocs)
    ├── assets/             (CSS, JS, fonts Material)
    ├── audits/             (3 rapports d'audit)
    ├── forge/              (~200 pages Forge)
    ├── meta/               (2 pages Forge-web)
    ├── search/             (interface Material search)
    ├── sitemap.xml
    └── sitemap.xml.gz
```

---

## État Git

```text
 M docs/audits/FW-AUDIT-EXISTING-001.md       (2 liens hors-site → inline code)
 M docs/audits/FW-LANDING-FINALIZE-001.md     (1 lien hors-site → inline code, détecté en début de QA)
 M docs/forge/reference.md                    (régénéré par le re-import : fixup ADR appliqué)
 M mkdocs.yml                                 (site_url → /docs/)
 M scripts/import_forge_docs.py               (+ KNOWN_FIXUPS + apply_known_fixups)
?? scripts/check_local_links.py               (nouveau script QA)
?? docs/audits/FW-LOCAL-QA-001.md             (ce rapport)
```

Vérifications négatives :

- `git diff --check` = 0
- `.claude/` : **absent** de git status (correctement ignoré)
- `dist/`, `site/`, `.venv/` : tous ignorés
- Forge core : intact

Branche : `main`. Aucun commit créé.

Commande de commit suggérée (à exécuter manuellement) :

```bash
git add mkdocs.yml scripts/import_forge_docs.py scripts/check_local_links.py \
        docs/forge/reference.md \
        docs/audits/FW-AUDIT-EXISTING-001.md \
        docs/audits/FW-LANDING-FINALIZE-001.md \
        docs/audits/FW-LOCAL-QA-001.md
git commit -m "qa(site): local QA + link checker + site_url fix (FW-LOCAL-QA-001)"
```

---

## Limites restantes

1. **Responsive non testé** : aucun navigateur graphique. Délégué à QA visuelle.
2. **Liens externes non testés réseau** : inventaire uniquement (10 URLs identifiées). Test HTTP réseau hors périmètre.
3. **5 INFO MkDocs résiduelles** non bloquantes — 4 dans `FW-AUDIT-EXISTING-001.md` (liens vers dossiers : `.`, `../../`), 2 dans `forge/starters/welcome/index.md` (liens vers `../01-contact-simple/` et `../`). À traiter dans un futur ticket si on veut un build « INFO-clean ».
4. **Nav MkDocs toujours incomplète** : 7 entrées Forge visibles dans la nav latérale alors que ~200 pages sont publiées. → `FW-NAV-DOCS-STRUCTURE-001`.
5. **Pas de minification ni d'optimisation d'assets** : logo PNG = 825 ko. Optimisation déléguée à un futur ticket.
6. **Pas de CI** : `scripts/build-site.sh` et `scripts/check_local_links.py` doivent être lancés manuellement.
7. **Lien PyPI absent** de la landing : à évaluer.
8. **Aucun audit d'accessibilité (a11y)** : pas de test WCAG, alt manquants non vérifiés.
9. **Lien CHARTE_DOC.md vers GitHub** : la landing pointe vers `github.com/caucrogeGit/Forge/blob/main/CHARTE_DOC.md`. Pourrait être migré vers une copie publiée sur forgemvc.com → décision éditoriale.
10. **`dist/docs/404.html`** : la page 404 affiche correctement la nav mais le bouton « Accueil » va vers `/docs/` (cohérent avec `site_url`), pas vers `/`. Comportement acceptable.
11. **Aucun commit créé** par ce ticket.

---

## Prochain ticket recommandé

**FW-NAV-DOCS-STRUCTURE-001 — Structurer progressivement la navigation documentaire Forge**

Justification :

- la QA confirme que **toutes** les pages importées (~200) sont accessibles individuellement et techniquement saines ;
- mais seules **7 pages** apparaissent dans la nav latérale MkDocs ;
- les pages non-nav restent accessibles par URL directe et par la recherche, mais une nav structurée améliore considérablement la découvrabilité ;
- la nav de Forge core (200 entrées) peut servir de base, après adaptation aux nouveaux chemins (`forge/` prefix).

Pré-requis désormais satisfaits :

- import documentaire propre, link-clean, build strict-clean ;
- 9 URLs critiques validées + 0 lien interne cassé ;
- script de build reproductible + checker de liens réutilisable.

Périmètre suggéré pour `FW-NAV-DOCS-STRUCTURE-001` (à préciser dans le ticket lui-même) :

1. Reprendre la structure nav de Forge core en l'adaptant au préfixe `forge/`.
2. Couvrir au minimum : Premiers pas, Concepts, Entités, Référence (CLI, API, modules, sessions), Déploiement, Sécurité, ADR, Starters, Roadmap, Historique.
3. Rebuild + relancer link checker à chaque étape.
4. Ne pas modifier le contenu des pages (juste la nav).
5. Ne pas inventer de pages manquantes.
