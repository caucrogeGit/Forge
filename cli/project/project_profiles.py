# pyright: strict
"""Contrat des profils de projet Forge.

Ces constantes définissent les profils officiels et leur description.
L'option --profile de `forge new` est disponible depuis PROFILE-002.
Le profil choisi est enregistré dans forge_profile.txt à la racine du projet.
"""

from __future__ import annotations

SUPPORTED_PROJECT_PROFILES: tuple[str, ...] = (
    "minimal",
    "standard",
    "dynamic",
    "multilingual",
    "auth-mfa",
)

DEFAULT_PROJECT_PROFILE: str = "standard"

PROJECT_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "minimal": (
        "Projet Forge le plus simple possible. "
        "Structure MVC de base, sans composants avancés ni exemple métier."
    ),
    "standard": (
        "Projet Forge recommandé pour une application classique. "
        "Layout public/admin, formulaires, flash, pagination."
    ),
    "dynamic": (
        "Projet Forge avec interactions front légères. "
        "Contenu du profil standard enrichi de HTMX et Alpine.js optionnel."
    ),
    "multilingual": (
        "Projet Forge prêt pour l'internationalisation. "
        "Contenu du profil standard avec i18n initialisée et translations/fr.json."
    ),
    "auth-mfa": (
        "Projet Forge avec authentification MFA (TOTP) activée. "
        "Même base que standard. Voir la progression welcome-mfa pour construire les contrôleurs MFA à la main."
    ),
}
