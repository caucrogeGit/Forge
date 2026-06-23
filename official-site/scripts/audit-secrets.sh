#!/usr/bin/env bash
# Audit reproductible de l'exposition de secrets dans le dépôt Forge-official-site.
#
# Vérifie qu'aucun secret permettant d'accéder à la VM de production
# n'est suivi par Git ou présent dans l'historique.
#
# Sortie : rapport texte sur stdout, code de sortie 0 si propre, 1 sinon.
#
# Référence : FORGE-WEB-SECRET-EXPOSURE-AUDIT-001
#             docs/security/deployment-secrets.md

set -uo pipefail

cd "$(dirname "$0")/.."

EXIT_CODE=0

EXCLUDES=(
  --exclude-dir=.git
  --exclude-dir=node_modules
  --exclude-dir=site
  --exclude-dir=dist
  --exclude-dir=build
  --exclude-dir=.venv
  --exclude-dir=venv
  --exclude-dir=.claude
  --exclude-dir=__pycache__
)

section() {
  printf '\n=== %s ===\n' "$1"
}

fail() {
  printf '  KO: %s\n' "$1"
  EXIT_CODE=1
}

ok() {
  printf '  ok: %s\n' "$1"
}

section "1. Fichiers sensibles suivis par Git"
SENSITIVE_TRACKED=$(git ls-files | grep -Ei \
  '(^|/)(\.env|\.env\..*|id_rsa|id_ed25519|.*\.pem|.*\.key|.*\.p12|.*\.pfx|credentials|secrets|authkey|cloudflare|tailscale|sshpass|known_hosts|authorized_keys)$' \
  | grep -vEi '\.example$|example\.' || true)
if [[ -z "$SENSITIVE_TRACKED" ]]; then
  ok "aucun fichier sensible suivi"
else
  fail "fichiers sensibles suivis :"
  printf '%s\n' "$SENSITIVE_TRACKED" | sed 's/^/    /'
fi

section "2. Dossiers de build/cache suivis par Git"
BUILD_TRACKED=$(git ls-files | grep -E '^(site|dist|node_modules|\.venv|\.cache|\.claude)/' || true)
if [[ -z "$BUILD_TRACKED" ]]; then
  ok "aucun dossier de build/cache suivi"
else
  fail "dossiers de build/cache suivis :"
  printf '%s\n' "$BUILD_TRACKED" | head -10 | sed 's/^/    /'
fi

section "3. Motifs de secrets fortement signifiants"
HARD_PATTERNS='(BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|sshpass +[^$"{ ]|tskey-[a-zA-Z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|sk_live_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{20,})'
HARD_MATCHES=$(grep -RInE "$HARD_PATTERNS" . "${EXCLUDES[@]}" \
  --exclude=audit-secrets.sh \
  --exclude=forge-web-secret-exposure-audit.md \
  --exclude=deployment-secrets.md \
  2>/dev/null || true)
if [[ -z "$HARD_MATCHES" ]]; then
  ok "aucun motif de secret réel détecté"
else
  fail "motifs de secrets potentiels :"
  printf '%s\n' "$HARD_MATCHES" | head -20 | sed 's/^/    /'
fi

section "4. Mentions Tailscale / Cloudflare / DNS tokens"
SOFT_PATTERNS='(tailscale.*auth|authkey *= *[^$"]+|CF_API[_A-Z0-9]*KEY *= *[^$"]+|CLOUDFLARE_API[_A-Z0-9]*TOKEN *= *[^$"]+|DDNS_TOKEN *= *[^$"]+)'
SOFT_MATCHES=$(grep -RInE "$SOFT_PATTERNS" . "${EXCLUDES[@]}" \
  --exclude=audit-secrets.sh \
  --exclude=forge-web-secret-exposure-audit.md \
  --exclude=deployment-secrets.md \
  2>/dev/null || true)
if [[ -z "$SOFT_MATCHES" ]]; then
  ok "aucun token DNS/Tailscale/Cloudflare assigné"
else
  fail "tokens DNS/Tailscale/Cloudflare possiblement assignés :"
  printf '%s\n' "$SOFT_MATCHES" | head -20 | sed 's/^/    /'
fi

section "5. Couverture .gitignore"
GITIGNORE_REQUIRED=(
  '.env'
  '.env.*'
  '*.pem'
  '*.key'
  'id_rsa'
  'id_ed25519'
  'secrets/'
  'credentials/'
  'site/'
  'dist/'
  'node_modules/'
  '.venv/'
)
MISSING_IGNORES=()
for pat in "${GITIGNORE_REQUIRED[@]}"; do
  if ! grep -Fxq "$pat" .gitignore; then
    MISSING_IGNORES+=("$pat")
  fi
done
if [[ ${#MISSING_IGNORES[@]} -eq 0 ]]; then
  ok ".gitignore couvre les motifs requis"
else
  fail "motifs absents de .gitignore :"
  printf '    %s\n' "${MISSING_IGNORES[@]}"
fi

section "6. Workflows GitHub Actions"
if [[ -d .github ]]; then
  WF_LEAKS=$(grep -RInE \
    '(ssh-rsa AAAA|BEGIN .* PRIVATE KEY|tskey-[a-zA-Z0-9]+|ghp_[A-Za-z0-9]+|password *: *[^$"{][^$"}]+|tailscale.*authkey *: *[^$"{][^$"}]+)' \
    .github 2>/dev/null || true)
  if [[ -z "$WF_LEAKS" ]]; then
    ok ".github présent, aucun secret inline détecté"
  else
    fail "secrets inline potentiels dans .github :"
    printf '%s\n' "$WF_LEAKS" | sed 's/^/    /'
  fi
else
  ok "aucun dossier .github (pas de workflow GitHub Actions)"
fi

section "7. Historique Git — noms sensibles"
HIST=$(git log --all --name-only --pretty=format: | sort -u \
  | grep -Ei '(^|/)(\.env|id_rsa|id_ed25519|.*\.pem|.*\.key|credentials|authkey|\.p12|\.pfx)$' \
  | grep -vEi '\.example$|example\.' || true)
if [[ -z "$HIST" ]]; then
  ok "aucun fichier sensible jamais commité"
else
  fail "fichiers sensibles présents dans l'historique :"
  printf '%s\n' "$HIST" | sed 's/^/    /'
fi

section "Résumé"
if [[ $EXIT_CODE -eq 0 ]]; then
  printf '  GO — aucun secret de déploiement détecté dans le dépôt.\n'
else
  printf '  NO-GO — au moins un point bloquant. Voir détails ci-dessus.\n'
fi

exit "$EXIT_CODE"
