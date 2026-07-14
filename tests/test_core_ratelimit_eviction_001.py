"""Tests — CORE-RATELIMIT-EVICTION-001 : éviction du store anti-bruteforce.

Le store in-memory de core/auth/rate_limit.py accumulait chaque tentative pour
toute la vie du processus (croissance mémoire non bornée, coût O(n) croissant).
Garde-fous :
  1. les tentatives sorties de la rétention sont élaguées à l'écriture ;
  2. la taille d'un bucket est plafonnée à MAX_ATTEMPTS_PER_KEY ;
  3. le balayage global amorti évince les clés abandonnées (IP variées) ;
  4. is_locked_out refuse une fenêtre plus longue que la rétention
     (comptage silencieusement faux sinon — règle B) ;
  5. non-régression : le verrouillage nominal continue de fonctionner.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import core.auth.rate_limit as rl
from core.auth.exceptions import InvalidAuthRateLimitRuleError
from core.auth.rate_limit import (
    ATTEMPTS_RETENTION_SECONDS,
    MAX_ATTEMPTS_PER_KEY,
    is_locked_out,
    purge_all_attempts,
    record_attempt,
)


@pytest.fixture(autouse=True)
def _clean_store():
    purge_all_attempts()
    yield
    purge_all_attempts()


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class TestPruneAtWrite:
    def test_tentative_hors_retention_est_elagee(self):
        now = _now()
        old = now - timedelta(seconds=ATTEMPTS_RETENTION_SECONDS + 10)
        record_attempt("login", "1.2.3.4", now=old)
        record_attempt("login", "1.2.3.4", now=now)
        assert len(rl._attempts_store["login:1.2.3.4"]) == 1

    def test_tentative_dans_la_retention_est_conservee(self):
        now = _now()
        recent = now - timedelta(seconds=30)
        record_attempt("login", "1.2.3.4", now=recent)
        record_attempt("login", "1.2.3.4", now=now)
        assert len(rl._attempts_store["login:1.2.3.4"]) == 2

    def test_bucket_plafonne(self):
        now = _now()
        for i in range(MAX_ATTEMPTS_PER_KEY + 50):
            record_attempt("login", "1.2.3.4", now=now + timedelta(seconds=i))
        assert len(rl._attempts_store["login:1.2.3.4"]) == MAX_ATTEMPTS_PER_KEY


class TestGlobalSweep:
    def test_cles_abandonnees_evincees_par_le_balayage(self):
        base = _now() - timedelta(seconds=ATTEMPTS_RETENTION_SECONDS + 60)
        # 300 IPs distinctes attaquent, puis disparaissent.
        for i in range(300):
            record_attempt("login", f"10.0.0.{i}", now=base)
        # Le balayage se déclenche pendant les écritures suivantes (>= _SWEEP_EVERY).
        now = _now()
        for i in range(rl._SWEEP_EVERY):
            record_attempt("login", "9.9.9.9", now=now)
        keys = set(rl._attempts_store)
        assert "login:9.9.9.9" in keys
        assert not any(k.startswith("login:10.0.0.") for k in keys), (
            "les clés hors rétention doivent être évincées par le balayage"
        )


class TestWindowContract:
    def test_fenetre_plus_longue_que_la_retention_refusee(self):
        with pytest.raises(InvalidAuthRateLimitRuleError):
            is_locked_out("login", "1.2.3.4", 5, ATTEMPTS_RETENTION_SECONDS + 1)

    def test_fenetre_egale_a_la_retention_acceptee(self):
        assert is_locked_out("login", "1.2.3.4", 5, ATTEMPTS_RETENTION_SECONDS) is False


class TestNominalUnchanged:
    def test_verrouillage_nominal(self):
        now = _now()
        for _ in range(5):
            record_attempt("login", "1.2.3.4", now=now)
        assert is_locked_out("login", "1.2.3.4", 5, 60, now=now) is True
        assert is_locked_out("login", "5.6.7.8", 5, 60, now=now) is False

    def test_clear_attempts_libere(self):
        now = _now()
        for _ in range(5):
            record_attempt("login", "1.2.3.4", now=now)
        rl.clear_attempts("login", "1.2.3.4")
        assert is_locked_out("login", "1.2.3.4", 5, 60, now=now) is False
