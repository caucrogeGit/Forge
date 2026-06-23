# Préparation à la publication

> Cette page documente l'état de préparation du site Forge-official-site avant déploiement
> sur la VM web. Elle ne décrit pas la procédure de déploiement elle-même : tant
> que la VM, le DNS et le reverse proxy ne sont pas en place, le site reste local.

## Structure de publication

Le site est généré localement par [`scripts/build-site.sh`](#build-local) sous la forme :

```text
dist/
├── index.html                  → servi à /
├── static/                     → servi à /static/
│   ├── tailwind.css
│   ├── img/forge-logo.png
│   └── js/landing.js
├── robots.txt                  → servi à /robots.txt
├── sitemap.xml                 → servi à /sitemap.xml (sitemap manuel)
└── docs/                       → servi à /docs/
    ├── index.html              → /docs/
    ├── 404.html                → page 404 MkDocs Material
    ├── assets/                 → JS/CSS/fonts Material
    ├── forge/                  → documentation Forge importée
    ├── meta/                   → docs internes Forge-official-site
    ├── audits/                 → rapports d'audit
    ├── search/                 → interface de recherche Material
    ├── sitemap.xml             → sitemap MkDocs (généré, pages /docs/*)
    └── sitemap.xml.gz
```

Le serveur cible devra servir ce dossier `dist/` statiquement, sans transformation.

## Build local

Commande unique, reproductible :

```bash
bash scripts/build-site.sh
```

Ce script :

1. Active le venv local (`.venv/`) s'il existe ;
2. Vérifie la présence de `mkdocs` ;
3. Supprime `dist/` et `site/` ;
4. Copie `public/` (landing + assets + robots + sitemap) vers `dist/` ;
5. Lance `mkdocs build --strict` (produit `site/`) ;
6. Intègre `site/` sous `dist/docs/`.

Validation associée :

```bash
python scripts/check_local_links.py dist
```

Doit retourner « `OK — aucun lien local cassé.` »

## Fichiers à copier vers le serveur

Lorsque la VM sera prête, seul `dist/` doit être copié. Aucun autre fichier
de ce dépôt n'est nécessaire à l'exécution du site.

À **ne jamais** envoyer sur la VM web :

- `.venv/`
- `node_modules/`
- `.git/`
- `scripts/` (ce sont des outils de génération côté développement)
- `src/`, `tests/`, `docs/` sources Markdown
- `.env*`, `*.pem`, `*.key`
- `.claude/`, `.vscode/`

Méthode recommandée plus tard (à valider en `FW-DEPLOY-GO-001`) :

```bash
rsync -av --delete dist/ user@vm:/var/www/forgemvc.com/
```

## Hypothèse Caddy

Le reverse proxy retenu en première phase est **Caddy**. Configuration
attendue (à formaliser en `FW-CADDY-STATIC-SITE-001`) :

```caddy
forgemvc.com, www.forgemvc.com {
    root * /var/www/forgemvc.com
    file_server
    encode gzip zstd

    redir https://forgemvc.com{uri} permanent {
        if {host} == "www.forgemvc.com"
    }

    log {
        output file /var/log/caddy/forgemvc.com.access.log
    }
}
```

Caddy gérera automatiquement HTTPS via Let's Encrypt.

## Ports publics futurs

Seuls deux ports doivent être ouverts à Internet :

| Port | Protocole | Rôle |
|---|---|---|
| 80 | TCP | HTTP (redirection vers HTTPS + challenges ACME) |
| 443 | TCP | HTTPS (site servi) |

À **ne pas** exposer publiquement :

- `22` SSH direct (passer par Tailscale/VPN ou whitelist IP)
- `8006` interface Proxmox
- `25`, `587`, `993` SMTP/IMAPS (mail reporté)
- `3306`, `5432`, `6379` bases de données

## DNS pas encore modifié

Aucune entrée DNS n'a été activée pour ce ticket. Les configurations
minimales attendues (à appliquer en `FW-DNS-WEB-001`) :

```text
A      forgemvc.com       → <IP publique VM>
CNAME  www.forgemvc.com   → forgemvc.com
```

Pas de DNSSEC, pas de CAA, pas d'enregistrement MX (mail reporté), tant que
le site n'est pas servi en HTTPS stable.

## Déploiement pas encore effectué

À ce stade, **aucun déploiement réel** n'a été lancé :

- la VM web cible n'est pas auditée (→ `FW-SERVER-TARGET-AUDIT-001`) ;
- aucune configuration Caddy n'est livrée (→ `FW-CADDY-STATIC-SITE-001`) ;
- aucun DNS n'est modifié (→ `FW-DNS-WEB-001`) ;
- aucun port n'est ouvert sur la box ;
- Proxmox reste hors d'Internet.

Le `dist/` reste un artefact local jusqu'à validation explicite de chacune
de ces étapes.

## Logs et statistiques

**Décision actée** :

- **Aucun Google Analytics** au lancement.
- **Aucun tracker JavaScript** tiers.
- **Aucun cookie de tracking** ni bannière de consentement (donc rien à
  consentir, conforme RGPD par construction).
- Première source de mesure : **les access logs Caddy**.
- À moyen terme : **GoAccess** pour produire un rapport statistique HTML local
  à partir des logs Caddy, sans envoyer aucune donnée à un tiers.

Justifications :

- privilégier la simplicité et la confidentialité au démarrage ;
- éviter d'ajouter un payload JS public avant que le site ne soit stable ;
- ne pas créer d'obligation RGPD avant d'avoir un vrai besoin analytique ;
- conserver la souveraineté des données utilisateurs visiteurs.

À traiter dans un ticket dédié :

```text
FW-ACCESS-LOGS-STATS-001 — Mettre en place les logs d'accès et statistiques simples
```

Périmètre suggéré pour ce futur ticket :

1. format des access logs Caddy (combined / json) ;
2. rotation des logs (`logrotate`) ;
3. rétention des logs (durée à décider) ;
4. mise en place de GoAccess en mode batch quotidien ;
5. publication éventuelle du rapport HTML sur `/stats/` derrière basic-auth ;
6. décision sur l'anonymisation des IP (truncate au /24 / /48).

## Conventions de référencement

Les pages-clés exposées dans `sitemap.xml` (manuel, racine du site) :

- `/` (landing)
- `/docs/` (accueil documentation Forge-official-site)
- `/docs/forge/` (accueil Forge)
- `/docs/forge/installation/`
- `/docs/forge/getting-started/`
- `/docs/forge/reference/`
- `/docs/forge/charter/`

Le sitemap MkDocs étendu (toutes les pages indexées) est par ailleurs généré
automatiquement à `/docs/sitemap.xml`. Les robots peuvent crawler les deux.

Le fichier `robots.txt` est ouvert :

```text
User-agent: *
Allow: /
Sitemap: https://forgemvc.com/sitemap.xml
```

Aucune section privée n'est servie publiquement.

## État du `dist/` local

À chaque ré-exécution de `bash scripts/build-site.sh` :

- ~260 fichiers générés ;
- 209 pages HTML ;
- 0 lien local cassé (validé par `scripts/check_local_links.py`) ;
- 0 warning MkDocs en mode `--strict` ;
- les 6 paquets PyPI Forge (`forge-mvc`, `-stats`, `-rbac`, `-workflow`, `-media`,
  `-mfa`) ont été vérifiés présents en `1.0.0b8` au moment du dernier audit
  (voir `scripts/check_pypi_packages.py`).
