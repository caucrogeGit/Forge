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
| [ADR-017](017-slug-type.md) | Type `slug` et module URL-slug canonique (`core/http/slug.py`) |
| [ADR-018](018-image-module-extraction.md) | Extraction du traitement d'image hors du core : `forge-mvc-images` (proposé) |
| [ADR-019](019-upload-extraction.md) | Extraction de l'upload générique hors du core : `forge-mvc-files` (proposé) |
| [ADR-020](020-files-media-storage-primitives.md) | Périmètre de `forge-mvc-files` : primitives de stockage média génériques (proposé) |
| [ADR-021](021-pivot-extraction.md) | Extraction de pivot advanced hors du core : `forge-mvc-pivot` (accepté) |
| [ADR-022](022-mail-extraction.md) | Extraction de l'email hors du core : `forge-mvc-mail` (accepté) |
