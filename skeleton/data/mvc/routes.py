# pyright: strict
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from optins.registry import register_optins

router = Router()

with router.group("", public=True) as public:
    public.add("GET", "/", HomeController.index, name="home-index")

# Branche les routes des opt-ins « route » activés (ADR-061). No-op tant
# qu'aucun opt-in route n'est activé (forge opt-in:enable <name>).
register_optins(router)
