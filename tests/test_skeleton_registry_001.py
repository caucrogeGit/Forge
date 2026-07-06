"""SKELETON-REGISTRY-001 (ADR-024) — module de matérialisation du squelette.

skeleton expose DATA_DIR, iter_skeleton_files() et materialize().
Ces tests garantissent l'API et une copie fidèle (dotfiles compris, bytecode
exclu) sans modifier la source.
"""
from pathlib import Path

import skeleton as skeleton


def test_data_dir_pointe_sur_data():
    assert skeleton.DATA_DIR.name == "data"
    assert skeleton.DATA_DIR.is_dir()
    assert (skeleton.DATA_DIR / "app.py").is_file()


def test_iter_inclut_fichiers_cles_et_dotfiles():
    rels = {p.relative_to(skeleton.DATA_DIR).as_posix() for p in skeleton.iter_skeleton_files()}
    for expected in [
        "app.py",
        "config.py",
        "requirements.txt",
        "mvc/routes.py",
        "mvc/views/home/index.html",
        ".gitignore",
        "storage/uploads/.gitkeep",
    ]:
        assert expected in rels, f"{expected} absent de iter_skeleton_files()"


def test_iter_exclut_bytecode():
    rels = [p.as_posix() for p in skeleton.iter_skeleton_files()]
    assert not any(r.endswith((".pyc", ".pyo")) for r in rels)
    assert not any("__pycache__" in r for r in rels)


def test_materialize_copie_arbre_complet(tmp_path):
    dest = tmp_path / "proj"
    written = skeleton.materialize(dest)

    # Tous les fichiers source se retrouvent dans dest, à l'identique.
    sources = skeleton.iter_skeleton_files()
    assert len(written) == len(sources)

    for src in sources:
        rel = src.relative_to(skeleton.DATA_DIR)
        copied = dest / rel
        assert copied.is_file(), f"{rel} non copié"
        assert copied.read_bytes() == src.read_bytes(), f"{rel} altéré à la copie"

    # Dotfiles et dossiers vides préservés.
    assert (dest / ".gitignore").is_file()
    assert (dest / "storage" / "uploads" / ".gitkeep").is_file()
    # La source n'est pas modifiée.
    assert (skeleton.DATA_DIR / "app.py").is_file()


def test_materialize_cree_dest_si_absent(tmp_path):
    dest = tmp_path / "nouveau" / "projet"
    assert not dest.exists()
    skeleton.materialize(dest)
    assert (dest / "app.py").is_file()


def test_materialize_retourne_chemins_sous_dest(tmp_path):
    dest = tmp_path / "proj"
    written = skeleton.materialize(dest)
    assert written, "materialize doit retourner des fichiers"
    for p in written:
        assert Path(dest) in p.parents or p.parent == Path(dest)
