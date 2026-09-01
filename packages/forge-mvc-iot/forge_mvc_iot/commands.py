# pyright: strict
"""Commandes CLI livrées par forge-mvc-iot, découvertes par le cœur (ADR-059).

Table déclarative légère (chaînes uniquement, aucun import lourd) exposée via
l'entry point ``forge_mvc.commands``. Le cœur (dispatch_optin) la découvre et
importe le handler paresseusement à l'invocation. Clés par commande :

- ``module`` : module à importer paresseusement (obligatoire) ;
- ``attr`` : appelable dans le module (défaut ``main``) ;
- ``full`` : passe les arguments complets, commande incluse (défaut ``False``) ;
- ``exit_rc`` : ``sys.exit(rc)`` si le handler renvoie un code non nul (défaut ``True``) ;
- ``config`` : amorce la config projet (``env/dev``) avant le handler (défaut ``False``),
  pour les commandes adossées à la base (ADR-072, retour terrain 016 F39).
"""
from __future__ import annotations

# `iot:listen` insère les mesures reçues dans `iot_events` : il ouvre une connexion
# BDD et a besoin des identifiants applicatifs d'env/dev (config: True, ADR-072).
# iot:doctor est un diagnostic statique par défaut (--db/--mqtt gérés gracieusement),
# iot:simulate ne fait que publier en MQTT, iot:init copie une migration : aucun n'amorce.
COMMANDS: dict[str, dict[str, str | bool]] = {
    "iot:doctor": {"module": "forge_mvc_iot.cli.doctor"},
    "iot:init": {"module": "forge_mvc_iot.cli.init"},
    "iot:simulate": {"module": "forge_mvc_iot.cli.simulate"},
    "iot:listen": {"module": "forge_mvc_iot.cli.listen", "config": True},
    # iot:gc compte puis supprime dans `iot_events` : connexion BDD requise.
    "iot:gc": {"module": "forge_mvc_iot.cli.gc", "config": True},
}
