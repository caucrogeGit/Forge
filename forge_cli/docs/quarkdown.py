"""forge docs:pdf — génération PDF de la documentation via Quarkdown (optionnel).

Quarkdown est une dépendance externe facultative. Le cœur Forge ne l'importe pas.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import forge_cli.output as out


_INSTALL_HINT = """
  Quarkdown n'est pas installé ou n'est pas dans le PATH.

  Installation (Linux / macOS) :
    curl -fsSL https://raw.githubusercontent.com/quarkdown-labs/get-quarkdown/refs/heads/main/install.sh \\
      | sudo env "PATH=$PATH" bash

  Homebrew :
    brew install quarkdown

  Quarkdown requiert Java 17+.

  La génération PDF est une fonctionnalité optionnelle.
  Le cœur de Forge n'en dépend pas.
"""

_QD_SOURCE = Path("docs") / "quarkdown" / "forge-documentation.qd"
_PDF_TARGET = Path("build") / "docs" / "forge-documentation.pdf"


def _find_quarkdown() -> str | None:
    return shutil.which("quarkdown")


def _find_repo_root() -> Path | None:
    """Remonte l'arborescence pour trouver la racine du dépôt Forge."""
    for candidate in [Path.cwd()] + list(Path.cwd().parents):
        if (candidate / "forge.py").exists() and (candidate / "docs").is_dir():
            return candidate
    return None


def _locate_generated_pdf(qd_file: Path) -> Path | None:
    """Cherche le PDF généré par Quarkdown à côté du fichier source."""
    stem = qd_file.stem
    candidates = [
        qd_file.parent / f"{stem}.pdf",
        qd_file.parent / stem / f"{stem}.pdf",
        qd_file.parent / "out" / f"{stem}.pdf",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def cmd_docs_pdf(args: list[str]) -> None:
    print("\nforge docs:pdf\n")

    qk = _find_quarkdown()
    if not qk:
        print(out.error("Quarkdown introuvable sur le PATH."))
        print(_INSTALL_HINT)
        raise SystemExit(1)

    print(out.ok(f"Quarkdown : {qk}"))

    root = _find_repo_root()
    if root is None:
        print(out.error("Racine du dépôt Forge introuvable depuis le répertoire courant."))
        print(out.info("Lancer forge docs:pdf depuis la racine du dépôt Forge."))
        raise SystemExit(1)

    qd_file = root / _QD_SOURCE
    if not qd_file.exists():
        print(out.error(f"Fichier source introuvable : {_QD_SOURCE}"))
        print(out.info("Créer docs/quarkdown/forge-documentation.qd avant de générer le PDF."))
        print(out.info("Voir : docs/pdf.md pour la structure attendue."))
        raise SystemExit(1)

    target = root / _PDF_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)

    print(out.info(f"Source : {_QD_SOURCE}"))
    print(out.info(f"Cible  : {_PDF_TARGET}"))
    print()

    result = subprocess.run(
        [qk, "c", str(qd_file), "--pdf"],
        cwd=root,
    )

    if result.returncode != 0:
        print()
        print(out.error("Quarkdown a signalé une erreur (voir la sortie ci-dessus)."))
        raise SystemExit(result.returncode)

    generated = _locate_generated_pdf(qd_file)
    if generated and generated.resolve() != target.resolve():
        shutil.move(str(generated), str(target))

    if target.exists():
        print()
        print(out.ok(f"PDF prêt : {_PDF_TARGET}"))
    else:
        print()
        print(out.warn("PDF non trouvé à l'emplacement attendu."))
        print(out.info("Quarkdown a peut-être placé le fichier ailleurs — consulter la sortie ci-dessus."))


# ── Dispatch ──────────────────────────────────────────────────────────────────

def main(args: list[str]) -> None:
    if not args:
        print("Usage : forge docs:pdf")
        raise SystemExit(1)
    command = args[0]
    if command == "docs:pdf":
        cmd_docs_pdf(args[1:])
    else:
        print(f"Commande inconnue : {command!r}")
        raise SystemExit(1)
