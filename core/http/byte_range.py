"""Parsing d'un en-tête HTTP ``Range`` — `core.http.byte_range`.

Ticket : CORE-HTTP-FILE-RANGE-001.

Volontairement minimal et explicite : une **seule** plage d'octets est
gérée (``bytes=START-END``, ``bytes=START-``, ``bytes=-SUFFIX``). Les
requêtes multi-plages (``bytes=0-1,5-9``) ne sont pas servies en
partiel — on retourne ``None`` et l'appelant sert la ressource complète
(``200``), ce qui reste conforme à la RFC 7233 (le serveur PEUT ignorer
``Range``).

La fonction est **pure** (pas d'I/O) : elle prend la taille du fichier en
argument et reste donc trivialement testable.
"""
from __future__ import annotations

from typing import NamedTuple


class RangeSpec(NamedTuple):
    """Résultat du parsing d'une plage unique.

    - ``satisfiable=True``  → servir ``206`` avec les octets [start, end]
      (bornes **incluses**).
    - ``satisfiable=False`` → plage hors limites → l'appelant répond
      ``416 Range Not Satisfiable`` avec ``Content-Range: bytes */SIZE``.
    """

    satisfiable: bool
    start: int
    end: int  # inclus


def parse_byte_range(range_header: str | None, file_size: int) -> RangeSpec | None:
    """Parse une plage d'octets unique.

    Retourne :
        - ``None`` si pas d'en-tête, en-tête non géré, multi-plages ou
          syntaxe invalide → l'appelant sert la ressource complète (200) ;
        - ``RangeSpec(True, start, end)`` pour une plage satisfaisable ;
        - ``RangeSpec(False, 0, 0)`` pour une plage non satisfaisable (416).
    """
    if not range_header:
        return None

    header = range_header.strip()
    prefix = "bytes="
    if not header.lower().startswith(prefix):
        return None

    spec = header[len(prefix):].strip()
    if "," in spec or "-" not in spec:
        # Multi-plages non gérées / syntaxe sans tiret → on sert tout.
        return None

    start_raw, _, end_raw = spec.partition("-")
    start_raw, end_raw = start_raw.strip(), end_raw.strip()

    try:
        if start_raw == "":
            # Forme suffixe : ``bytes=-N`` → les N derniers octets.
            if end_raw == "":
                return None
            suffix = int(end_raw)
            if suffix <= 0:
                return RangeSpec(False, 0, 0)
            start = max(0, file_size - suffix)
            end = file_size - 1
        else:
            start = int(start_raw)
            end = int(end_raw) if end_raw != "" else file_size - 1
    except ValueError:
        return None

    if file_size == 0 or start < 0 or start > end or start >= file_size:
        return RangeSpec(False, 0, 0)

    end = min(end, file_size - 1)
    return RangeSpec(True, start, end)
