"""Test méta — TEST-UPLOAD-AV-FALSE-POSITIVE-FIX-001.

Garde-fou : aucun fichier ``.py`` de ``tests/`` ne doit contenir en clair une
signature d'exécutable Windows ("MZ" + 0x90) ni une balise d'ouverture PHP.
Ces littéraux déclenchent des faux positifs antivirus (Windows Defender,
ThreatID 2147891542) sur l'archive du dépôt. Les payloads factices doivent
être construits dynamiquement — voir ``tests/_malicious_samples.py``.

Les motifs interdits sont eux-mêmes assemblés à la volée pour que ce fichier de
test ne se signale pas lui-même.
"""
from __future__ import annotations

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent

# Motifs reconstruits à la volée — ne pas écrire la signature en clair ici non
# plus, sinon ce fichier déclencherait son propre garde-fou et l'antivirus.
_PE_SIGNATURE = "MZ" + "\\x90"   # tel qu'il apparaîtrait dans un littéral b"..."
_PHP_OPEN = "<?" + "php"


@pytest.mark.parametrize("forbidden", [_PE_SIGNATURE, _PHP_OPEN])
def test_aucune_signature_av_litterale_dans_les_tests(forbidden):
    coupables = []
    for py in TESTS_DIR.rglob("*.py"):
        if forbidden in py.read_text(encoding="utf-8"):
            coupables.append(py.name)
    assert not coupables, (
        f"Signature antivirus littérale {forbidden!r} trouvée dans : {coupables}. "
        "Construire le payload dynamiquement via tests/_malicious_samples.py."
    )
