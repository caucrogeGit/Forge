import pytest
from core.security.hashing import (
    hacher_mot_de_passe, verifier_mot_de_passe,
    enregistrer_tentative, est_limite,
    MAX_TENTATIVES,
)

IP = "192.168.1.100"


class TestHachage:
    def test_format_sel_deux_points_hash(self):
        h = hacher_mot_de_passe("monmdp")
        sel, hash_ = h.split(":", 1)
        assert len(sel)   == 32  # 16 octets en hex
        assert len(hash_) == 64  # SHA-256 en hex

    def test_verification_mot_de_passe_correct(self):
        h = hacher_mot_de_passe("monmdp")
        assert verifier_mot_de_passe("monmdp", h) is True

    def test_verification_mot_de_passe_incorrect(self):
        h = hacher_mot_de_passe("monmdp")
        assert verifier_mot_de_passe("mauvais", h) is False

    def test_format_invalide_retourne_false(self):
        assert verifier_mot_de_passe("monmdp", "pas_de_double_point") is False

    def test_hash_vide_retourne_false(self):
        assert verifier_mot_de_passe("monmdp", "") is False

    def test_deux_hashes_du_meme_mdp_sont_differents(self):
        h1 = hacher_mot_de_passe("monmdp")
        h2 = hacher_mot_de_passe("monmdp")
        assert h1 != h2  # sels aléatoires différents


class TestRateLimiting:
    def test_pas_limite_initialement(self):
        assert est_limite(IP) is False

    def test_sous_la_limite(self):
        for _ in range(MAX_TENTATIVES - 1):
            enregistrer_tentative(IP)
        assert est_limite(IP) is False

    def test_limite_atteinte(self):
        for _ in range(MAX_TENTATIVES):
            enregistrer_tentative(IP)
        assert est_limite(IP) is True

    def test_ips_independantes(self):
        for _ in range(MAX_TENTATIVES):
            enregistrer_tentative(IP)
        assert est_limite("10.0.0.1") is False
