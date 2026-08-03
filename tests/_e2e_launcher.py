"""
Lanceur de serveur Forge pour les tests E2E.

Lancé en sous-processus par les fixtures `forge_server` de `tests/`.
Lit le port depuis TEST_PORT (non surchargé par dotenv).
Démarre ThreadingHTTPServer sur ce port.

E2E-LAUNCHER-APP-PATH-001 — l'application servie vit dans
`tests/fixtures/app/`. Elle était à la racine du dépôt jusqu'à l'ADR-044, qui
l'a relocalisée en fixture le 2026-06-23 ; ce lanceur a continué de la chercher
à la racine.

Le sous-processus mourait sur `FileNotFoundError`, son `stderr` était jeté par
l'appelant, et l'absence de `READY:` se traduisait en `pytest.skip("Serveur
Forge non disponible")`. Soixante-cinq tests, dont les trente-trois d'en-têtes
de sécurité, ne s'exécutaient donc plus nulle part, en affichant le vocabulaire
d'un poste local mal équipé.

Le chemin est résolu ici, en un seul endroit, et une absence est signalée par un
message explicite plutôt que par une trace tronquée.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

#: Application de dogfooding servie par les tests E2E (ADR-044).
APP_DIR = ROOT / "tests" / "fixtures" / "app"
APP_FILE = APP_DIR / "app.py"

# TEST_PORT n'est jamais dans les fichiers env → jamais surchargé par load_dotenv
test_port = int(os.environ.get("TEST_PORT", 0))
if not test_port:
    print("ERROR: TEST_PORT non défini", file=sys.stderr, flush=True)
    sys.exit(1)

# APP_ENV posé avant tout import de config/app — setdefault respecte cette valeur
os.environ.setdefault("APP_ENV", "prod")

logging.basicConfig(level=logging.CRITICAL)

if not APP_FILE.is_file():
    print(f"ERROR: application E2E introuvable : {APP_FILE}", file=sys.stderr, flush=True)
    sys.exit(2)

# L'application lit `config`, `env/`, `static/` et `storage/` en relatif : elle
# doit être importable ET courante, sinon elle échoue sur `No module named
# 'config'` bien après la résolution du chemin.
os.chdir(APP_DIR)
sys.path.insert(0, str(APP_DIR))

# Import app.py sans déclencher le bloc __main__ (nom ≠ "__main__")
spec = importlib.util.spec_from_file_location("_forge_app_e2e", APP_FILE)
mod = importlib.util.module_from_spec(spec)
sys.modules["_forge_app_e2e"] = mod
spec.loader.exec_module(mod)

ThreadingHTTPServer.allow_reuse_address = True
server = ThreadingHTTPServer(("127.0.0.1", test_port), mod.RequestHandler)

# Signale la disponibilité au processus parent
print(f"READY:{test_port}", flush=True)

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
