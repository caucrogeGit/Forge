# Décisions d'architecture (ADR)

Les *Architecture Decision Records* documentent les décisions structurantes
de Forge. Chaque ADR a **force décisionnelle** : à lire avant toute
proposition qui le concerne. Un nouvel ADR est requis pour toute décision
structurante (`docs/adr/<numéro>-<sujet>.md`).

| Numéro | Sujet |
|---|---|
| [ADR-001](001-auth-strategy.md) | Stratégie d'authentification |
| [ADR-002](002-session-strategy.md) | Stockage de session |
| [ADR-003](003-language-convention.md) | API publique en anglais |
| [ADR-004](004-core-perimeter.md) | Périmètre du core minimal strict |
| [ADR-005](005-packaging.md) | Packaging hybride monorepo + multi-distributions PyPI |
| [ADR-006](006-python-version.md) | Python 3.12+ minimum |
| [ADR-007](007-charter-v2-adoption.md) | Adoption formelle de la charte v2 |
| [ADR-008](008-auth-audit-architecture.md) | Audit auth : logging fourni, persistance applicative |
| [ADR-009](009-stability-policy-terrain.md) | Politique de stabilité : audits, bêta consolidée, tests terrain |
| [ADR-010](010-auth-session-canonical-api.md) | API canonique auth/session |
| [ADR-011](011-auth-audit-vocab-perimeter.md) | Périmètre du vocabulaire d'audit auth |
| [ADR-012](012-legacy-format-deprecation-policy.md) | Politique de dépréciation du format legacy |
| [ADR-013](013-nullable-required-contract-policy.md) | Politique nullable / required des contrats |
| [ADR-014](014-rbac-contract-location.md) | Emplacement du contrat RBAC |
| [ADR-015](015-dev-tls-handshake-per-thread.md) | Handshake TLS par thread (dev-server) |
| [ADR-016](016-opt-in-unification.md) | Unification du modèle opt-in : concept unique, cycle install/enable à 4 verbes |
