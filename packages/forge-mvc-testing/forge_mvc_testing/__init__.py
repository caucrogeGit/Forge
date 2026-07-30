"""forge-mvc-testing — infrastructure de test partagée pour Forge (dev only).

Fournit `FakeRequest` et, via un plugin pytest (point d'entrée `pytest11`,
voir `forge_mvc_testing.plugin`), les fixtures partagées : configuration du
noyau, nettoyage entre tests, et `fake_request`.

Ce paquet n'est JAMAIS une dépendance runtime ; il n'est installé qu'en
développement (ADR-041).
"""
from __future__ import annotations

from forge_mvc_testing.fake_request import FakeRequest

__all__ = ["FakeRequest"]
__version__ = "1.0.0rc3"
