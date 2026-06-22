"""Garde-fou STARTER-LANG-NORMALIZE-001.

Vérifie que les starters respectent la convention de frontière linguistique :
- le schéma SQL reste français (noms de colonnes) ;
- les variables Python et les clés de contexte de template utilisent des noms
  canoniques anglais ou normalisés ;
- les API dépréciées (get_user, authenticate_session) ne sont pas utilisées ;
- les starters actifs exposent build_auth_user() pour l'isolation du mapping SQL.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTERS = PROJECT_ROOT / "cli" / "starters" / "data"

# Les classes TestUsersCoreAuthReference, TestAuthMfaController et
# TestMfaChallengeController ont été retirées : elles inspectaient les starters
# supprimés `users-core-auth` et `welcome-optin-mfa`.
