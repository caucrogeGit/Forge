# pyright: strict
"""Conseils d'activation/désactivation selon le kind d'un opt-in.

Ticket : OPTIN-KIND-ADAPTER-001 (ADR-016, palier 4a).

Seuls les opt-ins de kind ``route`` (iot) ont un câblage projet réel (couche
``optins/``). Pour les bibliothèques et les transversaux, ``opt-in:enable`` /
``opt-in:disable`` n'écrivent rien : ils **informent** sur la façon d'utiliser
ou de retirer la brique. Pas de cérémonie vide (principe §8).
"""
from __future__ import annotations

from cli.optins.catalog import KIND_CROSSCUTTING, KIND_LIBRARY, OptIn


def enable_guidance(optin: OptIn) -> str:
    """Message d'activation pour un opt-in non-routier (library/crosscutting)."""
    if optin.kind == KIND_LIBRARY:
        return (
            f"Opt-in « {optin.name} » (bibliothèque) — aucun câblage projet.\n"
            f"Importe-le et utilise ses fonctions directement :\n"
            f"    import {optin.package_import}\n"
            f"Rien à activer ni à désactiver côté projet."
        )
    if optin.kind == KIND_CROSSCUTTING:
        if optin.name == "rbac":
            return (
                "Opt-in « rbac » (transversal) — s'applique par décorateurs.\n"
                "Le provider Jinja can() se branche au chargement du paquet\n"
                "(mécanisme plugin : le core ne dépend pas de rbac).\n"
                "Protège tes routes : @require_permission(...) sur tes contrôleurs.\n"
                "\n"
                "Valider mvc/security/rbac.json dans VS Code (optionnel) — le schéma\n"
                "rbac n'est pas dans le squelette nu (c'est un opt-in), forge-mvc le\n"
                "fournit :\n"
                "  1. Copie le schéma dans schemas/ de ton projet :\n"
                """       python -c "import forge_mvc_rbac, pathlib, shutil; shutil.copy(pathlib.Path(forge_mvc_rbac.__file__).parent / 'schemas' / 'rbac.schema.json', 'schemas/rbac.schema.json')"\n"""
                "  2. Ajoute l'association dans .vscode/settings.json (Forge ne modifie\n"
                "     pas ce fichier), dans le tableau json.schemas existant :\n"
                """       { "fileMatch": ["/mvc/security/rbac.json"], "url": "./schemas/rbac.schema.json" }"""
            )
        if optin.name == "mfa":
            return (
                "Opt-in « mfa » (transversal) — découvre-le via le parcours manuel\n"
                "dédié : la progression welcome-mfa dans la documentation\n"
                "(réalisée à la main, ADR-035).\n"
                "Le parcours welcome-mfa montre chaque brique TOTP (secret,\n"
                "enrôlement, challenge, récupération) à câbler dans ton flux d'auth."
            )
    return f"Opt-in « {optin.name} » — voir la documentation."


def disable_guidance(optin: OptIn) -> str:
    """Message de désactivation pour un opt-in non-routier."""
    if optin.kind == KIND_LIBRARY:
        return (
            f"Opt-in « {optin.name} » (bibliothèque) — rien à débrancher côté projet.\n"
            f"Retire ses imports de ton code ; "
            f"`forge opt-in:remove {optin.name}` pour le package."
        )
    if optin.kind == KIND_CROSSCUTTING:
        return (
            f"Opt-in « {optin.name} » (transversal) — retire son câblage de ton code\n"
            f"(décorateurs / starter), puis `forge opt-in:remove {optin.name}`."
        )
    return f"Opt-in « {optin.name} » — voir la documentation."
