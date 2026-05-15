"""Tests pour forge_cli.output — formatage des tags CLI."""

from forge_cli.output import (
    created,
    dry_run,
    error,
    info,
    ok,
    preserved,
    tag,
    written,
)


def test_tag_contient_label_et_message():
    result = tag("FOO", "bar.sql")
    assert "[FOO]" in result
    assert "bar.sql" in result


def test_written_contient_ecrit_et_chemin():
    result = written("mvc/entities/contact/contact.sql")
    assert "[ÉCRIT]" in result
    assert "mvc/entities/contact/contact.sql" in result


def test_created_contient_cree_et_chemin():
    result = created("mvc/entities/contact/contact.py")
    assert "[CRÉÉ]" in result
    assert "mvc/entities/contact/contact.py" in result


def test_preserved_contient_preserve_et_chemin():
    result = preserved("mvc/entities/contact/contact.py")
    assert "[PRÉSERVÉ]" in result
    assert "mvc/entities/contact/contact.py" in result


def test_preserved_avec_detail_contient_detail():
    result = preserved("contact.py", "fichier manuel, non touché")
    assert "[PRÉSERVÉ]" in result
    assert "contact.py" in result
    assert "fichier manuel, non touché" in result


def test_preserved_sans_detail_pas_de_double_espace_parasite():
    result = preserved("contact.py")
    assert "  " not in result.split("contact.py")[1]


def test_error_contient_erreur_et_message():
    result = error("quelque chose a échoué")
    assert "[ERREUR]" in result
    assert "quelque chose a échoué" in result


def test_ok_contient_ok_et_message():
    result = ok("Modele valide.")
    assert "[OK]" in result
    assert "Modele valide." in result


def test_info_contient_info_et_message():
    result = info("Modifiez le JSON si besoin.")
    assert "[INFO]" in result
    assert "Modifiez le JSON si besoin." in result


def test_dry_run_contient_dry_run_et_message():
    result = dry_run("Aucun fichier modifié.")
    assert "[DRY-RUN]" in result
    assert "Aucun fichier modifié." in result


def test_alignement_written_et_created():
    """written et created produisent des lignes de même longueur avant le chemin."""
    prefix_written = written("x").split("x")[0]
    prefix_created = created("x").split("x")[0]
    assert len(prefix_written) == len(prefix_created)


def test_alignement_written_et_preserved():
    """written et preserved produisent des préfixes de même longueur."""
    prefix_written = written("x").split("x")[0]
    prefix_preserved = preserved("x").split("x")[0]
    assert len(prefix_written) == len(prefix_preserved)
