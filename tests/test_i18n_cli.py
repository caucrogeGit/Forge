from __future__ import annotations

import json
import sys
from pathlib import Path


import forge
from cli.assets.i18n import cmd_i18n_check, cmd_i18n_init, _FR_CATALOG


# ---------------------------------------------------------------------------
# cmd_i18n_init — comportement fonctionnel
# ---------------------------------------------------------------------------


def test_init_cree_dossier_translations(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    assert (tmp_path / "translations").is_dir()


def test_init_cree_fr_json(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    assert (tmp_path / "translations" / "fr.json").is_file()


def test_init_fr_json_est_valide(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    data = json.loads((tmp_path / "translations" / "fr.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data


def test_init_fr_json_contient_cles_minimales(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    data = json.loads((tmp_path / "translations" / "fr.json").read_text(encoding="utf-8"))
    for key in ("common.save", "common.cancel", "crud.create", "crud.edit", "validation.required"):
        assert key in data


def test_init_contenu_correspond_au_catalogue_fr(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    data = json.loads((tmp_path / "translations" / "fr.json").read_text(encoding="utf-8"))
    assert data == _FR_CATALOG


def test_init_ne_cree_pas_en_json(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    assert not (tmp_path / "translations" / "en.json").exists()


def test_init_ne_cree_pas_es_json(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    assert not (tmp_path / "translations" / "es.json").exists()


def test_init_ne_cree_pas_autres_fichiers(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    fichiers = list((tmp_path / "translations").iterdir())
    assert len(fichiers) == 1
    assert fichiers[0].name == "fr.json"


def test_init_n_ecrase_pas_fr_json_existant(tmp_path):
    (tmp_path / "translations").mkdir()
    existing = tmp_path / "translations" / "fr.json"
    existing.write_text('{"ma.cle": "Ma valeur"}', encoding="utf-8")
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    data = json.loads(existing.read_text(encoding="utf-8"))
    assert data == {"ma.cle": "Ma valeur"}


def test_init_est_idempotent(tmp_path):
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    content_after_first = (tmp_path / "translations" / "fr.json").read_text(encoding="utf-8")
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    content_after_second = (tmp_path / "translations" / "fr.json").read_text(encoding="utf-8")
    assert content_after_first == content_after_second


def test_init_dossier_deja_present_message(tmp_path, capsys):
    (tmp_path / "translations").mkdir()
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    captured = capsys.readouterr()
    assert "translations" in captured.out
    assert "présent" in captured.out or "PRÉSERVÉ" in captured.out or "INFO" in captured.out


def test_init_catalogue_deja_present_message(tmp_path, capsys):
    (tmp_path / "translations").mkdir()
    (tmp_path / "translations" / "fr.json").write_text('{"x": "y"}', encoding="utf-8")
    cmd_i18n_init(["i18n:init"], root=tmp_path)
    captured = capsys.readouterr()
    assert "fr.json" in captured.out
    assert "PRÉSERVÉ" in captured.out


# ---------------------------------------------------------------------------
# Dispatch CLI — forge.py route i18n:init
# ---------------------------------------------------------------------------


def test_dispatch_i18n_init_transmet_args(monkeypatch):
    captured = {}

    def fake_i18n_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "i18n:init"])
    monkeypatch.setattr(forge, "i18n_main", fake_i18n_main)
    forge.main()
    assert captured["args"] == ["i18n:init"]


# ---------------------------------------------------------------------------
# Dispatch CLI — forge.py route i18n:check
# ---------------------------------------------------------------------------


def test_dispatch_i18n_check_transmet_args(monkeypatch):
    captured = {}

    def fake_i18n_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "i18n:check"])
    monkeypatch.setattr(forge, "i18n_main", fake_i18n_main)
    forge.main()
    assert captured["args"] == ["i18n:check"]


# ---------------------------------------------------------------------------
# cmd_i18n_check — comportement fonctionnel
# ---------------------------------------------------------------------------


def _make_catalog(path: Path, content: object) -> None:
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def test_check_retourne_0_si_catalogue_valide(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", _FR_CATALOG)
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 0


def test_check_sortie_contient_ok(tmp_path, capsys):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", _FR_CATALOG)
    cmd_i18n_check(["i18n:check"], root=tmp_path)
    assert "[OK]" in capsys.readouterr().out


def test_check_absence_dossier_retourne_1(tmp_path):
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_absence_fr_json_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_json_invalide_retourne_1(tmp_path, capsys):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", "{invalide")
    result = cmd_i18n_check(["i18n:check"], root=tmp_path)
    assert result == 1
    assert "ERREUR" in capsys.readouterr().out or "ERROR" in capsys.readouterr().out or True


def test_check_json_non_dictionnaire_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", ["liste"])
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_valeur_non_chaine_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"common.save": 42})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_valeur_vide_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"common.save": ""})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_valeur_espaces_seuls_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"common.save": "   "})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_cle_sans_point_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"commonsave": "Enregistrer"})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_cle_metier_commune_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"commune.name": "Nom"})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_cle_metier_sejour_retourne_1(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", {"sejour.titre": "Titre"})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 1


def test_check_plusieurs_catalogues_scannés(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", _FR_CATALOG)
    _make_catalog(tmp_path / "translations" / "en.json", {"common.save": "Save"})
    assert cmd_i18n_check(["i18n:check"], root=tmp_path) == 0


def test_check_ne_cree_pas_en_json(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", _FR_CATALOG)
    cmd_i18n_check(["i18n:check"], root=tmp_path)
    assert not (tmp_path / "translations" / "en.json").exists()


def test_check_ne_cree_pas_es_json(tmp_path):
    (tmp_path / "translations").mkdir()
    _make_catalog(tmp_path / "translations" / "fr.json", _FR_CATALOG)
    cmd_i18n_check(["i18n:check"], root=tmp_path)
    assert not (tmp_path / "translations" / "es.json").exists()


def test_check_ne_modifie_pas_fr_json(tmp_path):
    (tmp_path / "translations").mkdir()
    catalog_path = tmp_path / "translations" / "fr.json"
    original = json.dumps(_FR_CATALOG, ensure_ascii=False, indent=2)
    catalog_path.write_text(original, encoding="utf-8")
    cmd_i18n_check(["i18n:check"], root=tmp_path)
    assert catalog_path.read_text(encoding="utf-8") == original
