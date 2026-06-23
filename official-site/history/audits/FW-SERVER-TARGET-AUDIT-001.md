# Rapport final — FW-SERVER-TARGET-AUDIT-001

> Date : 2026-05-23
> Branche : `main`
> **Statut : RAPPORT PARTIEL — VM cible non identifiée.**
> Périmètre exécuté : strictement local (lecture seule). Aucun audit distant, aucune connexion SSH, aucun scan réseau. Forge core intact.

---

## Résumé

L'audit demandé n'a **pas pu être exécuté sur une VM cible** : aucune VM web dédiée à `forgemvc.com` n'est encore identifiée ni provisionnée. Confirmé explicitement par l'utilisateur (« Pas encore — rapport partiel »).

Conformément à la consigne du ticket (« Si la VM cible n'est pas encore clairement identifiée, arrêter le ticket avec un rapport partiel »), aucune action distante n'a été tentée. Aucun scan réseau n'a été effectué. Aucune connexion SSH n'a été ouverte. Aucun port n'a été sondé sur quelque machine que ce soit.

Vérifications strictement locales effectuées :

- État Forge-web : working tree propre, `dist/` régénéré (FW-PUBLISH-READINESS-001), 265 fichiers, landing + docs présents.
- `infra/` : vide (`.gitkeep` seul).
- `notes/` : vide (`.gitkeep` seul).
- Pas de SSH config (`~/.ssh/config` absent).
- Aucune mention d'IP, hostname ou nom de VM dans `docs/`, `README.md`, ou la documentation interne (`docs/meta/`).
- Les mentions de « VM web sur Proxmox » dans la doc restent **génériques** (architecture cible, pas une machine concrète).

Décision : ce ticket est consommé pour valider que **rien n'est en place côté serveur**, et pour orienter le ticket suivant vers la création/identification de la VM cible avant toute publication.

Aucun commit créé.

---

## VM cible

| Information | Valeur |
|---|---|
| Nom de la VM | **non identifiée** |
| Adresse IP locale | **non identifiée** |
| OS | **inconnu** |
| Utilisateur SSH | **inexistant** (pas de cible) |
| Méthode d'accès | **inexistante** (pas de cible) |
| Rôle prévu | VM web Forge-web (futur) |
| Réponse utilisateur | « Pas encore — rapport partiel » |

Aucune VM web dédiée n'a été préparée à ce stade du projet. Le projet est encore en phase **local-only**.

---

## Accès SSH

**Non testé** — pas de cible.

Vérifications négatives locales :

- `~/.ssh/config` : absent.
- Aucune mention de `ssh root@…` ou `ssh user@vm…` dans la doc ou les notes Forge-web.
- Aucune clé SSH dédiée à un déploiement n'est répertoriée dans le dépôt (et le `.gitignore` exclut correctement `*.key`, `*.pem`).

---

## Système

**Non audité** — pas de cible.

À documenter dans le ticket de création/identification de la VM (`FW-WEB-VM-CREATE-001`) :

```bash
# À exécuter sur la future VM cible (lecture seule)
hostname
cat /etc/os-release
uname -a
uptime
whoami
id
```

OS recommandé (cohérent avec la doc Forge core) : **Debian 13 stable**, minimal, sans environnement graphique.

---

## Ressources

**Non audité** — pas de cible.

Commandes prévues pour la future VM :

```bash
free -h
df -hT
lsblk
nproc
```

Spécifications **minimales recommandées** pour un site statique Forge-web sous Caddy (à confirmer dans `FW-WEB-VM-CREATE-001`) :

| Ressource | Minimum recommandé | Justification |
|---|---|---|
| CPU | 1 vCPU | site 100 % statique, charge marginale |
| RAM | 512 Mo | Caddy + OS Debian minimal |
| Disque système | 8 Go | OS + Caddy + binaires + buffer |
| Espace logs | 2 Go | logs Caddy + rotation |
| Total recommandé | 10–15 Go | confortable, sans gaspillage |

Le `dist/` actuel pèse ~10 Mo (logo inclus). Aucune contrainte de stockage forte.

---

## Réseau

**Non audité** — pas de cible.

Commandes prévues :

```bash
ip -br addr
ip route
ss -tulpn
```

Points critiques à vérifier sur la future VM :

| Port | Statut attendu sur la VM web | Risque si différent |
|---|---|---|
| 22/tcp | Écoute locale OK (SSH contrôlé) | Si exposé Internet : compromission |
| 80/tcp | **Libre** (sera Caddy) | Si occupé : conflit |
| 443/tcp | **Libre** (sera Caddy) | Si occupé : conflit |
| 8006/tcp | **Absent** (interface Proxmox) | Si présent : VM = node Proxmox → STOP |
| 25, 587, 993 | Absents | Mail non géré pour l'instant |
| 3306, 5432, 6379 | Absents | Site statique, pas de DB |

---

## Ports écoutés

**Non audité** — pas de cible.

Note : `ss -tulpn` doit être exécuté avec `sudo` pour voir les programmes propriétaires des sockets. Sans `sudo`, on voit seulement les ports écoutés sans le nom du processus.

---

## Firewall local

**Non audité** — pas de cible.

Selon la distribution future :

```bash
sudo ufw status verbose          # Debian/Ubuntu
sudo nft list ruleset            # nftables (Debian 12+)
sudo iptables -S                 # legacy
```

Politique cible (à formaliser dans `FW-CADDY-STATIC-SITE-001`) :

- **Default INPUT** : DROP.
- **Autorisé** : 22/tcp (SSH, idéalement restreint à Tailscale/VPN/IP admin), 80/tcp (HTTP redirection vers HTTPS), 443/tcp (HTTPS).
- **Refusé explicitement** : 8006/tcp, 25, 587, 993, ports DB.

---

## Serveurs web présents

**Non audité** — pas de cible.

Vérifications prévues sur la future VM :

```bash
command -v caddy nginx apache2
systemctl status caddy nginx apache2 --no-pager
```

Cas attendus :

- **VM vierge** : aucun serveur web installé → idéal pour FW-CADDY-STATIC-SITE-001.
- **Caddy déjà présent** : à examiner (config existante à respecter ou à remplacer ?).
- **Nginx ou Apache présent** : à examiner — décider si on cohabite, si on migre, ou si on choisit une autre VM.

---

## Dossiers de publication possibles

**Non audité** — pas de cible.

Vérifications prévues :

```bash
ls -ld /var/www /srv /opt
getent passwd | grep -E 'www-data|caddy|forge|deploy'
```

Choix recommandé pour la future cible de déploiement (cf. `docs/deployment-readiness.md`) :

```text
/srv/forge-web/
```

Justification : `/srv` est spécifié par le FHS pour les données servies par le système. `/var/www` est un héritage Apache. `/opt` est plutôt pour des applications tierces auto-contenues.

**Ne pas créer ce dossier dans ce ticket.**

---

## Vérification Proxmox

**Non audité** — pas de cible.

Signaux d'alerte à vérifier impérativement sur toute machine prétendant être la VM web :

| Indicateur | Si présent → |
|---|---|
| Processus `pveproxy` actif | **STOP — c'est un node Proxmox, pas une VM** |
| Port 8006/tcp en écoute | **STOP — interface Proxmox** |
| Paquets `proxmox-ve`, `pve-manager` | **STOP — node Proxmox** |
| Commande `pveversion` disponible | **STOP — node Proxmox** |
| Hostname commençant par `pve-` ou contenant `proxmox` | suspect, à vérifier |

Règle stricte rappelée : **Proxmox ne doit jamais être exposé directement à Internet, et le site Forge-web ne doit jamais être servi depuis le node Proxmox.**

---

## Risques identifiés

Risques **observés à ce stade** (avant toute VM) :

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Choisir une VM partagée avec d'autres services par commodité | Moyenne | Moyen (surface d'attaque accrue) | Imposer une VM dédiée Forge-web au futur ticket de création |
| 2 | Confondre VM web et node Proxmox par méconnaissance | Faible | **Très élevé** (exposition Proxmox) | Vérification §9 obligatoire avant tout déploiement |
| 3 | Exposer SSH publiquement par défaut sur la nouvelle VM | Moyenne | Élevé | Définir d'emblée : SSH limité à Tailscale/LAN/whitelist IP |
| 4 | Ne pas vérifier les ports déjà ouverts avant Caddy | Élevée si on oublie | Moyen (conflit 80/443) | Exécuter `ss -tulpn` AVANT d'installer Caddy |
| 5 | Réutiliser une clé SSH existante non dédiée | Moyenne | Moyen | Créer une clé SSH dédiée au déploiement Forge-web |
| 6 | Choisir un OS exotique ou ancien | Faible | Moyen (mise à jour, support Caddy) | Imposer Debian 13 stable ou équivalent maintenu |
| 7 | Ne pas isoler le user de déploiement | Moyenne | Moyen | Créer un user `forge` ou `deploy` non-root dédié |

---

## Décision proposée

Compte tenu de l'absence de VM cible identifiée, la suite logique est :

1. **Décider** où la VM va être créée :
   - Proxmox existant (créer une nouvelle VM dédiée) ;
   - VPS cloud externe (Hetzner, Scaleway, OVH…) ;
   - Hébergement statique managé (Netlify, Cloudflare Pages…) — option à évaluer mais en rupture avec la doctrine « VM Caddy » du projet.

2. **Provisionner** la VM avec :
   - OS : Debian 13 stable minimal ;
   - 1 vCPU / 512 Mo–1 Go RAM / 10–15 Go disque ;
   - SSH non exposé à Internet (Tailscale ou IP admin whitelistée) ;
   - User non-root pour le déploiement ;
   - Firewall actif par défaut DROP, ports 22/80/443 selon politique.

3. **Auditer** la VM nouvellement provisionnée (relancer ce même ticket, ou son successeur `FW-SERVER-TARGET-AUDIT-002`).

4. **Seulement après** : installer Caddy, configurer le firewall, etc.

---

## Limites restantes

1. **Aucune VM auditée** : conséquence directe de l'absence de cible.
2. **`docs/deployment-readiness.md`** (page publique) reste valide mais générique sur la cible.
3. **Aucune action distante** entreprise — `ss`, `ssh`, `nmap`, `ping` n'ont jamais été lancés.
4. **Aucune commande nécessitant `sudo`** sur localhost — il n'y a pas lieu de privilégier le poste de dev comme cible.
5. **`infra/` reste vide** : il accueillera un fichier de notes (Caddyfile-type, instructions VM) au moment de `FW-CADDY-STATIC-SITE-001`.
6. **`notes/` reste vide** : il accueillera potentiellement les notes manquantes (`notes-infrastructure-proxmox.md`, `notes-dns-domaine-forgemvc-com.md`) identifiées en FW-AUDIT-EXISTING-001 et FW-REPO-STRUCTURE-001, à recréer dans un ticket dédié (`FW-NOTES-RECREATE-001`).
7. **Aucun commit créé.**

---

## Prochain ticket recommandé

**FW-WEB-VM-CREATE-001 — Créer ou préparer la VM web Forge-web**

Périmètre suggéré (à confirmer dans son propre ticket) :

1. Choisir l'hébergeur (Proxmox local, VPS externe, ou autre — décision explicite à documenter).
2. Provisionner la VM avec les spécifications minimales recommandées (§Ressources).
3. Installer Debian 13 minimal, mises à jour à jour.
4. Créer un utilisateur non-root dédié (`forge` ou `deploy`).
5. Configurer SSH (clé publique, pas de mot de passe, port 22 mais non exposé Internet).
6. Vérifier qu'aucun service web n'est démarré par défaut.
7. Documenter dans `infra/vm-web.md` : IP, hostname, user, méthode d'accès.
8. **Ne pas installer Caddy** ni ouvrir les ports 80/443 dans ce ticket.

À la fin de `FW-WEB-VM-CREATE-001`, relancer `FW-SERVER-TARGET-AUDIT-002` (ou réutiliser ce ticket avec une cible désormais identifiée) pour produire l'audit complet.

Chaîne de tickets prévue :

```text
FW-WEB-VM-CREATE-001          (créer/préparer la VM)
FW-SERVER-TARGET-AUDIT-002    (auditer la VM créée)
FW-CADDY-STATIC-SITE-001      (installer/configurer Caddy)
FW-DNS-WEB-001                (DNS A + CNAME minimums)
FW-DEPLOY-PREP-001            (procédure rsync + checklist)
FW-DEPLOY-GO-001              (premier déploiement réel)
FW-ACCESS-LOGS-STATS-001      (logs Caddy + GoAccess)
```
