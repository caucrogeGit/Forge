# pyright: strict
"""Exceptions Auth Forge."""

from __future__ import annotations


class AuthError(ValueError):
    """Erreur de base du module auth Forge."""


class InvalidAuthUserError(AuthError):
    """Données utilisateur incomplètes ou invalides."""


class InvalidAuthAuditEventError(AuthError):
    """Donnees evenement audit Auth/User incompletes ou invalides."""


class InvalidAuthRateLimitAttemptError(AuthError):
    """Donnees tentative rate limit Auth/User incompletes ou invalides."""


class InvalidAuthRateLimitRuleError(AuthError):
    """Donnees regle rate limit Auth/User incompletes ou invalides."""


class InvalidNewPasswordError(AuthError):
    """Nouveau mot de passe invalide."""


class InvalidMfaFactorError(AuthError):
    """Donnees de facteur MFA incompletes ou invalides."""


class InvalidMfaRecoveryCodeError(AuthError):
    """Donnees de code de recuperation MFA incompletes ou invalides."""
