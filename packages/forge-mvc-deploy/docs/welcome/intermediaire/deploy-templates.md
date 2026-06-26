# Adapter les gabarits

Objectif : comprendre et adapter les gabarits Nginx et systemd générés.

**Ce que vous allez apprendre :** les fichiers produits par `deploy:init` sont
des modèles.
Quelques réglages sont à ajuster avant la mise en production : l'utilisateur du
service, le nombre de workers Gunicorn, la taille d'upload Nginx et les chemins
du projet.

Deuxième palier du **niveau intermédiaire** de la progression Deploy.

## Ce que ce starter montre

- les réglages clés du gabarit systemd ;
- les réglages clés du gabarit Nginx ;
- où trouver les chemins à corriger.

## 1. Le gabarit systemd

Fichier `deploy/systemd/forge-app.service` : il lance Gunicorn comme service.

| Réglage | À adapter |
|---------|-----------|
| `User` | Le compte système qui exécute le service, pas `root`. |
| `WorkingDirectory` | Le chemin absolu du projet sur le serveur. |
| Workers Gunicorn | Le nombre de processus, selon les cœurs disponibles. |

### Comprendre ce code

- `User` doit pointer vers un compte dédié, sans privilèges superflus (principe 7, sécuriser par défaut).
- `WorkingDirectory` et les chemins absolus dépendent de votre serveur, le gabarit ne peut pas les deviner.
- Le nombre de workers se règle d'après la machine ; une règle courante est `2 x cœurs + 1`.

## 2. Le gabarit Nginx

Fichier `deploy/nginx/forge-app.conf` : il place Nginx en reverse proxy devant
Forge.

| Réglage | À adapter |
|---------|-----------|
| `server_name` | Le nom de domaine public. |
| Certificats TLS | Les chemins des certificats HTTPS. |
| `client_max_body_size` | Déjà calibré sur `UPLOAD_MAX_SIZE` du projet. |
| `proxy_pass` | L'adresse locale où Forge écoute en HTTP. |

### Comprendre ce code

- Nginx termine HTTPS côté public ; Forge écoute en HTTP local (`APP_SSL_ENABLED=false`).
- `client_max_body_size` est généré d'après `UPLOAD_MAX_SIZE` lu dans `config.py` : harmonisez les deux si vous le changez.
- `proxy_pass` doit viser l'adresse et le port où Gunicorn sert l'application.

## 3. Vérifier après adaptation

```bash
forge deploy:check
```

### Comprendre ce code

- Après avoir adapté les gabarits, relancez `deploy:check` pour valider la cohérence.
- La commande signale notamment une incohérence HTTP/HTTPS entre Nginx et `APP_SSL_ENABLED`.
- Un gabarit personnalisé n'est jamais réécrit par `deploy:init` (write-if-new).

## À retenir

- Les gabarits sont des modèles : `User`, workers, chemins et domaine sont à adapter.
- `client_max_body_size` est calibré sur `UPLOAD_MAX_SIZE` ; gardez les deux cohérents.
- Nginx termine HTTPS, Forge écoute en HTTP local : `deploy:check` vérifie cette cohérence.

## Après ce starter

Vous savez adapter les gabarits.
Faisons le point sur ce niveau intermédiaire.

[Bilan](bilan.md)
