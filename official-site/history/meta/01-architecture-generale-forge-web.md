# Conversation 01 : Architecture générale Forge-web

## 1. Rôle de cette conversation

Cette conversation correspond à la conversation **01 — Architecture générale** du projet ChatGPT **Forge-web**.

Elle sert à cadrer le projet globalement avant de passer aux opérations techniques.

Son objectif n’est pas d’exécuter des commandes terminal, mais de fixer les décisions structurantes :

- séparation entre **Forge**, **Forge-web** et **Forge Design** ;
- rôle du site officiel `forgemvc.com` ;
- choix de l’architecture web initiale ;
- séparation entre site, documentation, DNS, reverse proxy, firewall et mail ;
- ordre prudent de progression ;
- limites à ne pas franchir trop tôt.

---

## 2. Objectif général du projet Forge-web

Le projet **Forge-web** doit publier le site officiel du framework Python Forge sous le domaine :

```text
forgemvc.com
www.forgemvc.com
```

Le site devra accueillir :

- une landing page publique ;
- la documentation Forge ;
- des liens vers GitHub, PyPI et les ressources officielles ;
- éventuellement plus tard une démo publique ;
- éventuellement plus tard un serveur mail lié au domaine.

Le projet **Forge-web** ne doit pas modifier le cœur du framework Forge.

---

## 3. Séparation des périmètres

### 3.1 Forge

Forge reste le framework Python MVC principal.

Il contient :

- le cœur du framework ;
- la CLI `forge` ;
- les générateurs ;
- les modules officiels ;
- la documentation technique du framework.

Forge ne doit pas être transformé en site vitrine ni en application métier.

### 3.2 Forge-web

Forge-web est un projet séparé.

Il sert uniquement à publier :

- la landing page officielle ;
- la documentation publique ;
- les pages de présentation ;
- les éventuelles pages de téléchargement, installation ou liens publics.

Forge-web est donc le projet de publication web, pas le framework.

### 3.3 Forge Design

Forge Design reste un futur projet séparé.

Il ne fait pas partie de Forge-web au départ.

Il ne doit pas être mélangé avec :

- la landing page ;
- la documentation ;
- le reverse proxy ;
- le DNS ;
- le serveur mail.

### 3.4 Infrastructure

L’infrastructure couvre :

- Proxmox ;
- VM web ;
- reverse proxy ;
- HTTPS ;
- DNS ;
- firewall ;
- sauvegardes ;
- monitoring ;
- éventuel serveur mail.

Ces sujets doivent rester séparés des décisions éditoriales et du code Forge.

---

## 4. Décision d’architecture initiale

L’architecture retenue pour la première version publique est volontairement simple.

```text
Internet
  ↓
Box / routeur
  ↓
VM forge-web
  ↓
Caddy
  ↓
Site statique Forge-web
  ├── landing page
  └── documentation MkDocs générée
```

Accès administrateur séparé :

```text
Administrateur
  ↓
Tailscale / VPN / réseau local
  ↓
SSH VM forge-web
  ↓
Proxmox uniquement en privé
```

Cette architecture évite trois erreurs :

1. exposer Proxmox directement ;
2. démarrer trop tôt avec une architecture réseau complexe ;
3. exposer une application dynamique inutilement.

---

## 5. Choix du site statique

La première version du site sera statique.

Cela signifie :

- pas de base de données pour le site officiel ;
- pas de back-office dynamique ;
- pas d’application Forge exposée au départ ;
- pas de serveur applicatif Python nécessaire pour publier la documentation ;
- fichiers HTML/CSS/JS générés et servis par Caddy.

Avantages :

- plus simple ;
- plus stable ;
- plus facile à sauvegarder ;
- moins de surface d’attaque ;
- plus facile à déployer ;
- parfaitement adapté à une landing page et à une documentation.

Décision :

```text
Forge-web produira un site statique.
```

---

## 6. Documentation MkDocs

La documentation publique sera générée avec **MkDocs**.

Principe :

```text
docs/        → sources Markdown
mkdocs.yml   → configuration MkDocs
site/        → site généré
```

La documentation doit être construite localement avant publication.

Commandes qui seront utilisées plus tard dans la conversation dédiée :

```bash
mkdocs serve
mkdocs build --strict
```

Mais ces commandes ne sont pas lancées dans cette conversation. Elles relèvent de :

```text
17 — Environnement local de génération
04 — Documentation MkDocs
```

---

## 7. Choix du reverse proxy : Caddy

Le choix recommandé pour le début est **Caddy**.

Raisons :

- configuration simple ;
- HTTPS automatique ;
- redirections faciles ;
- très adapté à un site statique ;
- moins verbeux que Nginx + Certbot.

Alternative possible :

```text
Nginx + Certbot
```

Mais cette alternative est plus lourde pour le besoin initial.

Décision :

```text
Caddy sera utilisé en première intention pour servir forgemvc.com en HTTPS.
```

---

## 8. DNS minimal retenu

Configuration DNS initiale :

```text
A      forgemvc.com       → IP publique du serveur
CNAME  www.forgemvc.com   → forgemvc.com
```

Domaine canonique :

```text
https://forgemvc.com
```

Redirections attendues :

```text
http://forgemvc.com       → https://forgemvc.com
http://www.forgemvc.com   → https://forgemvc.com
https://www.forgemvc.com  → https://forgemvc.com
```

Objectif : éviter deux sites concurrents :

```text
forgemvc.com
www.forgemvc.com
```

Décision :

```text
forgemvc.com est le domaine officiel.
www.forgemvc.com redirige vers forgemvc.com.
```

---

## 9. Ports publics autorisés

Seuls deux ports doivent être publics en première phase :

```text
80/tcp   HTTP
443/tcp  HTTPS
```

Le port 80 sert principalement à :

- rediriger vers HTTPS ;
- permettre certaines validations de certificat selon la configuration.

Le port 443 sert à :

- publier le site en HTTPS.

---

## 10. Ports à ne pas exposer

Ces ports ne doivent pas être ouverts publiquement :

```text
22/tcp     SSH public direct
8006/tcp   interface Proxmox
3306/tcp   MariaDB
5432/tcp   PostgreSQL
6379/tcp   Redis
25/tcp     SMTP, tant que le mail n’est pas validé
587/tcp    SMTP submission, tant que le mail n’est pas validé
993/tcp    IMAPS, tant que le mail n’est pas validé
```

Règle stricte :

```text
Proxmox ne doit jamais être exposé directement sur Internet.
```

Accès recommandé :

```text
Tailscale / VPN / réseau local uniquement
```

---

## 11. Serveur mail : décision de report

Le serveur mail n’est pas déployé maintenant.

Raison : l’auto-hébergement mail est beaucoup plus sensible que l’hébergement web.

Il impose de maîtriser :

- MX ;
- SPF ;
- DKIM ;
- DMARC ;
- PTR / reverse DNS ;
- réputation IP ;
- antispam ;
- filtrage ;
- sauvegardes ;
- supervision.

Décision :

```text
Pas de serveur mail au départ.
Pas de MX pour l’instant.
Pas de mail.forgemvc.com actif.
```

Le mail sera étudié seulement après :

1. site web publié ;
2. HTTPS validé ;
3. accès Proxmox sécurisé ;
4. sauvegardes en place ;
5. firewall stabilisé.

---

## 12. VM firewall / DMZ : décision de report

La VM firewall ou DMZ est une bonne idée à terme, mais elle n’est pas prioritaire immédiatement.

Risque : une mauvaise règle réseau peut couper l’accès au serveur.

Décision :

```text
Pas de VM firewall en première étape.
```

Approche retenue :

```text
VM forge-web simple
Firewall Proxmox progressif
Accès admin via Tailscale/VPN
DMZ étudiée plus tard
```

---

## 13. Architecture progressive retenue

### Phase A — Version minimale publiable

Objectif : publier rapidement mais proprement.

```text
forgemvc.com
└── landing page + documentation
```

Avec :

```text
VM forge-web
Caddy
HTTPS automatique
DNS minimal
Proxmox non exposé
```

### Phase B — Sécurisation

Objectif : renforcer l’infrastructure après publication initiale.

```text
SSH limité
Firewall VM
Firewall Proxmox
Sauvegardes
Logs
Monitoring simple
```

### Phase C — Évolutions possibles

Seulement après stabilisation :

```text
docs.forgemvc.com      si la documentation doit être séparée
demo.forgemvc.com      si une démo Forge devient publique
design.forgemvc.com    si Forge Design devient public
mail.forgemvc.com      si le serveur mail est validé
status.forgemvc.com    si une page d’état devient utile
```

Décision actuelle :

```text
Ne créer que les entrées DNS nécessaires au départ.
```

---

## 14. Ce qui est explicitement refusé pour l’instant

| Sujet | Décision |
|---|---|
| Exposer Proxmox sur Internet | Refusé |
| Ouvrir SSH à tout Internet | Refusé |
| Créer le serveur mail maintenant | Refusé |
| Activer DNSSEC trop tôt | Refusé |
| Ajouter CAA avant HTTPS validé | Refusé |
| Créer une VM firewall sans plan de retour | Refusé |
| Mélanger Forge-web avec Forge Design | Refusé |
| Modifier le cœur Forge depuis Forge-web | Refusé |
| Multiplier les sous-domaines dès le départ | Refusé |

---

## 15. Ordre de travail retenu

L’ordre retenu pour le projet Forge-web est :

```text
01 Architecture générale
02 Création du dépôt Forge-web
17 Environnement local de génération
03 Landing page
04 Documentation MkDocs
15 Stratégie éditoriale et contenu public
16 Publication GitHub / liens externes
05 VM web Proxmox
11 Sécurité SSH et accès administrateur
06 DNS forgemvc.com
07 Reverse proxy et HTTPS
13 Procédure de déploiement Forge-web
12 Sauvegardes et restauration
08 Firewall Proxmox
14 Monitoring et logs
18 Plan de mise en production finale
09 VM firewall / DMZ
10 Serveur mail forgemvc.com
```

Raison de cet ordre :

- d’abord cadrer ;
- ensuite créer le projet ;
- ensuite générer localement ;
- ensuite produire le contenu ;
- ensuite seulement publier ;
- ensuite sécuriser plus finement ;
- enfin étudier les sujets risqués.

---

## 16. Règle de travail pour les conversations techniques

Pour toute opération technique, utiliser le préfixe :

```text
ope ...
```

Exemples :

```text
ope créer la structure initiale du projet Forge-web
ope installer MkDocs localement
ope préparer la VM web Proxmox
ope vérifier les DNS de forgemvc.com
ope configurer Caddy pour HTTPS
```

Quand une opération commence, la méthode doit rester stricte :

1. checklist claire ;
2. une seule étape à la fois ;
3. commandes limitées à l’étape en cours ;
4. attente du retour terminal ;
5. diagnostic si erreur ;
6. aucune supposition de réussite ;
7. préservation des fichiers existants.

---

## 17. Décision finale de la conversation 01

Décision consolidée :

```text
Forge-web sera un projet séparé.
Il produira un site statique composé d’une landing page et d’une documentation MkDocs.
Le site sera publié sur une VM dédiée Proxmox.
Caddy servira le site et gérera HTTPS.
forgemvc.com sera le domaine canonique.
www.forgemvc.com redirigera vers forgemvc.com.
Seuls les ports 80 et 443 seront publics.
Proxmox restera inaccessible depuis Internet.
SSH restera réservé à un accès administrateur contrôlé.
Le mail et la VM firewall/DMZ sont reportés.
```

---

## 18. Prochaine conversation à ouvrir

La prochaine conversation logique est :

```text
02 — Création du dépôt Forge-web
```

Message d’ouverture conseillé :

```text
Cette conversation est la n°02 du projet Forge-web : Création du dépôt Forge-web.

Objectif :
Créer proprement le projet local Forge-web, séparé du framework Forge.

Contexte validé dans la conversation 01 — Architecture générale :
- Forge-web est un projet séparé de Forge ;
- il servira à publier forgemvc.com ;
- il contiendra la landing page et la documentation publique ;
- le site sera statique dans un premier temps ;
- MkDocs servira à générer la documentation ;
- Caddy sera probablement utilisé plus tard pour servir le site en HTTPS ;
- Proxmox ne doit jamais être exposé publiquement ;
- le mail et la VM firewall/DMZ sont reportés.

Règles de travail :
- commencer par une checklist claire ;
- donner uniquement les commandes de l’étape en cours ;
- attendre mon retour terminal avant de continuer ;
- ne jamais supposer qu’une commande a réussi ;
- préserver les fichiers existants ;
- ne pas modifier le cœur du framework Forge.

Je veux maintenant créer la structure initiale du projet Forge-web.
```

Commande à écrire ensuite dans cette nouvelle conversation :

```text
ope créer la structure initiale du projet Forge-web
```

---

## 19. Résumé ultra-court

```text
Conversation 01 = cadrage architectural.
Décision = site statique Forge-web, landing + docs MkDocs, servi par Caddy sur VM Proxmox.
Domaine = forgemvc.com.
www = redirection.
Ports publics = 80/443 seulement.
Proxmox, SSH, mail, DNSSEC, CAA, VM firewall = prudence / report.
Prochaine étape = conversation 02, création propre du dépôt Forge-web.
```

---

## 20. Sources internes utilisées

Documents internes du projet Forge-web :

- `conversations-projet-forge-web.md`
- `notes-infrastructure-proxmox.md`
- `notes-dns-domaine-forgemvc-com.md`
- `CHARTE_DOC.md`

Ces documents structurent les décisions de cette conversation.
