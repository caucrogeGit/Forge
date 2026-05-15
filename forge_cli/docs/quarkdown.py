"""forge docs:pdf — génération PDF de la documentation via Quarkdown (optionnel).

Quarkdown est une dépendance externe. Ce module ne l'importe jamais :
il l'appelle via subprocess si le binaire est présent sur le PATH.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


_QD_SOURCE = Path("docs") / "quarkdown" / "forge-documentation.qd"
_PDF_TARGET = Path("build") / "docs" / "forge-documentation.pdf"

_QUARKDOWN_ABSENT = """
[ERREUR] Quarkdown n'est pas installé ou n'est pas dans le PATH.

  Installation (Linux / macOS) :
    curl -fsSL https://raw.githubusercontent.com/quarkdown-labs/get-quarkdown/refs/heads/main/install.sh \\
      | sudo env "PATH=$PATH" bash

  Homebrew :
    brew install quarkdown

  Quarkdown requiert Java 17+.
  La génération PDF est optionnelle — le cœur de Forge n'en dépend pas.
"""


def _log(message: str) -> None:
    print(f"[Forge] {message}")


def _find_quarkdown() -> str | None:
    return shutil.which("quarkdown")


def _find_repo_root() -> Path | None:
    """Remonte l'arborescence pour trouver la racine du dépôt Forge."""
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "forge.py").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return None


def _find_generated_pdf(qd_file: Path) -> Path | None:
    """Cherche le PDF créé par Quarkdown à côté du fichier source."""
    stem = qd_file.stem
    for candidate in (
        qd_file.parent / f"{stem}.pdf",
        qd_file.parent / stem / f"{stem}.pdf",
        qd_file.parent / "out" / f"{stem}.pdf",
    ):
        if candidate.exists():
            return candidate
    return None


def build_pdf() -> None:
    """Génère le PDF de la documentation Forge via Quarkdown."""

    qk = _find_quarkdown()
    if not qk:
        sys.exit(_QUARKDOWN_ABSENT)

    root = _find_repo_root()
    if root is None:
        sys.exit("[ERREUR] Racine du projet Forge introuvable. Lancer depuis le dépôt Forge.")

    qd_file = root / _QD_SOURCE
    if not qd_file.exists():
        sys.exit(
            f"[ERREUR] Fichier source introuvable : {_QD_SOURCE}\n"
            "  Créer docs/quarkdown/forge-documentation.qd avant de générer le PDF.\n"
            "  Voir : docs/pdf.md"
        )

    target = root / _PDF_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)

    cmd = [qk, "c", str(qd_file), "--pdf"]
    _log("Génération PDF en cours...")
    _log(f"→ {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=root)

    if result.returncode != 0:
        sys.exit(f"[ERREUR] Quarkdown a échoué (code {result.returncode}).")

    generated = _find_generated_pdf(qd_file)
    if generated and generated.resolve() != target.resolve():
        try:
            shutil.move(str(generated), str(target))
        except OSError as exc:
            sys.exit(f"[ERREUR] Impossible de déplacer le PDF : {exc}")

    if not target.exists():
        sys.exit(
            "[ERREUR] PDF non trouvé après génération.\n"
            "  Quarkdown a peut-être placé le fichier à un emplacement inattendu.\n"
            f"  Chercher manuellement dans : {qd_file.parent}"
        )

    _log(f"PDF généré : {_PDF_TARGET}")
