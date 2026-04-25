from pathlib import Path

import pytest

from forge_cli.sync_landing import (
    GENERATED_COMMENT,
    LandingSyncError,
    expected_docs_content,
    landing_is_synced,
    main,
    sync_landing,
)


def _write_source(root: Path, content: str = "<!DOCTYPE html>\n<html></html>\n") -> Path:
    source = root / "mvc" / "views" / "landing" / "index.html"
    source.parent.mkdir(parents=True)
    source.write_text(content, encoding="utf-8")
    return source


def test_sync_landing_ecrit_docs_index_depuis_landing(tmp_path):
    source = _write_source(tmp_path)
    target = tmp_path / "docs" / "index.html"

    written = sync_landing(source_path=source, target_path=target)

    assert written == target
    assert target.read_text(encoding="utf-8") == expected_docs_content(source)


def test_sync_landing_ajoute_commentaire_fichier_genere(tmp_path):
    source = _write_source(tmp_path)
    target = tmp_path / "docs" / "index.html"

    sync_landing(source_path=source, target_path=target)

    assert target.read_text(encoding="utf-8").startswith(GENERATED_COMMENT)
    assert "FICHIER GENERE" in target.read_text(encoding="utf-8")


def test_sync_landing_check_ok_si_synchronise(tmp_path, monkeypatch, capsys):
    _write_source(tmp_path)
    monkeypatch.chdir(tmp_path)
    sync_landing()

    main(["sync:landing", "--check"])

    captured = capsys.readouterr()
    assert "[OK]" in captured.out
    assert "docs/index.html est synchronisé" in captured.out


def test_sync_landing_check_erreur_si_desynchronise(tmp_path, monkeypatch, capsys):
    _write_source(tmp_path)
    monkeypatch.chdir(tmp_path)
    sync_landing()
    (tmp_path / "docs" / "index.html").write_text("modification manuelle\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["sync:landing", "--check"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "[ERREUR]" in captured.out
    assert "docs/index.html est désynchronisé" in captured.out


def test_sync_landing_source_absente_erreur_propre(tmp_path):
    source = tmp_path / "mvc" / "views" / "landing" / "index.html"
    target = tmp_path / "docs" / "index.html"

    with pytest.raises(LandingSyncError) as exc_info:
        sync_landing(source_path=source, target_path=target)

    assert "Source introuvable" in str(exc_info.value)


def test_sync_landing_main_source_absente_affiche_erreur(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["sync:landing"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "[ERREUR]" in captured.out
    assert "Source introuvable : mvc/views/landing/index.html" in captured.out


def test_sync_landing_ne_modifie_pas_la_source(tmp_path):
    source_content = "<!DOCTYPE html>\n<html><body>canonique</body></html>\n"
    source = _write_source(tmp_path, source_content)
    target = tmp_path / "docs" / "index.html"

    sync_landing(source_path=source, target_path=target)

    assert source.read_text(encoding="utf-8") == source_content


def test_landing_is_synced_detecte_une_divergence(tmp_path):
    source = _write_source(tmp_path)
    target = tmp_path / "docs" / "index.html"
    sync_landing(source_path=source, target_path=target)
    assert landing_is_synced(source_path=source, target_path=target)

    target.write_text(target.read_text(encoding="utf-8") + "\n<!-- manuel -->\n", encoding="utf-8")
    assert not landing_is_synced(source_path=source, target_path=target)
