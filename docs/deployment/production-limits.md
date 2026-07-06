# Limites de production

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page synthétise les limites de production connues de Forge pour la série `1.0`.
Elle complète les pages [Mise en production pas à pas](mise-en-production.md), [Guide de déploiement](deployment.md), [Déploiement WSGI minimal](wsgi-deployment.md) et [Sécurité en production](production-security.md).

!!! warning "Forge 1.0 n'est pas une plateforme de production clé en main"
    La série 1.0 a livré l'entrée WSGI configurée, la résolution sécurisée de `X-Real-IP`, et les avertissements production au démarrage.
    **Forge ne prétend pas encore fournir** une orchestration multi-worker distribuée, des sessions partagées, ni un guide d'exploitation haute disponibilité complet.
    Cette page liste ce qui est utilisable, ce qui est acceptable avec précaution, et ce qui reste explicitement à cadrer côté infrastructure.

---

## 1. Niveaux d'utilisation

| Niveau | Description | Chemin recommandé |
|---|---|---|
| **Développement** | code local, hot reload manuel, démos | `python app.py` |
| **Test / démo** | smoke tests, environnements éphémères | `python app.py` ou WSGI |
| **Production encadrée** | exposition derrière reverse proxy, charge modérée | `create_configured_wsgi_app()` + Gunicorn + reverse proxy |
| **Production publique sérieuse** | charge forte, multi-instance, HA | nécessite cadrage explicite hors Forge (cf §7-8) |

---

## 2. Tableau synthétique

| Domaine | État 1.0 | Recommandation |
|---|---|---|
| Serveur HTTP direct | Développement uniquement | Ne pas exposer `python app.py` publiquement |
| WSGI | Chemin recommandé | Utiliser `create_configured_wsgi_app()` |
| Reverse proxy | Requis en production | Caddy ou Nginx devant Gunicorn |
| HTTPS | Hors Forge | Terminer TLS côté reverse proxy |
| IP client | Support `X-Real-IP` sécurisé | Configurer `APP_TRUSTED_PROXIES` |
| Sessions par défaut | `MemorySessionStore` non persistant | Éviter en production (warning émis au démarrage) |
| Sessions persistantes | `FileSessionStore`, `MariaDbSessionStore` | À configurer explicitement |
| Rate-limits login / upload | Compteurs en mémoire mono-process | Non partagés entre workers |
| Anti-rejeu MFA (TOTP) | État en mémoire mono-process | Code TOTP rejouable sur un autre worker |
| Fichiers statiques (`/static/...`) | Servis par Forge | À déléguer au reverse proxy |
| Médias (`/media/...`) | Servis par Forge avec garde-fous | À cadrer selon l'application |
| Multi-worker | Compatible côté dispatch WSGI | Stores mémoire non partagés (cf §7) |

---

## 3. `python app.py` n'est pas pour la production publique

`python app.py` lance un `ThreadingHTTPServer` Python pur, conçu pour le développement et les démonstrations.
Il :

- ne gère pas correctement la concurrence à grande échelle ;
- n'optimise pas les keep-alive ni les timeouts réseau ;
- ne propose pas de gestion fine du cycle de vie des workers ;
- ne compresse pas, ne cache pas, ne sert pas les statiques efficacement.

**Pour une exposition publique**, utiliser le chemin WSGI documenté dans [Déploiement WSGI minimal](wsgi-deployment.md) (Gunicorn + Caddy/Nginx).

---

## 4. Sessions et rate-limits

### Sessions

- `MemorySessionStore` (défaut) : **volatile**, toutes les sessions sont perdues au redémarrage.
  **Mono-processus**, incompatible avec un déploiement multi-worker.
- `FileSessionStore` : persistance basique sur disque.
  Utilisable en mono-worker.
  En multi-worker, le verrou n'est pas strict ; à éviter pour des charges concurrentes élevées.
- `MariaDbSessionStore` : persistance et partage entre workers.
  C'est le choix le plus robuste actuellement disponible côté Forge.

Sélection explicite via `forge.configure(session_store=...)` ou [ADR-002](../adr/002-session-strategy.md).

### Rate-limits et anti-rejeu MFA

- Le rate-limit login (`core.auth.rate_limit`) et le rate-limit upload (module d'upload optionnel) stockent leurs compteurs **en mémoire dans le processus courant**.
  Cette implémentation n'est pas configurable dans la série 1.0.0.
- En multi-worker, **les compteurs ne sont pas partagés**, la protection reste utile localement mais n'est pas une défense distribuée.
- Forge n'embarque ni Redis ni autre backend distribué pour ces compteurs.
- L'anti-rejeu TOTP de `forge-mvc-mfa` (qui empêche de rejouer un code à six chiffres déjà consommé dans sa fenêtre de validité) stocke aussi son état **en mémoire par processus**.
  En multi-worker, un code TOTP intercepté peut être rejoué sur un autre worker que celui qui l'a consommé.

### Avertissement automatique

`create_configured_wsgi_app()` émet **une fois au démarrage** (et jamais par requête) un avertissement si `APP_ENV=prod` avec un session store mémoire, voir [Déploiement WSGI § warnings](wsgi-deployment.md#6-warnings-production-au-demarrage).
Cet avertissement signale le risque, il ne le corrige pas.

---

## 5. Reverse proxy et IP client

Forge n'honore `X-Real-IP` que si l'IP du socket appartient à la liste explicite `APP_TRUSTED_PROXIES`.
Règles :

- `APP_TRUSTED_PROXIES` est **vide par défaut** → `X-Real-IP` est ignoré ;
- liste séparée par virgules, espaces tolérés ;
- comparaison **IP exacte**, pas de notation CIDR ;
- pas de wildcard ; `0.0.0.0` n'a aucune signification particulière ;
- `X-Real-IP` invalide → fallback sur l'IP du socket ;
- **`X-Forwarded-For` n'est pas supporté** dans la série 1.0.0.

Détail et exemples : [Déploiement WSGI § APP_TRUSTED_PROXIES](wsgi-deployment.md#5-app_trusted_proxies-et-x-real-ip).

---

## 6. Fichiers statiques et médias

- **Statiques (`/static/...`)** : Forge sait les servir (cf `app.py:RequestHandler._serve_static`), mais ce dispatch traverse la pile Python complète.
  En production, faire servir directement par le reverse proxy, plus rapide, plus sûr, et libère Gunicorn pour le métier.
- **Médias (`/media/...`)** : Forge expose `serve_media_file` avec des garde-fous path traversal.
  Le périmètre exact reste **à cadrer côté application** selon la sensibilité des fichiers (public/privé, droits, ACL).
  Ne pas exposer un dossier arbitraire derrière une route Forge sans contrôle d'accès explicite.

---

## 7. Multi-worker

Un déploiement Gunicorn multi-worker (`--workers N > 1`) **fonctionne** côté dispatch WSGI : chaque worker construit son `Application` via `create_configured_wsgi_app()` et traite ses requêtes indépendamment.

**Limite importante** : les stores mémoire (sessions, rate-limits) sont **propres à chaque worker**.
Augmenter le nombre de workers sans configurer un session store partagé donne une **fausse impression de robustesse** :

- les sessions seront différentes selon le worker qui répond → comportement d'authentification cassé ;
- les compteurs de rate-limit seront divisés par le nombre de workers en pratique (un attaquant a N tentatives avant d'être bloqué au lieu d'1) ;
- l'anti-rejeu TOTP étant lui aussi par worker, un code MFA intercepté peut être rejoué sur un autre worker que celui qui l'a consommé.

Pour un déploiement multi-worker fiable, **configurer `MariaDbSessionStore` explicitement** (cf §4).

---

## 8. Ce que Forge 1.0 garantit / ne garantit pas

### Garanti

- entrée WSGI configurée : `core.app.wsgi.create_configured_wsgi_app()` ;
- factory partagée `core.app.app_factory.build_application()` (même config qu'`app.py`) ;
- warnings production émis à la construction de l'application WSGI (`MemorySessionStore` en `APP_ENV=prod`) ;
- résolution sécurisée de l'IP client via `APP_TRUSTED_PROXIES` ;
- smoke tests WSGI transversaux (factory + warnings + IP client) ;
- helpers de cookie de session centralisés (`set_session_cookie`, `clear_session_cookie`) ;
- comparaison constant-time pour le token Bearer API ;
- `wsgi.py` et unit systemd Gunicorn générés par `forge deploy:init`, avec un parcours documenté : [Mise en production pas à pas](mise-en-production.md).

### Non garanti : à cadrer côté infrastructure ou tickets futurs

- rate-limit distribué (Redis / autre backend) ;
- session store distribué cloud-native ;
- support complet `X-Forwarded-For` (chaînes de proxies) ;
- support CIDR pour `APP_TRUSTED_PROXIES` ;
- guide d'exploitation haute disponibilité ;
- automatisation de la sécurité applicative métier (authentification fine, RBAC dynamique au-delà du socle) ;
- intégration packagée d'un serveur WSGI dans le runtime Forge (Gunicorn reste une dépendance projet, pas Forge).

---

## Pour aller plus loin

- [Déploiement WSGI minimal](wsgi-deployment.md), Gunicorn + reverse proxy
- [Guide de déploiement](deployment.md), Architecture Nginx/systemd
- [Sécurité en production](production-security.md), Cookies, headers, CSRF, uploads
- [ADR-002, Stratégie de session](../adr/002-session-strategy.md)
- [ADR-009, Politique de stabilité terrain](../adr/009-stability-policy-terrain.md)
