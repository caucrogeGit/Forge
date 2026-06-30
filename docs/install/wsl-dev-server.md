# Dépannage du serveur de dev sous WSL2

Ce document explique deux pièges qui, **combinés**, donnent l'impression que le
serveur Forge est cassé alors qu'il fonctionne. Symptômes observés :

- `forge run` échoue en boucle avec « Le port 8000 est déjà utilisé sur
  0.0.0.0 », **alors que `ss -tulpn | grep :8000` et `lsof -i :8000` ne montrent
  rien**.
- Quand le serveur démarre malgré tout, `curl http://127.0.0.1:<port>/` **reste
  pendu** (timeout, `HTTP 000`) : la connexion TCP s'ouvre mais aucune réponse
  n'arrive.

!!! tip "En résumé"
    1. Le serveur dev parle **HTTPS** : interrogez-le en `https://`, pas
       `http://`.
    2. Le port est tenu par un **forward fantôme de VS Code** côté Windows,
       invisible aux outils Linux : libérez-le via l'onglet **PORTS**, ou changez
       `APP_PORT`.

---

## Cause n° 1 : le serveur dev est en HTTPS par défaut

En environnement `dev`, Forge active TLS : `config.APP_SSL_ENABLED` vaut `True`
**même si** la ligne reste commentée dans `env/dev`.

```ini
# env/dev
# APP_SSL_ENABLED=true     ← commentée, mais le défaut dev est déjà true
```

Ce comportement vient du défaut de configuration : en `dev`, le défaut de
`APP_SSL_ENABLED` est `true` (en `prod`, il est `false`, car Nginx termine TLS).

Conséquence : le serveur écoute en **HTTPS**. Un client en clair (`http://`)
ouvre la socket TCP puis attend une réponse qui ne viendra jamais. Le serveur,
lui, attend un **handshake TLS**. D'où le `curl` qui « pend » et le `HTTP 000`.

Le log de démarrage le dit explicitement :

```text
[INFO-DEV] Serveur en écoute sur https://0.0.0.0:8001
[INFO-DEV] Attention : le serveur utilise HTTPS - préfixez bien vos URL par https://
           (le navigateur affichera un avertissement de certificat auto-signé).
```

!!! note "Hôte affiché : 127.0.0.1 ou 0.0.0.0"
    L'hôte du log dépend de `APP_HOST` (défaut : `127.0.0.1`). Les exemples
    ci-dessus montrent `0.0.0.0`, valeur d'un projet qui écoute sur toutes les
    interfaces. Le message de port occupé reprend la même valeur d'hôte.

### Vérification

```bash
# KO : reste pendu (clair contre serveur TLS)
curl -s -m 3 http://127.0.0.1:8001/

# OK : -k accepte le certificat auto-signé
curl -sk -m 3 https://127.0.0.1:8001/
# → Bonjour le monde !
```

Dans le navigateur : ouvrir **`https://127.0.0.1:8001/`** et accepter
l'avertissement de certificat auto-signé (normal en dev).

---

## Cause n° 2 : un « port-forward fantôme » de VS Code tient le port

### Pourquoi `ss` et `lsof` ne voient rien

Sous **WSL2 en réseau miroité**, `localhost` est partagé entre Windows et Linux.
Quand un serveur ouvre un port dans WSL, **VS Code (`Code.exe`, côté Windows)
auto-forwarde** ce port sur `127.0.0.1:<port>`. Ce forward **n'est pas toujours
relâché** quand le serveur meurt.

Le listener qui subsiste est alors un **processus Windows**. Les outils Linux
(`ss`, `lsof`) ne le voient pas, mais `bind()` côté WSL échoue quand même avec
`EADDRINUSE` (« déjà utilisé sur 0.0.0.0 »). D'où le paradoxe : rien n'écoute
côté Linux, mais impossible de binder.

### Diagnostic

```bash
# 1) Quelque chose accepte-t-il la connexion alors que rien ne tourne chez nous ?
timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/8000' && echo "listener fantôme"

# 2) Qui écoute, côté Windows ?  (interop WSL → exécutables .exe)
netstat.exe -ano | grep ':8000'
#   TCP    127.0.0.1:8000    0.0.0.0:0    LISTENING    11844

tasklist.exe /FI "PID eq 11844"
#   Code.exe   11844 ...        ← c'est VS Code

# 3) Confirmer côté Linux : bind() brut qui échoue alors que rien n'écoute
python3 - <<'PY'
import socket
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: s.bind(("0.0.0.0", 8000)); print("BIND OK")
except OSError as e: print("ECHEC", e.errno, e.strerror)   # 98 Address already in use
PY
```

!!! warning "À ne pas confondre avec les plages réservées par Windows"
    Hyper-V, WSL et Docker réservent des plages de ports, autre cause possible
    d'`EADDRINUSE` sans listener :

    ```bash
    netsh.exe int ipv4 show excludedportrange protocol=tcp
    ```

    Si le port tombe dans une plage listée, il est réservé par le système :
    changer de port.

### Résolution

**Option A : libérer le port (garde 8000).**
Dans VS Code, onglet **PORTS** (à côté de TERMINAL, en bas), clic droit sur la
ligne du port, puis **Stop Forwarding Port**. Relancer ensuite `forge run`.

**Option B : changer de port (immédiat).**

```ini
# env/dev   (fichier local, ignoré par git)
APP_PORT=8001
```

Relancer `forge run` et ouvrir `https://127.0.0.1:8001/`.

!!! tip "Limiter les forwards automatiques"
    Pour réduire les forwards automatiques à l'avenir, régler dans VS Code :
    `"remote.autoForwardPorts": false` (désactive l'auto-forward) ou
    `"remote.autoForwardPortsSource": "process"`.

---

## Piège bonus : processus serveurs orphelins

`forge run` est un **superviseur autoreload** : il relance un **processus
enfant** (`app.py`) à chaque sauvegarde. Tuer le PID du superviseur (ou de
`python app.py`) ne tue pas forcément l'enfant qui détient réellement la socket.
Un orphelin continue alors d'écouter et provoque à son tour un `EADDRINUSE`.

```bash
# Repérer tous les process serveurs de ce projet
ps -eo pid,etime,cmd | grep -E 'welcome-forge/app\.py|bin/forge run' | grep -v grep

# Nettoyer pour de bon
pkill -9 -f 'welcome-forge/app.py'
pkill -9 -f 'bin/forge run'
```

---

## Récapitulatif (check-list de débogage)

| Symptôme | Cause probable | Vérifier et corriger |
|----------|----------------|----------------------|
| `curl http://` pend, `HTTP 000` | Serveur en **HTTPS** | `curl -sk https://…` ; ouvrir en `https://` |
| « Port déjà utilisé » mais `ss` et `lsof` vides | **Forward fantôme VS Code** | `netstat.exe -ano \| grep :PORT`, puis PORTS → Stop Forwarding, ou changer `APP_PORT` |
| `EADDRINUSE` sans listener, hors VS Code | **Plage réservée Windows** | `netsh.exe … show excludedportrange`, puis changer de port |
| Le port reste pris après un `kill` | **Orphelin** enfant de `forge run` | `pkill -9 -f welcome-forge/app.py` |

### État de référence (qui fonctionne)

```text
forge run                       # APP_ENV=dev, autoreload
→ [INFO-DEV] Serveur en écoute sur https://0.0.0.0:8001
navigateur : https://127.0.0.1:8001/   → « Bonjour le monde ! »
```

---

## Voir aussi

- [Windows + WSL (parcours complet)](windows-wsl.md)
- [Configurer VS Code pour l'auto-import des classes Forge](vscode.md)
