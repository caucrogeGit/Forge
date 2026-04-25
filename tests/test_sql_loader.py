"""
Tests de core/database/sql_loader.py — cache thread-safe et invalidation.
"""
import os

import pytest
import core.forge as forge
from core.database import sql_loader


@pytest.fixture(autouse=True)
def reset_sql_cache():
    sql_loader._vider_cache()
    yield
    sql_loader._vider_cache()


def _setup_sql_dir(tmp_path, monkeypatch, content="REQUETE = 'SELECT 1'\n"):
    env_dir = tmp_path / "dev"
    env_dir.mkdir()
    f = env_dir / "test_queries.py"
    f.write_text(content, encoding="utf-8")
    monkeypatch.setitem(forge._cfg, "sql_dir", str(tmp_path))
    monkeypatch.setitem(forge._cfg, "app_env", "dev")
    return f


class TestSqlLoaderCache:
    def test_chargement_module_valide(self, tmp_path, monkeypatch):
        _setup_sql_dir(tmp_path, monkeypatch, "REQUETE = 'SELECT 1'\n")
        m = sql_loader.charger_queries("test_queries.py")
        assert m.REQUETE == "SELECT 1"

    def test_cache_hit_retourne_meme_objet(self, tmp_path, monkeypatch):
        _setup_sql_dir(tmp_path, monkeypatch)
        m1 = sql_loader.charger_queries("test_queries.py")
        m2 = sql_loader.charger_queries("test_queries.py")
        assert m1 is m2

    def test_cache_invalide_si_contenu_change(self, tmp_path, monkeypatch):
        f = _setup_sql_dir(tmp_path, monkeypatch, "VERSION = 1\n")
        m1 = sql_loader.charger_queries("test_queries.py")
        assert m1.VERSION == 1

        # Taille différente → stat.st_size change → invalidation garantie sans sleep
        f.write_text("VERSION = 2\nEXTRA = 'x'\n", encoding="utf-8")

        m2 = sql_loader.charger_queries("test_queries.py")
        assert m2.VERSION == 2
        assert m1 is not m2

    def test_cache_invalide_si_meme_taille_mais_mtime_change(self, tmp_path, monkeypatch):
        """Deux fichiers de même taille mais mtime différent sont rechargés."""
        f = _setup_sql_dir(tmp_path, monkeypatch, "V = 1\n")
        m1 = sql_loader.charger_queries("test_queries.py")

        f.write_text("V = 9\n", encoding="utf-8")  # même taille (6 octets)
        # Avance explicitement le mtime d'1 seconde — évite les races sub-ms sur tmpfs
        stat = f.stat()
        os.utime(f, (stat.st_atime + 1.0, stat.st_mtime + 1.0))

        m2 = sql_loader.charger_queries("test_queries.py")
        assert m2.V == 9
        assert m1 is not m2

    def test_fichier_absent_leve_file_not_found(self, tmp_path, monkeypatch):
        (tmp_path / "dev").mkdir()
        monkeypatch.setitem(forge._cfg, "sql_dir", str(tmp_path))
        monkeypatch.setitem(forge._cfg, "app_env", "dev")
        with pytest.raises(FileNotFoundError, match="introuvable"):
            sql_loader.charger_queries("inexistant_queries.py")

    def test_vider_cache_libere_entrees(self, tmp_path, monkeypatch):
        _setup_sql_dir(tmp_path, monkeypatch)
        sql_loader.charger_queries("test_queries.py")
        assert len(sql_loader._cache) == 1
        sql_loader._vider_cache()
        assert len(sql_loader._cache) == 0
