# Politique secrets de déploiement — Forge-official-site

## Principe

Le dépôt `Forge-official-site` ne contient **aucun secret permettant d'accéder à la
VM de production**.

Un développeur disposant uniquement d'un clone du dépôt ne doit pas pouvoir
obtenir d'accès direct à :

- la VM `forge-web` / `Forge-official-site` ;
- le serveur web Caddy en production ;
- le DNS / Cloudflare ;
- Tailscale ;
- GitHub Actions de déploiement ;
- tout autre système connecté à la VM.

## Interdits dans le dépôt

- clés SSH privées (`id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`, `*.pfx`) ;
- mots de passe en clair ;
- tokens DNS / Cloudflare (`CF_API_TOKEN`, `CLOUDFLARE_API_KEY`, `DDNS_TOKEN`) ;
- authkeys Tailscale (`tskey-...`) ;
- fichiers `.env` réels (toute valeur non placeholder) ;
- credentials de déploiement, fichiers `credentials/`, dossiers `secrets/` ;
- commandes `sshpass`, `expect` avec mot de passe, ou toute méthode
  d'authentification baked-in dans un script ;
- tokens GitHub (`ghp_*`, `gho_*`, `ghs_*`).

## Autorisés

- fichiers exemples nommés explicitement `.example`, `*.example.*` ou
  `*example*`, **sans aucune valeur de secret réelle** ;
- noms de variables d'environnement (`API_TOKEN`, `MAIL_PASSWORD`,
  `FORGE_MFA_SECRET_KEY`, etc.) — ce sont des références, pas des valeurs ;
- scripts de déploiement (`scripts/deploy-to-forge-web.sh`) tant qu'ils
  s'appuient sur l'authentification SSH locale du développeur (clé hors
  dépôt) et ne contiennent aucun mot de passe ;
- documentation de procédure mentionnant l'IP LAN `192.168.1.98` ou les
  chemins `/srv/forge-web/current` — il s'agit de coordonnées d'hôte, pas
  d'éléments d'authentification.

## Modèle de déploiement

Le déploiement `dist/` → VM `forge-web` se fait via `rsync`/`ssh` en
utilisant **la clé SSH locale du développeur**, jamais une clé embarquée
dans le dépôt.

L'autorisation côté VM est gérée hors dépôt via `~/.ssh/authorized_keys`
sur la VM cible. Le dépôt ne décrit pas comment cette clé est provisionnée,
et c'est volontaire.

Aucun déploiement automatique GitHub Actions n'est configuré. Si un workflow
est ajouté plus tard, les secrets doivent passer exclusivement par
`${{ secrets.* }}` (GitHub Secrets) — jamais inline.

## Que faire si un secret a été commité

1. **Considérer le secret compromis.** Quelqu'un peut déjà l'avoir vu via
   le clone, le `git log`, ou un cache GitHub.
2. **Le révoquer immédiatement** sur le système concerné (rotation de clé
   SSH côté VM, rotation du token, etc.).
3. **Générer un nouveau secret** et le déployer hors dépôt.
4. **Décider** si la purge d'historique (`git filter-repo`, BFG) est
   nécessaire — ce n'est utile que si le secret n'a pas pu être révoqué.
5. **Documenter** l'incident dans `docs/audits/`.

Ne jamais simplement « supprimer le fichier » sans rotation du secret.

## Garde-fou automatique

Le script `scripts/audit-secrets.sh` doit être exécutable à tout moment :

```bash
bash scripts/audit-secrets.sh
```

Il vérifie les fichiers suivis, les motifs de secrets, l'historique Git et
la couverture `.gitignore`. Code de sortie 0 = GO, 1 = NO-GO.

## Référence

- Ticket initial : `FORGE-WEB-SECRET-EXPOSURE-AUDIT-001`.
- Rapport d'audit : [`docs/audits/forge-web-secret-exposure-audit.md`](../audits/forge-web-secret-exposure-audit.md).
