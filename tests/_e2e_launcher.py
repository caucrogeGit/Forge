"""
Lanceur de serveur Forge pour les tests E2E.

Importé en sous-processus par tests/test_http_e2e_001.py.
Lit le port depuis TEST_PORT (non surchargé par dotenv).
Démarre ThreadingHTTPServer sur ce port.
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

# TEST_PORT n'est jamais dans les fichiers env → jamais surchargé par load_dotenv
test_port = int(os.environ.get("TEST_PORT", 0))
if not test_port:
    print("ERROR: TEST_PORT non défini", file=sys.stderr, flush=True)
    sys.exit(1)

# APP_ENV posé avant tout import de config/app — setdefault respecte cette valeur
os.environ.setdefault("APP_ENV", "prod")

logging.basicConfig(level=logging.CRITICAL)

# Import app.py sans déclencher le bloc __main__ (nom ≠ "__main__")
spec = importlib.util.spec_from_file_location("_forge_app_e2e", ROOT / "app.py")
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
