# Checklist de déploiement production

Liste **actionnable** pour mettre une application Forge en production proprement.
Cette page est un fil conducteur ; les détails vivent dans les guides liés en
bas. Ticket : `PRODUCTION-CHECKLIST-DOCS-001`.

---

## 1. Avant de déployer — vérifications

Lance ces commandes **depuis le projet**, dans l'environnement cible :

```bash
forge doctor                    # diagnostic complet (Python, env, DB, SSL, sécurité prod…)
forge migration:apply --dry-run # aperçu des migrations à appliquer + leur SQL, sans rien exécuter
```

`forge doctor` inclut un check **Sécurité prod** : il vérifie que l'application
tourne avec un compte base de données **applicatif** (et non le compte admin),
et que les uploads sont **bornés** (`UPLOAD_MAX_SIZE`). Si l'opt-in
`forge-mvc-files` est installé, il vérifie aussi que les extensions autorisées
(`UPLOAD_ALLOWED_EXTENSIONS`) ne sont pas vides. Corrige tout `[WARN]`/`[FAIL]` avant d'exposer.

- [ ] `forge doctor` ne remonte aucun `[FAIL]`.
- [ ] Le check **Sécurité prod** est `[OK]`.
- [ ] `forge migration:apply --dry-run` montre exactement ce que tu attends.
- [ ] La suite de tests passe sur la version déployée.

## 2. Configuration `env/prod`

- [ ] `env/prod` existe et **ne contient aucun secret réel commité** (les
      fichiers `env/*` sont protégés et ignorés du suivi).
- [ ] `APP_ENV=prod`.
- [ ] Compte DB **applicatif** (`DB_APP_*`) distinct du compte **admin**
      (`DB_ADMIN_*`), avec privilèges minimaux.
      → [Configurer les comptes MariaDB d'un projet](../install/mariadb-comptes.md).
- [ ] `SSL_CERTFILE` / `SSL_KEYFILE` configurés (ou TLS terminé par le reverse
      proxy — voir §4).
- [ ] Plafond du corps multipart : `UPLOAD_MAX_SIZE` (noyau). Si l'opt-in
      `forge-mvc-files` est utilisé, configure aussi `UPLOAD_ALLOWED_EXTENSIONS`
      et `UPLOAD_ALLOWED_MIME_TYPES` (lus depuis l'environnement, ADR-032).

## 3. Sessions

- [ ] **Ne pas** utiliser le store mémoire en production (sessions perdues au
      redémarrage). Forge **avertit** au démarrage en `APP_ENV=prod` avec un
      store mémoire — configure un store partagé (ex. `FileSessionStore`).
      Voir [ADR-002](../adr/002-session-strategy.md).

## 4. Serveur d'application + reverse proxy

- [ ] Servir via **WSGI** (pas le serveur de dev `forge run`).
      → [Déploiement WSGI minimal](wsgi-deployment.md).
- [ ] Placer Forge derrière **Caddy / Nginx** (TLS, en-têtes, fichiers
      statiques). → [Déploiement avancé](deploy-advanced.md).
- [ ] Vérifier les en-têtes de sécurité et la CSP.
      → [Sécurité en production](production-security.md).

## 5. Migrations & exploitation

- [ ] `forge migration:apply --dry-run` puis `forge migration:apply`
      (sauvegarde la base avant en prod).
- [ ] Vérifier les **logs** côté serveur (les erreurs détaillées y vont ; la
      page d'erreur publique reste sobre, sans stacktrace).
- [ ] Connaître les [limites de production](production-limits.md) assumées.

## 6. Mise à jour

```bash
forge update --check     # version installée + commande de mise à jour suggérée
```

`forge update` ne modifie **pas** ton projet et ne lance **aucune migration**
automatiquement (pip en venv, ou `pipx upgrade` en installation pipx).

---

## À ne **jamais** faire en production

- Lancer `forge run` (serveur de développement) comme serveur public.
- Utiliser le compte DB **admin** comme compte applicatif.
- Stocker des secrets réels dans des fichiers commités.
- Exposer un store de sessions **mémoire**.
- Appliquer des migrations sans `--dry-run` préalable ni sauvegarde.

## Pour aller plus loin

- [Guide de déploiement](deployment.md)
- [Déploiement WSGI minimal](wsgi-deployment.md)
- [Sécurité en production](production-security.md)
- [Limites de production](production-limits.md)
- [Déploiement avancé](deploy-advanced.md)
