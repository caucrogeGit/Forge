# Audit exposition secrets — Forge-web

- **Ticket** : `FORGE-WEB-SECRET-EXPOSURE-AUDIT-001`
- **Date** : 2026-05-25
- **Dépôt** : `Forge-web` / cible `Forge-official-site`
- **Branche** : `main` — working tree propre

## Résumé

L'audit confirme que le dépôt `Forge-web` ne contient **aucun secret
permettant d'accéder à la VM `forge-web`**. Un développeur disposant
uniquement d'un clone du dépôt ne peut pas se connecter à la VM, prendre
la main sur le DNS / Cloudflare, ni déclencher un déploiement non
authentifié.

Verdict global : **GO**.

## État Git

- Remote : `git@github.com:caucrogeGit/Forge-web.git` (SSH).
- Branche courante : `main`.
- Working tree : propre.
- Commits totaux dans toutes les branches : 24.
- Derniers commits : sync documentation Forge beta.9 / beta.8, audits de
  publication. Aucun commit ne porte un nom évocateur de secret.

## Secrets recherchés

Catégories couvertes par les recherches `grep` et `git log` :

- clés SSH privées (RSA, OPENSSH, EC, DSA) ;
- mots de passe hard-codés ;
- tokens GitHub (`ghp_`, `gho_`, `ghs_`) ;
- authkeys Tailscale (`tskey-...`) ;
- tokens Cloudflare / DNS (`CF_API_*`, `CLOUDFLARE_API_*`, `DDNS_TOKEN`) ;
- tokens AWS (`AKIA...`), Stripe (`sk_live_...`), Slack (`xox[abp]-`) ;
- références `sshpass`, `expect` avec mot de passe ;
- fichiers `.env`, `*.key`, `*.pem`, `id_rsa*`, `id_ed25519*`, `credentials`,
  `secrets/`, `authorized_keys`, `known_hosts`.

## Fichiers sensibles suivis

```bash
git ls-files | grep -Ei '(^|/)(\.env|id_rsa|id_ed25519|.*\.pem|.*\.key|credentials|secrets|authkey|sshpass|known_hosts|authorized_keys)$'
```

Résultat : **aucun**.

Aucun fichier au format clé/cert n'existe non plus en local hors `.git` :

```bash
find . -path ./.git -prune -o ... -type f \( -name "*.env*" -o -name "*.key" ... \) -print
```

Résultat : aucun.

## Résultats grep

### Motifs forts (clés privées, tokens encodés)

Aucune correspondance. Les seules mentions de `BEGIN PRIVATE KEY`, `tskey-`,
`ghp_`, `AKIA*` apparaissent uniquement dans des patterns d'audit
(`scripts/audit-secrets.sh` et ce rapport).

### Motifs nominaux (`SECRET`, `TOKEN`, `PASSWORD`)

Toutes les occurrences sont **documentaires** :

- `docs/forge/api-json.md` : décrit la variable d'environnement `API_TOKEN`
  et insiste sur le fait de **ne jamais la versionner**.
- `docs/forge/reference/auth-mfa.md` et `docs/forge/auth.md` : documentent
  `FORGE_MFA_SECRET_KEY` comme variable d'environnement requise.
- `docs/forge/mail.md` : documente `MAIL_PASSWORD` avec une valeur
  placeholder `votre_mot_de_passe`.
- `docs/forge/reference/tests-e2e.md` : exemple `FORGE_E2E_DB_PASSWORD=secret`
  destiné aux tests locaux, pas un mot de passe réel.
- ID de tickets historiques (`SEC-MFA-SECRET-ENCRYPTION-001`,
  `PYPI-TOKEN-001`, etc.) — pas de valeurs.

Aucune valeur de secret réelle n'est assignée.

### Commandes de déploiement

- `scripts/deploy-to-forge-web.sh` utilise par défaut
  `REMOTE_HOST="roger@192.168.1.98"` et `rsync`/`ssh` avec
  authentification par **clé SSH locale du développeur** — pas de
  `sshpass`, pas de clé baked-in, pas de mot de passe.
- Documentation `docs/audits/FW-*` mentionne l'IP LAN `192.168.1.98` et le
  chemin `/srv/forge-web/current`. Ces éléments sont des **coordonnées
  d'hôte**, pas des secrets : connaître l'IP LAN d'un hôte sur un réseau
  privé ne donne pas accès à cet hôte sans clé.
- `docs/forge/wsgi-deployment.md:131` : exemple
  `APP_TRUSTED_PROXIES=127.0.0.1, ::1, 10.0.0.5` — exemple générique de
  configuration applicative, pas une donnée d'infrastructure réelle.

## GitHub Actions

Aucun dossier `.github/` présent dans le dépôt. Pas de workflow, donc :

- pas de secret inline ;
- pas de référence `${{ secrets.* }}` à auditer ;
- aucun déploiement automatique vers la VM via GitHub.

Si un workflow est ajouté plus tard, la politique
[`docs/security/deployment-secrets.md`](../security/deployment-secrets.md)
impose l'usage exclusif de `${{ secrets.* }}`.

## Historique Git

```bash
git log --all --name-only --pretty=format: | sort -u \
  | grep -Ei '(^|/)(\.env|id_rsa|id_ed25519|.*\.pem|.*\.key|credentials|secret|secrets|token|authkey)'
```

Résultat : **aucun fichier sensible n'a jamais été suivi**.

Recherche complémentaire sur les diffs ajoutés :

```bash
git log --all -p --diff-filter=AM | grep -E '^\+' \
  | grep -iE '(BEGIN .* PRIVATE KEY|sshpass |tskey-|ghp_|gho_|ghs_|AKIA)'
```

Résultat : aucune correspondance.

L'historique court (24 commits) ne pose pas de risque caché.

## Gitleaks

`gitleaks` **n'est pas installé** sur la machine de dev. Recommandation
optionnelle : si l'outil est installé plus tard, le passage

```bash
gitleaks detect --source . --redact
gitleaks detect --source . --no-git --redact
```

doit rester silencieux. Tant qu'il n'est pas disponible,
`scripts/audit-secrets.sh` couvre les cas critiques.

## Corrections appliquées

1. **`.gitignore` étendu** pour ignorer explicitement `id_rsa`, `id_rsa.*`,
   `id_ed25519`, `id_ed25519.*`, `*.p12`, `*.pfx`, et `credentials/`.
   Les patterns `*.key`, `*.pem`, `*.crt`, `secrets/`, `.env*` étaient
   déjà couverts.
2. **Création de `scripts/audit-secrets.sh`** —
   script d'audit reproductible. Codes de sortie : 0 (GO) ou 1 (NO-GO).
3. **Création de [`docs/security/deployment-secrets.md`](../security/deployment-secrets.md)** —
   politique secrets de déploiement.

Aucun secret n'a dû être révoqué — il n'y en avait aucun à révoquer.

## Risques restants

Risques **non bloquants** identifiés pour information :

- L'IP LAN `192.168.1.98` est publiée dans la documentation. Ce n'est pas
  un secret, mais elle informe un attaquant que la VM est joignable sur
  ce préfixe — utile seulement à un attaquant déjà présent dans le LAN.
  Décision : pas d'action — la documentation de procédure a une valeur
  opérationnelle qui prime.
- Le script `scripts/deploy-to-forge-web.sh` repose sur la disponibilité
  d'une clé SSH locale chez le développeur. Si un développeur supplémentaire
  obtient demain accès en écriture au dépôt, il n'aura pas pour autant
  accès à la VM — il faudra explicitement provisionner sa clé publique côté
  VM. Ce point est exactement la propriété cherchée.
- Pas de hook git pré-commit empêchant l'ajout futur d'un secret. Un suivi
  possible serait `pre-commit` + `gitleaks` ; hors périmètre de ce ticket.

## Verdict

**GO** — le dépôt `Forge-web` ne contient aucun secret permettant
d'accéder à la VM. Aucun accès VM possible depuis le dépôt seul.

Exécution du garde-fou :

```text
=== 1. Fichiers sensibles suivis par Git ===
  ok: aucun fichier sensible suivi
=== 2. Dossiers de build/cache suivis par Git ===
  ok: aucun dossier de build/cache suivi
=== 3. Motifs de secrets fortement signifiants ===
  ok: aucun motif de secret réel détecté
=== 4. Mentions Tailscale / Cloudflare / DNS tokens ===
  ok: aucun token DNS/Tailscale/Cloudflare assigné
=== 5. Couverture .gitignore ===
  ok: .gitignore couvre les motifs requis
=== 6. Workflows GitHub Actions ===
  ok: aucun dossier .github (pas de workflow GitHub Actions)
=== 7. Historique Git — noms sensibles ===
  ok: aucun fichier sensible jamais commité
=== Résumé ===
  GO — aucun secret de déploiement détecté dans le dépôt.
```
