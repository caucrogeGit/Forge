# Déploiement avancé Forge

Ce guide couvre le déploiement complet d'une application Forge en production :
préparation du projet, configuration serveur, cycle de mise à jour et validation.

!!! tip "Guides complémentaires"
    - [Déploiement](deployment.md) — commandes `forge deploy:init` / `forge deploy:check` et fichiers générés.
    - [Sécurité en production](production-security.md) — cookies, headers, CSRF, RBAC, uploads, checklist sécurité complète.

---

## Objectif

Déployer une application Forge de façon explicite, maîtrisée et reproductible.

Principes fondamentaux :

```text
Forge ne doit pas être exposé directement sans reverse proxy.
HTTPS doit être terminé par Nginx ou équivalent.
Les secrets doivent rester hors Git.
storage/ ne doit jamais être exposé directement.
```

---

## Architecture cible

```text
Internet (HTTPS :443)
    ↓  TLS terminé par Nginx
Nginx (reverse proxy)
    ↓  HTTP local :8000
Forge app.py via systemd
    ↓  SQL
MariaDB (:3306)
    ↓  fichiers
storage/uploads/
```

| Couche | Rôle |
|---|---|
| Nginx | Termine TLS, compresse, applique les headers de sécurité, sert les fichiers statiques optionnellement |
| Forge (systemd) | Exécute la logique MVC, génère les réponses HTML, contrôle les accès aux uploads |
| MariaDB | Persiste les données applicatives |
| `storage/uploads/` | Stocke les fichiers uploadés — jamais exposé directement |

---

## Prérequis serveur

- **OS** : Debian 12 ou Ubuntu 22.04+ recommandé
- **Python** : {{python_min}} ou plus (`python3 --version`)
- **MariaDB** : 10.11 LTS ou plus
- **Nginx** : version récente (`nginx -v`)
- **systemd** : présent sur Debian/Ubuntu
- **Utilisateur applicatif** : un utilisateur système dédié, sans sudo (ex. `forge`)
- **Accès SSH** : clé SSH, pas de mot de passe
- **Certificat TLS** : Let's Encrypt via Certbot ou certificat commercial

---

## Préparer le projet

Avant tout déploiement, le projet doit passer tous les contrôles locaux.
Un projet qui échoue ces contrôles ne doit pas être déployé.

```bash
forge project:check
forge project:audit
pytest
python -m compileall -q .
ruff check .
git diff --check
```

Générer les fichiers de déploiement :

```bash
forge deploy:init
```

Vérifier l'environnement cible :

```bash
forge deploy:check
```

`forge deploy:check` vérifie Python, les variables DB, le module `mariadb`,
les dossiers `storage/` et les fichiers `deploy/` générés. La commande échoue
si une erreur bloquante est détectée.

---

## Variables d'environnement

### Créer `env/prod`

```bash
cp env/example env/prod
chmod 640 env/prod
```

Éditez `env/prod` avec les valeurs de production :

```dotenv
APP_NAME=MonApplication
APP_ROUTES_MODULE=mvc.routes

# Base applicative
DB_NAME=mon_app_db
DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=mon_app_user
DB_APP_PWD=<mot_de_passe_fort>

# Base admin (uniquement pour db:init / db:apply)
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=<mot_de_passe_root>

# Serveur
APP_HOST=127.0.0.1
APP_PORT=8000
APP_SSL_ENABLED=false       # Nginx termine HTTPS, Forge écoute en HTTP local

# Stockage
UPLOAD_ROOT=storage/uploads
UPLOAD_MAX_SIZE=5242880     # 5 Mo
```

### Règles de sécurité

- `env/prod` ne doit **jamais** être versionné dans Git
- Vérifiez que `.gitignore` contient `env/prod`
- Permissions : `640` (propriétaire = utilisateur applicatif, groupe = www-data ou équivalent)
- Les credentials admin (`DB_ADMIN_*`) servent uniquement lors des migrations — les supprimer de `env/prod` après `db:init` si vous n'en avez plus besoin

---

## Base MariaDB

### Créer la base et l'utilisateur

```sql
-- Connecté en root MariaDB
CREATE DATABASE mon_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mon_app_user'@'localhost' IDENTIFIED BY 'mot_de_passe_fort';
GRANT SELECT, INSERT, UPDATE, DELETE ON mon_app_db.* TO 'mon_app_user'@'localhost';
FLUSH PRIVILEGES;
```

L'utilisateur applicatif (`mon_app_user`) n'a que les droits nécessaires à
l'application. Il ne peut pas `CREATE TABLE`, `DROP TABLE` ni accéder à
d'autres bases.

### Initialiser les tables

```bash
forge db:init
```

N'exécutez `forge db:init` **qu'une seule fois** par environnement. Cette
commande crée les tables depuis les fichiers `.sql` des entités.

Pour les migrations ultérieures :

```bash
# Toujours sauvegarder avant
mysqldump -u root -p mon_app_db > backup_avant_migration_$(date +%Y%m%d).sql
forge db:apply
```

!!! danger "Ne jamais tester sur la base de production"
    Utilisez un environnement de staging distinct avec une base séparée pour
    valider les migrations avant de les appliquer en production.

---

## Service systemd

Le fichier `deploy/systemd/forge-app.service` est généré par `forge deploy:init`.
Adaptez-le avant installation :

```ini
[Unit]
Description=Forge Application — MonApplication
After=network.target mariadb.service

[Service]
Type=simple
User=forge
Group=forge
WorkingDirectory=/srv/forge/mon_app
ExecStart=/srv/forge/mon_app/.venv/bin/python /srv/forge/mon_app/app.py --env prod
Restart=on-failure
RestartSec=5
EnvironmentFile=/srv/forge/mon_app/env/prod

# Journalisation
StandardOutput=journal
StandardError=journal
SyslogIdentifier=forge-mon-app

[Install]
WantedBy=multi-user.target
```

### Installation et activation

```bash
sudo cp deploy/systemd/forge-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable forge-app
sudo systemctl start forge-app
sudo systemctl status forge-app
```

### Commandes utiles

```bash
sudo systemctl status forge-app        # état du service
sudo systemctl restart forge-app       # redémarrer
sudo journalctl -u forge-app -n 50     # 50 dernières lignes de logs
sudo journalctl -u forge-app -f        # logs en temps réel
```

---

## Reverse proxy HTTPS

Le fichier `deploy/nginx/forge-app.conf` est généré par `forge deploy:init`.
Adaptez le `server_name` et ajoutez TLS :

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    # Certificat TLS
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Taille max upload (adapter à UPLOAD_MAX_SIZE + marge)
    client_max_body_size 6m;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Proxy vers Forge
    location / {
        proxy_pass          http://127.0.0.1:8000;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Real-IP         $remote_addr;
        proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto https;
        proxy_http_version  1.1;
        proxy_read_timeout  30s;
    }
}
```

### Installation

```bash
sudo cp deploy/nginx/forge-app.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/forge-app.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### HSTS

L'en-tête `Strict-Transport-Security` indique aux navigateurs de n'utiliser
que HTTPS pour ce domaine. Activez-le uniquement quand HTTPS est stable et
opérationnel — retirez-le temporairement lors d'une migration de domaine.

---

## Fichiers statiques

Forge sert le dossier `static/` par défaut. En production, deux stratégies :

### Stratégie A — Forge sert `static/`

Aucune configuration supplémentaire. Nginx relaie toutes les requêtes vers Forge.
Convient aux projets à faible trafic.

### Stratégie B — Nginx sert `static/` directement

```nginx
location /static/ {
    alias /srv/forge/mon_app/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

Convient aux projets à trafic élevé — Nginx sert les fichiers statiques sans
passer par Python.

!!! danger "Ne jamais exposer le projet brut"
    Ne configurez pas Nginx pour servir `/srv/forge/mon_app/` directement.
    Les chemins `env/`, `storage/logs/`, `.git/` ou les fichiers `.py`
    ne doivent jamais être accessibles depuis Internet.

---

## Uploads et médias

Les fichiers uploadés sont stockés dans `storage/uploads/` (configurable via
`UPLOAD_ROOT` dans `env/prod`).

### Règles fondamentales

- `storage/uploads/` n'est **jamais** exposé directement par Nginx
- Les téléchargements passent par une route Forge contrôlée (`/media/...`)
- Forge applique une validation 3 couches : extension → MIME → taille
- Les noms de fichiers sont sécurisés via `secure_filename` + UUID

### Vérifier les permissions

```bash
chown -R forge:forge storage/uploads/
chmod 750 storage/
chmod 750 storage/uploads/
```

### Sauvegarder les uploads

```bash
# Sauvegarde quotidienne des uploads
rsync -az /srv/forge/mon_app/storage/uploads/ /backup/mon_app/uploads/$(date +%Y%m%d)/
```

---

## Logs

### Logs systemd (journald)

```bash
# Logs du service
sudo journalctl -u forge-app
sudo journalctl -u forge-app --since "2026-01-01" --until "2026-01-02"
sudo journalctl -u forge-app -n 100 --no-pager
```

### Logs runtime Forge

Forge écrit des logs de diagnostic dans `storage/logs/` :

- `errors.dev.jsonl` — erreurs structurées JSON
- `errors.dev.md` — rapport lisible

!!! warning "Logs en production"
    Ces fichiers sont conçus pour le développement. En production :
    - Ne les exposez pas via Nginx
    - Ne les lisez pas comme source de vérité opérationnelle
    - Préférez `journalctl` pour la supervision

### Protéger `storage/logs/`

`storage/` ne doit pas être accessible via Nginx. Si vous avez ajouté un
alias `storage/`, retirez-le. Vérifiez avec :

```bash
curl -I https://example.com/storage/logs/errors.dev.jsonl
# Attendu : 404 ou connexion refusée — jamais 200
```

---

## Sécurité production

Les garanties de sécurité de Forge sont documentées dans
[Sécurité en production](production-security.md) :

- CSRF actif sur toutes les routes POST non explicitement opt-out
- Cookies `HttpOnly`, `SameSite=Strict`, `Secure` (activé automatiquement quand `X-Forwarded-Proto: https`)
- Headers HTTP de sécurité (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP)
- RBAC serveur — refus par défaut pour les anonymes
- Uploads filtrés (extension, MIME, taille)
- Secrets hors Git

Consultez la [checklist de sécurité complète](production-security.md) avant toute mise en production.

---

## Sauvegardes

### Base de données

```bash
# Sauvegarde complète
mysqldump -u root -p mon_app_db > /backup/mon_app/db/mon_app_$(date +%Y%m%d_%H%M).sql
gzip /backup/mon_app/db/mon_app_$(date +%Y%m%d_%H%M).sql

# Vérifier la sauvegarde
ls -lh /backup/mon_app/db/
```

Planifiez une sauvegarde automatique via cron :

```bash
# /etc/cron.d/mon-app-backup
0 3 * * * forge mysqldump -u root -p<pwd> mon_app_db | gzip > /backup/mon_app/db/daily_$(date +\%Y\%m\%d).sql.gz
```

### Uploads

```bash
rsync -az /srv/forge/mon_app/storage/uploads/ /backup/mon_app/uploads/
```

### Configuration

```bash
# Sauvegarder env/prod hors dépôt Git
cp /srv/forge/mon_app/env/prod /backup/mon_app/config/env_prod_$(date +%Y%m%d)
```

### Tester la restauration

Une sauvegarde non testée n'est pas une sauvegarde. Testez périodiquement la
restauration dans un environnement isolé.

---

## Mise à jour applicative

Cycle de mise à jour recommandé :

```bash
# 1. Sauvegarder
mysqldump -u root -p mon_app_db > /backup/mon_app/db/avant_maj_$(date +%Y%m%d).sql

# 2. Récupérer le code
git pull

# 3. Mettre à jour les dépendances
source .venv/bin/activate
pip install -r requirements.txt

# 4. Vérifier le projet
forge project:check
forge project:audit
pytest
python -m compileall -q .

# 5. Appliquer les migrations SQL si nécessaire
forge db:apply

# 6. Redémarrer le service
sudo systemctl restart forge-app

# 7. Vérifier
sudo systemctl status forge-app
sudo journalctl -u forge-app -n 20
```

!!! warning "Avant de passer à une version majeure"
    Consultez le [Guide de migration](migration-guide.md) et la
    [Matrice de compatibilité](compatibility.md) avant toute mise à jour majeure.

---

## Validation post-déploiement

```text
- [ ] Service systemd actif (systemctl status forge-app)
- [ ] HTTPS actif (certificat valide, redirection HTTP → HTTPS)
- [ ] HSTS présent dans les headers (curl -I https://example.com)
- [ ] Cookies Secure présents (onglet DevTools → Application → Cookies)
- [ ] Headers X-Content-Type-Options et X-Frame-Options présents
- [ ] Page d'accueil accessible
- [ ] Login fonctionnel (si auth utilisée)
- [ ] Upload fonctionnel (si utilisé)
- [ ] storage/logs/ non accessible via navigateur (retourne 404)
- [ ] storage/uploads/ non accessible directement via navigateur (retourne 404)
- [ ] env/prod non versionné (git status ne montre pas env/prod)
- [ ] Sauvegarde DB planifiée et testée
- [ ] Sauvegarde uploads planifiée
```

Vérifier les headers depuis l'extérieur :

```bash
curl -I https://example.com/
# Doit montrer : Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options
```

---

## Dépannage

### Le service ne démarre pas

```bash
sudo journalctl -u forge-app -n 50
# Chercher : ImportError, ModuleNotFoundError, FileNotFoundError, PermissionError
```

Causes fréquentes :
- Chemin incorrect dans `ExecStart` ou `WorkingDirectory`
- `env/prod` absent ou mal formaté
- Dépendances Python manquantes (`pip install -r requirements.txt`)
- Permissions incorrectes sur `storage/`

### Erreur 502 Bad Gateway

Nginx ne peut pas joindre Forge. Vérifiez :

```bash
sudo systemctl status forge-app    # service actif ?
curl http://127.0.0.1:8000/        # Forge répond en local ?
```

Causes fréquentes :
- Service forge-app arrêté ou crashé
- Port incorrect dans `proxy_pass`
- Forge démarre mais crash immédiatement (voir `journalctl`)

### Permission denied sur `storage/`

```bash
ls -la storage/
chown -R forge:forge storage/
chmod 750 storage/
chmod 750 storage/uploads/
chmod 750 storage/logs/
```

### Cookies non envoyés (session perdue)

Vérifiez que Nginx transmet `X-Forwarded-Proto: https`. Forge active
`Secure` sur les cookies uniquement quand ce header est présent.

```nginx
proxy_set_header X-Forwarded-Proto https;
```

### Upload impossible

Causes fréquentes :
- `client_max_body_size` trop petit dans Nginx (doit être ≥ `UPLOAD_MAX_SIZE` + marge)
- Permissions insuffisantes sur `storage/uploads/`
- `UPLOAD_ROOT` absent ou incorrect dans `env/prod`

```bash
# Vérifier
grep UPLOAD_ROOT env/prod
ls -la storage/uploads/
grep client_max_body_size /etc/nginx/sites-available/forge-app.conf
```

### Logs introuvables

```bash
# Logs systemd
sudo journalctl -u forge-app --since today

# Logs runtime (si le dossier existe)
ls -la storage/logs/
```

Si `storage/logs/` est vide, Forge n'a pas encore rencontré d'erreur ou le
dossier n'a pas les permissions correctes.

---

## Limites actuelles

| Limite | État |
|---|---|
| Sessions mémoire par défaut | `MemorySessionStore` — perdues au redémarrage. Voir backends fichier ou MariaDB dans [Déploiement](deployment.md). |
| Pas de supervision intégrée | Utilisez systemd + Prometheus/Grafana ou équivalent externe |
| Pas de rollback automatique | Gérez les rollbacks manuellement (git checkout + restauration DB) |
| SQL versionné absent | Pas de migration versionnée automatique — gérez les scripts SQL manuellement |
| Dettes de sécurité connues | `SECURITY-CACHE-001`, `CRUD-RBAC-UI-001`, `E2E-UPLOAD-HTTP-001`, `SECURITY-UPLOAD-RATE-LIMIT-001` — voir [Sécurité en production](production-security.md) |

---

## Voir aussi

- [Déploiement](deployment.md) — `forge deploy:init`, `forge deploy:check`, fichiers générés
- [Sécurité en production](production-security.md) — checklist sécurité complète
- [Guide de migration](migration-guide.md) — cycle de mise à jour entre versions
- [Matrice de compatibilité](compatibility.md) — Python, MariaDB, dépendances
- [Contrat de stabilité](stability-contract.md) — fichiers garantis préservés
