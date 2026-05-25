# ADR-015 — Handshake TLS par thread client pour le serveur de développement

## Statut

Accepté — Forge 1.0.0-beta.9 (ticket `APP-PY-TLS-HANDSHAKE-PER-THREAD-001`).

---

## Date

2026-05-25

---

## Contexte

Forge fournit un serveur de développement HTTPS intégré à `app.py`, basé sur
`http.server.ThreadingHTTPServer`. Ce serveur est destiné au développement
local, à la pédagogie et aux tests : il permet d'expérimenter avec un cookie
`Secure`, un en-tête HSTS, ou le comportement réel d'un navigateur sur HTTPS
sans imposer un reverse proxy en local.

En production, le périmètre reste clair : TLS doit être terminé par Nginx ou
un reverse proxy équivalent, et Forge écoute en HTTP local. Voir la
documentation `wsgi-deployment` et le ticket `WSGI-APP-FACTORY-CONFIG-001`.

### État avant la décision

L'activation TLS dans `app.py` se faisait par :

```python
server.socket = ssl_ctx.wrap_socket(server.socket, server_side=True)
```

Cette ligne enveloppe le **socket d'écoute** : chaque appel `accept()` rend
alors un `SSLSocket`, et `do_handshake_on_connect=True` par défaut force le
handshake TLS à s'exécuter de manière synchrone dans le thread appelant.

Comme `accept()` tourne dans le thread principal de `serve_forever()`, le
handshake TLS bloque ce thread tant qu'il n'est pas terminé. `ThreadingMixIn`
ne lance son thread enfant qu'**après** le retour de `get_request()` — donc
après le handshake. Le thread-par-requête ne protège donc pas du handshake
TLS bloquant.

### Symptômes terrain

Reproductibles sur la configuration courante du projet (VS Code Remote SSH,
navigateur distant, port forwarding, certificat auto-signé non encore
accepté) :

- Après 2 à 6 requêtes navigateur (selon le pre-connect), le serveur se fige
  sans traceback.
- `ss -tlnp | grep 8000` montre `Recv-Q: 5` — la file d'attente du kernel est
  saturée.
- Côté client : `ERR_TIMED_OUT` dans Chrome, `Connection timed out after
  10001 milliseconds` sur curl.
- Particulièrement facile à déclencher quand le navigateur refuse le
  certificat auto-signé : les handshakes interrompus (alerte
  `CERTIFICATE_UNKNOWN`) se cumulent et finissent par bloquer la boucle.

---

## Décision

1. Le socket d'écoute **n'est pas wrappé** par `ssl_ctx.wrap_socket(...)`.
   `accept()` rend toujours un socket TCP brut.
2. Le wrap TLS s'exécute dans `process_request_thread()` de la sous-classe
   `TLSThreadingHTTPServer`, **dans le thread du client** lancé par
   `ThreadingMixIn`.
3. Le handshake est borné par `TLS_HANDSHAKE_TIMEOUT = 10s` via
   `request.settimeout(...)`. Après le handshake, le socket repasse en mode
   bloquant standard pour la requête HTTP elle-même.
4. Les erreurs `ssl.SSLError`, `OSError` et `socket.timeout` sont attrapées,
   loggées en `WARNING` avec l'adresse client et le message d'origine, et la
   connexion est fermée proprement via `shutdown_request(request)`.
5. Le contexte SSL est posé en attribut `server.ssl_context` au lieu de muter
   `server.socket`.

Flux résultant :

```
TCP accept()                       (thread principal — non bloquant)
  → ThreadingMixIn lance un thread (thread du client)
      → wrap_socket()              (handshake TLS, borné par timeout)
          → RequestHandler         (requête HTTP normale)
```

---

## Conséquences

### Positives

- Le serveur dev ne se fige plus après quelques connexions TLS interrompues
  ou refusées.
- Un client TLS lent, muet, mal configuré, ou parlant le mauvais protocole
  n'occupe que son propre thread — la boucle d'accept reste disponible.
- Le port 8000 reste utilisable avec VS Code Remote SSH, port forwarding,
  navigateurs distants, et scanners de sécurité agressifs sans dégradation.
- Le comportement est plus robuste face aux certificats auto-signés non
  encore acceptés par le navigateur.
- Les handshakes échoués sont visibles dans les logs (`WARNING — Handshake
  TLS échoué depuis <addr> : <message>`).

### Limites

- Le serveur dev reste un serveur de développement. Il ne remplace pas
  Gunicorn + reverse proxy en production (cf ADR-005, ADR-006, et la
  documentation `wsgi-deployment`).
- `TLS_HANDSHAKE_TIMEOUT` est une constante de module. Sa configurabilité
  via `config.py` est un ticket de suivi (`APP-TLS-HANDSHAKE-TIMEOUT-CONFIG`,
  hors scope de cet ADR).
- L'observabilité des handshakes TLS échoués reste limitée au log
  (`WARNING`). Pas de compteur, pas de métrique exportée — un ticket de
  suivi optionnel a été suggéré.
- Le serveur dev reste mono-processus. Le multi-worker (Gunicorn, uWSGI)
  reste l'apanage du déploiement production via WSGI.

---

## Alternatives écartées

### A — Continuer à wrapper le socket d'écoute

Maintenir `server.socket = ssl_ctx.wrap_socket(server.socket, ...)`.

Rejeté : c'est exactement le code qui produit le blocage. Tout client TLS
qui ne complète pas son handshake fige toute la boucle d'acceptation. La
preuve a été reproduite et documentée.

### B — Surcharger uniquement `get_request()` pour wrapper là

Surcharger `BaseServer.get_request()` pour appeler `wrap_socket()` après
`accept()`.

Rejeté : `get_request()` est appelée par `serve_forever()` dans le thread
principal, exactement comme `accept()`. Le handshake TLS y est aussi
bloquant. Cette approche avait été proposée dans un ticket antérieur — c'est
une fausse piste.

### C — Supprimer TLS du serveur de développement

Désactiver le mode HTTPS de `app.py`, imposer HTTP en dev.

Rejeté : HTTPS local reste utile pour tester certains comportements
navigateur, notamment les cookies `Secure`, le contenu mixte HTTPS/HTTP, et
les en-têtes HSTS. Supprimer ce mode appauvrirait la pédagogie sans
contrepartie.

### D — Imposer un reverse proxy même en développement

Documenter l'usage obligatoire d'un Nginx/Caddy local pour terminer TLS,
même en dev.

Rejeté : trop lourd pour un usage pédagogique et quotidien. Forge vise un
démarrage en quelques minutes (`python app.py`). Imposer un reverse proxy
en plus contredirait cet objectif.

### E — Utiliser `ThreadingHTTPSServer` (Python 3.14+)

`http.server.ThreadingHTTPSServer` a été ajouté en Python 3.14 et résout
nativement ce problème.

Rejeté pour l'instant : Forge cible Python 3.12+ (ADR-006). La compatibilité
3.12 et 3.13 doit être préservée. Une future bascule sur
`ThreadingHTTPSServer` sera évaluée quand Python 3.14 sera la cible minimale.

---

## Hors périmètre de cet ADR

- Rendre `TLS_HANDSHAKE_TIMEOUT` configurable via `config.py`.
- Modifier les niveaux de logs TLS (déclasser `CERTIFICATE_UNKNOWN` en INFO).
- Ajouter un compteur d'observabilité des handshakes échoués.
- Documenter un guide complet Nginx/Caddy/systemd pour la production.
- Modifier la configuration WSGI ou la stratégie de déploiement production.

---

## Référence

- Code livré : `app.py`, classe `TLSThreadingHTTPServer`, constante
  `TLS_HANDSHAKE_TIMEOUT`.
- Ticket d'implémentation : `APP-PY-TLS-HANDSHAKE-PER-THREAD-001` (commit
  `fc520cf` sur la branche `fix/tls-per-thread-handshake`).
- Ticket documentaire : `APP-PY-TLS-HANDSHAKE-DOCS-001` (cet ADR).
- ADR-005 Packaging : `docs/adr/005-packaging.md` (périmètre WSGI/prod).
- ADR-006 Python 3.12+ : `docs/adr/006-python-version.md` (pourquoi
  `ThreadingHTTPSServer` n'est pas une option immédiate).
- Documentation WSGI : `docs/wsgi-deployment.md` (terminer TLS via reverse
  proxy en production).
