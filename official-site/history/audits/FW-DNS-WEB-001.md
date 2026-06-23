# Rapport final — FW-DNS-WEB-001

## Résumé

Audit DNS préparatoire réalisé sans modification de zone.

Le domaine `forgemvc.com` utilise Cloudflare comme DNS autoritatif.

Aucun enregistrement web actif n’a été trouvé pour le domaine racine ou `www`.

## Domaine

- Domaine : `forgemvc.com`.
- Variante prévue : `www.forgemvc.com`.
- Domaine canonique cible : `https://forgemvc.com/`.

## Gestion DNS détectée

Nameservers autoritatifs :

- `phil.ns.cloudflare.com`
- `violet.ns.cloudflare.com`

## IP publique détectée

IP publique vue depuis `devstation` :

- `93.26.201.177`

## Enregistrements actuels

Aucun enregistrement actif détecté pour :

- `A forgemvc.com`
- `AAAA forgemvc.com`
- `CNAME www.forgemvc.com`
- `A www.forgemvc.com`
- `MX forgemvc.com`
- `TXT forgemvc.com`
- `CAA forgemvc.com`
- `DS forgemvc.com`

La zone est donc vide côté web et ne présente pas de conflit apparent.

## Cible DNS proposée

Configuration minimale future :

- `A forgemvc.com -> 93.26.201.177`
- `CNAME www.forgemvc.com -> forgemvc.com`

TTL recommandé pendant les tests : `Auto` ou `300` secondes.

Proxy Cloudflare recommandé au départ : `DNS only`, pour laisser Caddy gérer directement HTTP/HTTPS et faciliter le diagnostic.

## Risques

- IP publique potentiellement dynamique.
- Redirection box/routeur 80/443 pas encore validée.
- Caddy n’écoute pas encore sur 443.
- Proxmox ne doit jamais être exposé.
- SSH ne doit pas être redirigé publiquement.
- Cloudflare proxy peut compliquer le diagnostic HTTPS initial.

## Hors périmètre respecté

Aucun DNS modifié.
Aucun port ouvert.
Aucune modification Caddy.
Aucune modification Proxmox.
Aucun mail configuré.
DNSSEC et CAA non activés.

## Décision

La zone DNS est prête pour une configuration web minimale, mais il faut d’abord vérifier la redirection routeur/box 80/443 vers `192.168.1.98` et préparer Caddy pour le domaine.

## Prochain ticket recommandé

`FW-ROUTER-PORTS-AUDIT-001 — Vérifier la redirection 80/443 vers la VM forge-web`.
