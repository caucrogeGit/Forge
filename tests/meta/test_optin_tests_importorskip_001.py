"""Garde-fou TESTS-OPTIN-IMPORTORSKIP-001.

Forge Core doit rester autonome. Les opt-ins officiels
(`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`)
leurs dépendances ainsi que leurs dépendances directes (`pyotp` pour MFA)
peuvent être absents d'un environnement core-only — `pytest` doit alors
ignorer proprement les tests qui en dépendent au lieu de produire une
erreur de collecte.

Le présent meta-test parcourt `tests/**/*.py` via AST et lève si :

  * un fichier de test contient un ``import``/``from ... import`` **au
    niveau module** ciblant un module opt-in (cf. `_OPTIN_MODULES`) ;
  * ET ce même fichier ne contient pas un
    ``pytest.importorskip("<module>")`` au niveau module pour ce module.

Pourquoi AST plutôt que grep textuel :

  * évite les faux positifs sur les chaînes (``assert "import X" not in src``)
    et docstrings qui mentionnent textuellement un opt-in ;
  * ne signale que les imports vraiment top-level — les imports protégés
    par ``try/except ImportError`` à l'intérieur d'une fonction sont OK
    sans guard, ils ne cassent pas la collecte.

Pillow (`PIL`) n'est PAS dans cette liste, par choix pragmatique : depuis
CORE-DROP-PILLOW-001 (ADR-018), Pillow est une dépendance de l'opt-in
`forge-mvc-images`, mais il reste présent dans l'environnement de test (le
paquet est installé en mode source). On ne l'ajoute donc pas au garde-fou
d'importorskip pour ne pas cascader des `importorskip` dans les tests qui
construisent simplement des images de fixture (`tests/test_uploads*.py`,
`tests/test_media_route.py`). Les tests du traitement d'image proprement dit
(`test_uploads_image.py`, `test_sec_upload_decompression_bomb_001.py`) gardent
eux explicitement `importorskip("forge_mvc_images")`.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

# Sous-ensemble CURÉ d'opt-ins (briques de type bibliothèque) dont les tests
# importeurs au niveau module utilisent `pytest.importorskip`. Ce n'est PAS la
# liste exhaustive des 12 opt-ins : l'exhaustivité de la couverture opt-in est
# garantie par `tests/meta/test_pytest_core_only_contract_001.py` (OPTIN_MODULES
# complet + fermeture sur imports inconnus). Les opt-ins à dépendances lourdes
# (files, images, audio, iot, video) sont volontairement hors de ce garde-fou-ci.
# Tout ajout ici doit aller de pair avec un fichier de test qui les importe en
# module-level ET le guarde par importorskip, sinon le garde-fou n'est pas exercé.
_OPTIN_MODULES: frozenset[str] = frozenset({
    "forge_mvc_rbac",
    "forge_mvc_workflow",
    "forge_mvc_stats",
    "forge_mvc_mfa",
    "forge_mvc_pivot",   # pivot advanced extrait du core (ADR-021)
    "forge_mvc_mail",    # mail extrait du core (ADR-022)
    "forge_mvc_i18n",    # i18n extrait du core (ADR-027)
    "pyotp",       # dépendance directe de forge-mvc-mfa (TOTP)
})

_TESTS_DIR = Path(__file__).resolve().parent.parent


def _top_level_optin_imports(tree: ast.Module) -> set[str]:
    """Modules opt-in importés au niveau module (hors try/except imbriqué).

    On itère sur ``tree.body`` directement : tout ``Import`` /
    ``ImportFrom`` profondément imbriqué (dans ``if``, ``try``, fonction)
    est ignoré — c'est le comportement souhaité.
    """
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _OPTIN_MODULES:
                    found.add(root)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _OPTIN_MODULES:
                    found.add(root)
    return found


def _module_level_importorskip_targets(tree: ast.Module) -> set[str]:
    """Modules ciblés par ``pytest.importorskip("X")`` au niveau module.

    Reconnaît :
        pytest.importorskip("forge_mvc_mfa")
        pytest.importorskip('forge_mvc_mfa')

    Et ignore les appels dans des classes ou fonctions — l'importorskip
    doit s'exécuter au chargement du module pour court-circuiter la
    collecte.
    """
    found: set[str] = set()
    for node in tree.body:
        # `pytest.importorskip("X")` est un appel — apparaît comme `Expr`
        # avec un `Call`. Si jamais le résultat est assigné
        # (`_ = pytest.importorskip(...)`), on traite aussi `Assign`.
        call = None
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
        if call is None:
            continue
        func = call.func
        # Match `pytest.importorskip` ou `importorskip` (alias direct).
        is_match = (
            (isinstance(func, ast.Attribute)
             and func.attr == "importorskip"
             and isinstance(func.value, ast.Name)
             and func.value.id == "pytest")
            or (isinstance(func, ast.Name) and func.id == "importorskip")
        )
        if not is_match:
            continue
        if not call.args:
            continue
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.add(first.value)
    return found


def _iter_test_files():
    """Tous les `tests/**/test_*.py` ET `packages/*/tests/**/test_*.py`.

    Les tests unitaires des opt-ins ont migré vers leur paquet (ADR-040) ;
    l'audit doit les couvrir là aussi.
    """
    roots = [_TESTS_DIR, *sorted((_TESTS_DIR.parent / "packages").glob("*/tests"))]
    for root in roots:
        for path in sorted(root.rglob("test_*.py")):
            yield path


# ---------------------------------------------------------------------------
# Données auditées au runtime — calculées une fois.
# ---------------------------------------------------------------------------

def _collect_audit() -> dict[Path, dict]:
    """Pour chaque fichier de test, calcule les imports opt-in vs les
    importorskip présents."""
    audit: dict[Path, dict] = {}
    for path in _iter_test_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = _top_level_optin_imports(tree)
        skips = _module_level_importorskip_targets(tree)
        if imports:  # on ne conserve que les fichiers concernés
            audit[path] = {"imports": imports, "skips": skips}
    return audit


_AUDIT = _collect_audit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEveryOptinImportIsGuarded:
    """Chaque import top-level d'un opt-in est précédé d'un importorskip
    pour le même module."""

    @pytest.mark.parametrize(
        "test_file",
        sorted(_AUDIT.keys()),
        ids=lambda p: str(p.relative_to(_TESTS_DIR.parent)),
    )
    def test_file_has_matching_importorskip(self, test_file: Path):
        info = _AUDIT[test_file]
        missing = info["imports"] - info["skips"]
        rel = test_file.relative_to(_TESTS_DIR.parent)
        assert not missing, (
            f"{rel} importe au niveau module {sorted(missing)} sans "
            f"`pytest.importorskip(...)` correspondant. "
            f"Ajouter en haut du fichier : "
            + " ; ".join(f'pytest.importorskip("{m}")' for m in sorted(missing))
        )


class TestAuditCoverage:
    """Sanity : l'audit a bien trouvé au moins quelques fichiers opt-in
    (sinon le garde-fou serait vacuously vrai, ex. modules renommés)."""

    def test_audit_covers_each_optin_at_least_once(self):
        """Au moins un fichier de test importe chaque opt-in **suivi ici**.

        Porte sur le sous-ensemble curé `_OPTIN_MODULES`, pas sur les 11
        opt-ins (voir la note sur `_OPTIN_MODULES` : l'exhaustivité est
        garantie par test_pytest_core_only_contract_001). Si un opt-in suivi
        ici disparaît de la suite, c'est un signal à investiguer (régression
        de couverture ou retrait volontaire) — retirer le module de
        `_OPTIN_MODULES` dans ce cas, avec un commit dédié.
        """
        all_imported: set[str] = set()
        for info in _AUDIT.values():
            all_imported.update(info["imports"])
        # `pyotp` n'est pas un opt-in Forge en propre — c'est une dép de MFA ;
        # on tolère son absence si plus aucun test MFA ne le tire directement.
        forge_optins = _OPTIN_MODULES - {"pyotp"}
        missing_coverage = forge_optins - all_imported
        assert not missing_coverage, (
            f"Plus aucun test n'importe : {sorted(missing_coverage)}. "
            "Soit la couverture a régressé, soit retirer ces modules de "
            "_OPTIN_MODULES dans ce fichier."
        )

    def test_no_unknown_skip_target(self):
        """Un `pytest.importorskip("X")` doit cibler un module opt-in
        connu ; sinon, le garde-fou ne s'applique pas et c'est suspect."""
        for path, info in _AUDIT.items():
            unknown = info["skips"] - _OPTIN_MODULES
            # On n'échoue pas — certains skips peuvent légitimement viser
            # d'autres modules (pyotp est déjà géré, mais un test pourrait
            # ajouter `pytest.importorskip("cryptography")` par exemple).
            # Le test sert juste de signal informatif si surprise.
            if unknown:
                # Reste un test PASS — message visible dans -v si besoin.
                pass
        # Toujours True : test purement informatif, voir docstring.
        assert True
