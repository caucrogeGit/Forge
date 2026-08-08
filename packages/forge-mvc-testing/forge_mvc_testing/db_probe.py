# pyright: strict
"""Motifs de saut des tests d'intégration BDD (TEST-DB-SKIP-REASON-001).

Les fixtures d'intégration rangeaient toute erreur de connexion sous un mot
unique, « injoignable », et leur commentaire assumait la confusion. Or « pas de
serveur » et « serveur qui refuse mes identifiants » appellent deux gestes
opposés, démarrer un service dans un cas, corriger une variable d'environnement
dans l'autre.

Le coût est réel et mesuré. Un lecteur de bonne foi conclut que le serveur est
arrêté, tente de le démarrer, constate qu'il tourne déjà, et cherche ailleurs.
En CI le point est masqué, `FORGE_REQUIRE_DB=1` transformant le saut en échec ;
en local il produit un faux diagnostic sans le moindre signal.

Ce module classe l'erreur et rédige un motif qui **nomme le geste attendu**. Il
vit dans `forge-mvc-testing` (ADR-041) plutôt que recopié dans chacune des douze
fixtures, la duplication étant précisément ce qui avait laissé le défaut
s'installer partout à l'identique.
"""
from __future__ import annotations

__all__ = [
    "CAUSE_AUTH",
    "CAUSE_UNREACHABLE",
    "CAUSE_UNKNOWN",
    "classify_connection_error",
    "connection_failure_message",
]

#: Le serveur répond, mais refuse les identifiants présentés.
CAUSE_AUTH = "auth"
#: Aucun serveur n'a répondu.
CAUSE_UNREACHABLE = "unreachable"
#: Ni l'un ni l'autre n'est reconnaissable.
CAUSE_UNKNOWN = "unknown"

# Signatures textuelles des trois pilotes. Aucun code d'erreur n'est portable,
# et le SQLSTATE ne discrimine pas davantage ici que pour les doublons
# (`UNIQUE-VIOLATION-PORTABLE-001`). Le texte reste le signal le plus fiable.
_AUTH_SIGNATURES = (
    "access denied",              # MariaDB, MySQL
    "authentication failed",      # PostgreSQL
    "login failed for user",      # SQL Server
    "18456",                      # SQL Server, numéro de « login failed »
    "auth_plugin",                # MariaDB, greffon d'authentification refusé
    "not allowed to connect",     # MariaDB, hôte non autorisé
)

_UNREACHABLE_SIGNATURES = (
    "can't connect",
    "cannot connect",
    "could not connect",
    "unable to connect",
    "connection refused",
    "no such host",
    "name or service not known",
    "timed out",
    "timeout expired",
    "network-related or instance-specific",   # SQL Server
    "server closed the connection",
)


def classify_connection_error(error: Exception) -> str:
    """Range l'erreur en :data:`CAUSE_AUTH`, :data:`CAUSE_UNREACHABLE` ou inconnu.

    L'authentification est testée **en premier**. Un refus d'identifiants prouve
    que le serveur répond, et certains messages de refus contiennent aussi le
    mot « connect », ce qui les ferait passer à tort pour une absence de serveur.
    """
    texte = str(error).lower()
    if any(signature in texte for signature in _AUTH_SIGNATURES):
        return CAUSE_AUTH
    if any(signature in texte for signature in _UNREACHABLE_SIGNATURES):
        return CAUSE_UNREACHABLE
    return CAUSE_UNKNOWN


def connection_failure_message(
    server_label: str,
    error: Exception,
    *,
    env_prefix: str,
) -> str:
    """Motif de saut ou d'échec, nommant le geste attendu.

    `server_label` nomme le serveur (« MariaDB »), `env_prefix` la famille de
    variables qui le configure (« FORGE_TEST_DB »), de sorte que le lecteur
    dispose du nom exact à poser sans avoir à ouvrir la fixture.
    """
    cause = classify_connection_error(error)
    if cause == CAUSE_AUTH:
        return (
            f"{server_label} de test RÉPOND mais refuse les identifiants : {error}. "
            f"Le serveur tourne, inutile de le démarrer. "
            f"Posez {env_prefix}_PASSWORD, et au besoin {env_prefix}_USER."
        )
    if cause == CAUSE_UNREACHABLE:
        return (
            f"{server_label} de test injoignable : {error}. "
            f"Démarrez le serveur, ou vérifiez {env_prefix}_HOST et {env_prefix}_PORT."
        )
    return (
        f"{server_label} de test inaccessible : {error}. "
        f"Vérifiez que le serveur tourne, puis les variables {env_prefix}_*."
    )
