"""Garde-fou DOCS-IMPORTS-VALIDITY-SWEEP-001.

Verrouille la validité des imports Python apparaissant dans les exemples
de code de la documentation Forge active.

Stratégie d'audit
-----------------
Le test parse chaque fichier Markdown actif, extrait les blocs ```python``
(et ```py``), puis utilise ``ast`` pour identifier les imports — ce qui
évite les faux positifs sur :

  * chaînes Python contenant ``"from ... import ..."`` (literal de fichier
    à écrire, par ex. dans un starter guide) ;
  * commentaires inline ;
  * ellipses ``...`` utilisées comme placeholder ``etc.``.

Classification
--------------
Trois familles de modules sont distinguées :

  * **Framework** — ``core.*``, ``forge_mvc_*``, ``forge_cli.*``. Tout
    import est résolu via ``importlib`` ; chaque symbole importé doit
    exister sur le module. Une faute ici échoue le test.

  * **User-project** — ``mvc.*`` (controllers, routes, db…). Forge génère
    ces fichiers dans le projet de l'utilisateur (``forge make:crud``,
    ``forge make:entity``…) ; ils n'existent pas dans le repo Forge.
    Accepté sans validation — leur absence côté Forge est attendue.

  * **Fictif annoté** — modules autres (`from mon_module import ...`),
    légitimes uniquement s'ils sont accompagnés d'un marqueur
    ``# exemple fictif``, ``# à adapter``, ``# Adapter à votre …``
    dans les 2 lignes précédentes. Sinon le test signale.

Les fichiers historiques (``docs/history/``, ``docs/adr/``,
``docs/roadmap/``) sont exclus — leur contenu décrit l'état du dépôt
à un moment passé.
"""
from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_REPO_ROOT = Path(__file__).resolve().parents[2]

# Pour pouvoir résoudre les opt-ins installés en mode source via packages/,
# on mime ce que fait le conftest racine. Sans cela, `forge_mvc_rbac` etc.
# apparaissent comme manquants.
for _pkg in sorted((_REPO_ROOT / "packages").iterdir()):
    if _pkg.is_dir() and str(_pkg) not in sys.path:
        sys.path.insert(0, str(_pkg))


# ---------------------------------------------------------------------------
# Sélection des fichiers
# ---------------------------------------------------------------------------


_EXCLUDED_DIR_PARTS = frozenset({
    "history", "adr", "__pycache__", ".pytest_cache",
})

_USER_PROJECT_ROOTS = frozenset({
    "mvc", "app", "config", "wsgi",
    # `modules/` est aussi côté projet utilisateur (système de modules Forge :
    # voir `docs/philosophy/module-author-guide.md`). Les modules concrets vivent dans
    # le projet, pas dans le repo Forge.
    "modules",
    # `optins/` est la couche de branchement local des opt-ins, générée
    # dans le projet utilisateur (voir docs/architecture/optins-project-structure.md).
    # Le code `optins.*` n'existe pas dans le repo Forge — c'est de
    # l'illustration projet, comme `mvc.*`.
    "optins",
})
_FRAMEWORK_ROOTS = frozenset({
    "core",
    "forge_mvc_mfa", "forge_mvc_rbac", "forge_mvc_workflow",
    "forge_mvc_stats", "forge_mvc_media",
    # forge-mvc-images : opt-in propriétaire du traitement d'image (ADR-018).
    "forge_mvc_images",
    # forge-mvc-iot / forge-mvc-video : paquets opt-in framework au même titre
    # que leurs frères ci-dessus.
    "forge_mvc_iot", "forge_mvc_video",
    "forge_cli",
    # `integrations/` est dans le repo Forge (Jinja2 renderer, etc.).
    "integrations",
    # `tests.fake_request` et autres helpers de test sont publiés comme
    # exemples utilisables — on les valide aussi.
    "tests",
})

# Marqueurs reconnus comme « exemple fictif explicite » dans les 2 lignes
# précédant un import non-Forge.
_FICTIF_MARKERS = (
    "exemple fictif",
    "à adapter",
    "a adapter",
    "adapter à votre",
    "adapter a votre",
    "votre projet",
    "votre module",
    "votre application",
    "mon_application",
    "votre_module",
    "my_project",
    "code d'illustration",
    "pseudo-code",
)


def _iter_active_md_files() -> list[Path]:
    roots = (
        [_REPO_ROOT / "README.md"]
        + list((_REPO_ROOT / "docs").rglob("*.md"))
        + list((_REPO_ROOT / "packages").rglob("README.md"))
    )
    return [
        p for p in roots
        if p.is_file() and not any(d in p.parts for d in _EXCLUDED_DIR_PARTS)
    ]


# ---------------------------------------------------------------------------
# Extraction des blocs Python depuis le Markdown
# ---------------------------------------------------------------------------


_FENCE_OPEN = re.compile(r"^\s*```(?:python|py)\s*$", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"^\s*```\s*$")


def _python_blocks(text: str) -> list[tuple[int, str]]:
    """Retourne la liste des blocs Python du fichier.

    Chaque entrée est ``(numéro_de_ligne_du_fence_ouvrant, source)``.
    Le source est concaténé pour pouvoir être parsé par ``ast``.
    """
    blocks: list[tuple[int, str]] = []
    current: list[str] | None = None
    start_lineno = 0
    for idx, line in enumerate(text.splitlines(), start=1):
        if current is None:
            if _FENCE_OPEN.match(line):
                current = []
                start_lineno = idx
            continue
        if _FENCE_CLOSE.match(line):
            blocks.append((start_lineno, "\n".join(current)))
            current = None
            continue
        current.append(line)
    return blocks


# ---------------------------------------------------------------------------
# Helpers de validation
# ---------------------------------------------------------------------------


def _root_of(module: str) -> str:
    return module.split(".", 1)[0]


def _is_framework(module: str) -> bool:
    return _root_of(module) in _FRAMEWORK_ROOTS


def _is_user_project(module: str) -> bool:
    return _root_of(module) in _USER_PROJECT_ROOTS


def _has_fictif_marker_nearby(file_text: str, block_start_line: int,
                              block_offset: int) -> bool:
    """True si un marqueur « fictif » apparaît dans les 2 lignes au-dessus
    de la position de l'import dans le fichier d'origine."""
    target_line = block_start_line + block_offset
    lines = file_text.splitlines()
    # Inspecte la ligne du block + 2 lignes au-dessus.
    for ln in range(max(0, target_line - 3), min(len(lines), target_line + 1)):
        line_lower = lines[ln].lower()
        if any(marker in line_lower for marker in _FICTIF_MARKERS):
            return True
    return False


# ---------------------------------------------------------------------------
# Collecte des imports
# ---------------------------------------------------------------------------


def _collect_imports(file_path: Path) -> list[dict]:
    """Pour ``file_path``, retourne la liste des imports détectés.

    Chaque entrée :
        {
            "path": Path,
            "block_line": int,        # ligne du fence ouvrant
            "node_offset": int,       # offset ligne dans le block
            "module": str,            # nom de module canonique
            "names": list[str],       # symboles importés (vide pour `import X`)
            "raw": str,               # texte brut de l'import
        }
    """
    text = file_path.read_text(encoding="utf-8")
    out = []
    for block_line, source in _python_blocks(text):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # On accepte les blocs avec sucre pédagogique non-Python
            # (placeholders ``...``, lignes commentaires libres). Si le
            # block ne parse pas, on tente quand même via regex sur les
            # lignes d'import strictes pour ne pas rater une régression.
            for off, line in enumerate(source.splitlines()):
                m = re.match(r"^\s*(from\s+([\w\.]+)\s+import\s+(.+))$", line)
                if m:
                    names = [
                        n.strip().split(" as ")[0].split("#")[0].strip()
                        for n in m.group(3).split(",")
                    ]
                    out.append({
                        "path": file_path,
                        "block_line": block_line,
                        "node_offset": off,
                        "module": m.group(2),
                        "names": [n for n in names if n and n != "..."],
                        "raw": line.strip(),
                    })
                m2 = re.match(r"^\s*import\s+([\w\.]+)\s*$", line)
                if m2:
                    out.append({
                        "path": file_path,
                        "block_line": block_line,
                        "node_offset": off,
                        "module": m2.group(1),
                        "names": [],
                        "raw": line.strip(),
                    })
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # On ignore les imports relatifs (`from .x import Y`) — ils
                # référencent du code généré dans le même package
                # (ex. `from .contact_base import ContactBase` dans le
                # `__init__.py` d'une entité utilisateur). Le test de
                # cohérence framework ne s'y applique pas.
                if node.level and node.level > 0:
                    continue
                out.append({
                    "path": file_path,
                    "block_line": block_line,
                    "node_offset": (node.lineno or 1) - 1,
                    "module": node.module,
                    "names": [a.name for a in node.names if a.name != "*"],
                    "raw": f"from {node.module} import "
                           + ", ".join(a.name for a in node.names),
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    out.append({
                        "path": file_path,
                        "block_line": block_line,
                        "node_offset": (node.lineno or 1) - 1,
                        "module": alias.name,
                        "names": [],
                        "raw": f"import {alias.name}",
                    })
    return out


_ALL_IMPORTS: list[dict] = []
for _f in _iter_active_md_files():
    _ALL_IMPORTS.extend(_collect_imports(_f))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAuditCoverage:
    """Le scan doit couvrir une masse significative de documentation."""

    def test_active_md_files_collected(self):
        files = _iter_active_md_files()
        assert len(files) >= 50, (
            f"Trop peu de fichiers Markdown auditables ({len(files)}) — "
            "le test n'inspecte probablement pas la bonne arborescence."
        )

    def test_some_framework_imports_found(self):
        framework = [i for i in _ALL_IMPORTS if _is_framework(i["module"])]
        assert len(framework) >= 50, (
            f"Trop peu d'imports framework détectés ({len(framework)}) — "
            "régression probable du parser de blocs Python."
        )


class TestFrameworkImportsResolve:
    """Tout import des modules framework doit pouvoir être résolu."""

    @pytest.mark.parametrize(
        "imp",
        [i for i in _ALL_IMPORTS if _is_framework(i["module"])],
        ids=lambda i: f"{i['path'].name}:{i['module']}",
    )
    def test_module_is_importable(self, imp):
        try:
            importlib.import_module(imp["module"])
        except ImportError as exc:
            rel = imp["path"].relative_to(_REPO_ROOT)
            pytest.fail(
                f"{rel} bloc ligne {imp['block_line']}+{imp['node_offset']}: "
                f"import framework invalide `{imp['raw']}` — {exc}"
            )


class TestFrameworkImportedSymbolsExist:
    """Chaque symbole importé d'un module framework doit exister sur le module."""

    @pytest.mark.parametrize(
        "imp",
        [
            i for i in _ALL_IMPORTS
            if _is_framework(i["module"]) and i["names"]
        ],
        ids=lambda i: f"{i['path'].name}:{i['module']}:{','.join(i['names'])[:60]}",
    )
    def test_symbols_present(self, imp):
        try:
            mod = importlib.import_module(imp["module"])
        except ImportError:
            pytest.skip(f"Module {imp['module']} non importable — couvert ailleurs.")
        rel = imp["path"].relative_to(_REPO_ROOT)
        missing = [n for n in imp["names"] if not hasattr(mod, n)]
        assert not missing, (
            f"{rel} bloc ligne {imp['block_line']}+{imp['node_offset']}: "
            f"`{imp['module']}` ne contient pas {missing}. "
            f"Import complet : `{imp['raw']}`"
        )


class TestNonFrameworkImportsAreAnnotatedOrUserProject:
    """Les imports hors framework doivent être :
      * soit `mvc.*` (code de projet utilisateur — Forge génère ces fichiers) ;
      * soit annotés par un marqueur fictif dans les 2 lignes précédentes.
    """

    @pytest.mark.parametrize(
        "imp",
        [
            i for i in _ALL_IMPORTS
            if not _is_framework(i["module"])
            and not _is_user_project(i["module"])
        ],
        ids=lambda i: f"{i['path'].name}:{i['module']}",
    )
    def test_annotated_or_known_pattern(self, imp):
        # Les modules stdlib / tiers ne nous concernent pas — on filtre.
        root = _root_of(imp["module"])
        if root in {
            "os", "sys", "json", "re", "time", "datetime", "pathlib",
            "logging", "typing", "subprocess", "io", "ast",
            "secrets", "hashlib", "hmac", "functools", "itertools",
            "collections", "dataclasses", "enum", "tempfile", "shutil",
            "warnings", "unittest", "contextlib", "abc",
            "pytest", "cryptography", "pyotp", "PIL", "jinja2",
            "mariadb", "argon2", "jsonschema", "dotenv",
            "importlib", "fastapi", "flask",  # non-Forge fréquents
        }:
            return
        # Sinon : doit être annoté.
        file_text = imp["path"].read_text(encoding="utf-8")
        annotated = _has_fictif_marker_nearby(
            file_text, imp["block_line"], imp["node_offset"]
        )
        rel = imp["path"].relative_to(_REPO_ROOT)
        assert annotated, (
            f"{rel} bloc ligne {imp['block_line']}+{imp['node_offset']}: "
            f"`{imp['raw']}` importe `{imp['module']}` qui n'est ni un "
            "module framework ni un chemin `mvc.*` du projet utilisateur. "
            "Ajouter un commentaire « # exemple fictif » ou "
            "« # à adapter à votre projet » à proximité, ou corriger l'import."
        )
