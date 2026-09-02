# pyright: strict
"""Commandes CLI de forge-mvc-qrcode, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands`` ; le
cœur (dispatch_optin) importe le handler paresseusement à l'invocation.
"""
from __future__ import annotations

# qrcode:make n'ouvre aucune connexion : le paquet est sans état, et la
# commande ne fait que produire un fichier (pas de `config: True`).
COMMANDS: dict[str, dict[str, str | bool]] = {
    "qrcode:make": {"module": "forge_mvc_qrcode.cli.make"},
}
