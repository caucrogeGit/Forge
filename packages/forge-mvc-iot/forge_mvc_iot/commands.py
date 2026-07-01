# pyright: strict
"""Commandes CLI livrées par forge-mvc-iot, découvertes par le cœur (ADR-059).

Table déclarative légère (chaînes uniquement, aucun import lourd) exposée via
l'entry point ``forge_mvc.commands``. Le cœur (dispatch_optin) la découvre et
importe le handler paresseusement à l'invocation. Clés par commande :

- ``module`` : module à importer paresseusement (obligatoire) ;
- ``attr`` : appelable dans le module (défaut ``main``) ;
- ``full`` : passe les arguments complets, commande incluse (défaut ``False``) ;
- ``exit_rc`` : ``sys.exit(rc)`` si le handler renvoie un code non nul (défaut ``True``).
"""
from __future__ import annotations

COMMANDS: dict[str, dict[str, str | bool]] = {
    "iot:doctor": {"module": "forge_mvc_iot.cli.doctor"},
    "iot:init": {"module": "forge_mvc_iot.cli.init"},
    "iot:simulate": {"module": "forge_mvc_iot.cli.simulate"},
    "iot:listen": {"module": "forge_mvc_iot.cli.listen"},
}
