# Security Policy

## Supported Versions

| Version | Support sécurité |
|---------|:----------------:|
| `1.x` série préversion courante (`1.0.0rc2`, release candidate) | ✅ Actif |
| `< 1.0.0-beta.1` | ❌ Non supporté |

La série `1.x` est la seule supportée ; en phase de préversion, cela correspond
à la release candidate courante `1.0.0rc2` (forme SemVer `1.0.0-rc.2`). Une fois
la `1.0.0` stable publiée, la ligne supportée sera `1.0.x`.

---

## Reporting a Vulnerability

Merci de **ne pas publier** les détails d'une vulnérabilité dans les issues GitHub publiques.

**Procédure recommandée :**

1. Ouvrir une [GitHub Security Advisory](https://github.com/caucrogeGit/Forge/security/advisories/new) (onglet *Security* → *Advisories* → *New draft advisory*).
2. Décrire le problème, les étapes de reproduction et l'impact estimé.
3. Laisser le champ exploit vide ou en accès restreint.

Si les advisories privés ne sont pas disponibles sur ce dépôt, envoyer un email à **forgemvc@gmail.com** avec le sujet `[SECURITY] Forge — <titre court>`.

Une confirmation de réception sera envoyée sous **5 jours ouvrés**.
Un correctif sera préparé, validé et publié dans les meilleurs délais avant divulgation publique.

---

## Périmètre

Les rapports de sécurité peuvent concerner :

- authentification et hachage des mots de passe (`core.auth`, `core.security.hashing`) ;
- gestion des sessions (`core.security.session`) ;
- protection CSRF (`core.security.csrf`) ;
- RBAC et autorisations (`forge_mvc_rbac`) ;
- MFA (`forge_mvc_mfa`) — OIDC retiré du périmètre Forge ;
- injection SQL dans les modèles ou le code généré ;
- path traversal sur les fichiers statiques ou les uploads ;
- validation et gestion des uploads (`forge_mvc_files` ; validation pure dans `core.forms`) ;
- code généré par la CLI introduisant des défauts dangereux ;
- exposition de secrets ou de données sensibles ;
- fuite d'informations dans les messages d'erreur HTTP.

---

## Hors périmètre

Les éléments suivants **ne sont pas** traités comme des rapports de sécurité :

- bugs fonctionnels sans impact sécurité ;
- demandes de nouvelles fonctionnalités ;
- problèmes de performance non exploitables ;
- failles résultant d'une mauvaise configuration explicitement documentée ;
- versions antérieures à 1.0.0-beta.1 (non maintenues) ;
- problèmes spécifiques à l'environnement de l'utilisateur (MariaDB mal configuré, certificats expirés, etc.).

---

## Modèle de sécurité

Forge est un framework MVC Python serveur. Son périmètre de sécurité couvre :

- le pipeline de la requête HTTP (routage, middlewares, dispatch) ;
- la génération et la validation des tokens CSRF ;
- le hachage des mots de passe (Argon2id pour les nouveaux projets) ;
- les sessions HTTP (stockage mémoire par défaut, voir *Limites connues*) ;
- la protection RBAC au niveau des contrôleurs ;
- la génération de code par la CLI (le code généré ne doit pas introduire de défauts de sécurité par défaut).

Forge **ne gère pas** la sécurité réseau, le TLS en production (délégué à Nginx), ni la sécurité de la base de données MariaDB.

---

## Notes de déploiement

Forge est conçu pour tourner **en mono-processus derrière un reverse proxy** (Nginx recommandé).

Configuration supportée :

```
Internet → Nginx (TLS) → Forge (processus unique, port local)
```

Configuration **non supportée** par défaut :

- Gunicorn / uWSGI multi-worker sans backend de session partagé ;
- déploiement horizontal multi-machines ;
- exposition directe de Forge sur Internet sans reverse proxy.

Pour toute question de déploiement sécurisé, voir [docs/deployment/deployment.md](docs/deployment/deployment.md).

---

## Contrôle des dépendances

Un workflow GitHub Actions (`dependency-audit.yml`) exécute `pip-audit` chaque lundi matin et à la demande.

**Statut actuel : mode observation, non bloquant.**

- Le scan peut signaler des vulnérabilités connues dans les dépendances Python de Forge.
- Ces résultats sont à analyser avant toute correction : tous les avertissements ne sont pas exploitables dans le contexte de Forge.
- Le scan ne bloque pas encore les contributions automatiquement.
- Forge ne garantit pas l'absence de vulnérabilités dans ses dépendances à tout instant.

Si `pip-audit` remonte une vulnérabilité réelle, un ticket séparé `DEPENDENCY-FIX-XXX` sera créé.

Pour lancer le scan localement :

```bash
pip install pip-audit
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
```

### Vulnérabilités connues suivies

- **`PYSEC-2026-217` — `mariadb` 1.1.14 (runtime).** L'avis concerne le connecteur
  MariaDB sur un chemin précis : échappement par `mysql_real_escape_string()`,
  protocole **texte** et jeu de caractères **big5**, qui pouvait laisser passer
  une injection SQL.
  **Exposition Forge : faible.** Forge n'utilise jamais `mysql_real_escape_string()` :
  toutes les requêtes passent par des paramètres liés (`cursor.execute(sql, params)`,
  protocole binaire), et le jeu de caractères par défaut n'est pas big5.
  **Aucune version corrigée n'est disponible en amont** (1.1.14 est la dernière
  publiée ; `pip-audit` ne liste aucune `fix version`).
  Le suivi est **automatisé** : `tools/check_ignored_vulns.py` relit l'audit sans
  les exclusions et **échoue** dès qu'un avis ignoré annonce une version
  corrective. Il tourne chaque semaine (`dependency-audit.yml`, seule étape
  bloquante de ce workflow) et à chaque validation de release. La dépendance est
  déclarée en plage, `mariadb>=1.1.14,<1.2`, pour accueillir le correctif sans
  changer le contrat.

- **`GHSA-537c-gmf6-5ccf` — `cryptography` (opt-in MFA).** L'avis vise l'OpenSSL
  lié statiquement dans les wheels `cryptography` antérieures à `48.0.1`. Le pin
  de `forge-mvc-mfa` est relevé à `cryptography>=48.0.1,<49` (MFA n'utilise que
  Fernet, API stable), ce qui embarque l'OpenSSL corrigé. **Résolu.**

---

## Divulgation responsable

Forge suit une politique de **divulgation coordonnée** :

1. Signalement privé par l'auteur ou la communauté.
2. Confirmation et analyse par le mainteneur.
3. Développement et test du correctif.
4. Publication du correctif dans la prochaine préversion (`1.0.0rcN`) tant que la `1.0.0` stable n'est pas publiée, puis dans une version corrective `1.0.x`.
5. Publication de l'advisory après livraison du correctif.

Le délai cible entre réception du rapport et publication du correctif est de **30 jours** pour les vulnérabilités critiques.

---

## Limites connues

Forge utilise des **sessions mémoire** par défaut.

- Les sessions sont perdues au redémarrage du processus.
- Elles ne sont pas partagées entre plusieurs workers.
- Le multi-worker (Gunicorn, uWSGI) n'est pas supporté sans backend de session partagé.
- Le scaling horizontal n'est pas supporté sans backend de session partagé.

**Forge ne doit pas être utilisé pour des systèmes critiques sans audit de sécurité externe préalable.**

Le cœur fournit deux backends : `MemorySessionStore` (défaut, mono-processus)
et `FileSessionStore` (persistance JSON sur disque). Voir `core/sessions/`.
Le partage entre processus demande l'opt-in `forge-mvc-sessions-db`, qui
apporte `DbSessionStore`, adossé au backend de base de données actif
(ADR-054). Voir ADR-002.

Voir aussi [ADR-002 — Stratégie de session](docs/adr/002-session-strategy.md).
