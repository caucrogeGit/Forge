"""ADR-087 : cliquet sur les deux règles de style mécanisables.

L'ADR-087 pose sept règles de rédaction. Deux se contrôlent sans ambiguïté :
l'absence de tiret cadratin (règle 3) et l'unicité du deux-points par phrase
(règle 5). Les cinq autres relèvent du jugement, et un contrôle approximatif
produirait des faux positifs qui feraient désactiver l'ensemble.

Ce garde-fou est un **cliquet**, sur le modèle de celui de la portabilité du
DDL : le fonds existant est gelé en l'état, et les listes ci-dessous ne peuvent
que **décroître**. Aucune campagne de réécriture n'est imposée, mais aucun
nouveau fichier ne peut enfreindre ces deux règles.

Le test échoue dans les **deux** sens. Un fichier qui entre dans la liste est
une régression ; un fichier qui en sort sans être retiré de la liste laisse le
cliquet se relâcher, et la liste doit être mise à jour dans le même commit.

Les archives sont hors périmètre : `docs/history/` est la mémoire brute du
projet, et le site publié ainsi que les dossiers de construction ne sont pas des
sources.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

EM_DASH = "—"

EXCLUDED_PARTS = (
    "docs/history",
    "/build/",
    "/.venv/",
    "/__pycache__/",
    "official-site/docs/forge",
    "/tmp/",
    "/node_modules/",
)

EM_DASH_LEGACY = frozenset({
    "CHANGELOG.md",
    "CHARTE_DOC.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "core/http/docs/request.md",
    "official-site/README.md",
    "official-site/docs/audits/FW-ACCESS-LOGS-STATS-001.md",
    "official-site/docs/audits/FW-AUDIT-EXISTING-001.md",
    "official-site/docs/audits/FW-CADDY-DOMAIN-HTTP-001.md",
    "official-site/docs/audits/FW-CLOUDFLARE-DNS-HTTP-001.md",
    "official-site/docs/audits/FW-CONTENT-PUBLIC-COHERENCE-001.md",
    "official-site/docs/audits/FW-CONTENT-SYNC-FORGE-CURRENT-001.md",
    "official-site/docs/audits/FW-DEPLOY-GO-001.md",
    "official-site/docs/audits/FW-DEPLOY-PREP-001.md",
    "official-site/docs/audits/FW-DNS-WEB-001.md",
    "official-site/docs/audits/FW-DOCS-IMPORT-001.md",
    "official-site/docs/audits/FW-FINAL-PUBLISH-AUDIT-001.md",
    "official-site/docs/audits/FW-GOACCESS-STATS-001.md",
    "official-site/docs/audits/FW-HTTPS-PORT-443-001.md",
    "official-site/docs/audits/FW-LANDING-FINALIZE-001.md",
    "official-site/docs/audits/FW-LOCAL-QA-001.md",
    "official-site/docs/audits/FW-MKDOCS-INIT-001.md",
    "official-site/docs/audits/FW-NAV-DOCS-STRUCTURE-001.md",
    "official-site/docs/audits/FW-PUBLISH-READINESS-001.md",
    "official-site/docs/audits/FW-REPO-STRUCTURE-001.md",
    "official-site/docs/audits/FW-ROUTER-PORTS-AUDIT-001.md",
    "official-site/docs/audits/FW-SERVER-TARGET-AUDIT-001.md",
    "official-site/docs/audits/FW-SERVER-TARGET-AUDIT-002.md",
    "official-site/docs/audits/OFFICIAL-SITE-LOCAL-DOCS-LINKS-001.md",
    "official-site/docs/audits/forge-official-site-sync-beta10.md",
    "official-site/docs/audits/forge-web-secret-exposure-audit.md",
    "official-site/docs/deployment-readiness.md",
    "official-site/docs/meta/01-architecture-generale-forge-web.md",
    "official-site/docs/meta/02-creation-depot-forge-web.md",
    "official-site/docs/operations/manual-forge-docs-publication.md",
    "official-site/docs/security/deployment-secrets.md",
    "packages/forge-mvc-audio/README.md",
    "packages/forge-mvc-deploy/README.md",
    "packages/forge-mvc-files/README.md",
    "packages/forge-mvc-fixtures/README.md",
    "packages/forge-mvc-images/README.md",
    "packages/forge-mvc-iot/README.md",
    "packages/forge-mvc-mfa/README.md",
    "packages/forge-mvc-stats/README.md",
    "packages/forge-mvc-workflow/README.md",
    "storage/logs/errors.dev.md",
    "tests/fixtures/app/storage/logs/errors.dev.md",
})

MULTI_COLON_LEGACY = frozenset({
    "CHANGELOG.md",
    "core/modules/docs/manifest.md",
    "docs/adr/028-welcome-forge-tutorial-per-level.md",
    "docs/adr/031-mail-core-decoupling.md",
    "docs/adr/040-per-package-test-surface.md",
    "docs/adr/044-framework-only-repo.md",
    "docs/adr/045-official-site-integration.md",
    "docs/adr/056-rbac-contract-tooling-extraction.md",
    "docs/adr/061-optin-project-registry.md",
    "docs/adr/069-foreign-key-field-type.md",
    "docs/adr/070-entities-engine-extraction.md",
    "docs/adr/072-optin-cli-command-contract.md",
    "docs/adr/077-fixtures-reliees.md",
    "docs/contributing/starter-welcome-model.md",
    "docs/features/crud.md",
    "docs/install/vscode.md",
    "docs/philosophy/licence.md",
    "docs/roadmap/forge-admin-roadmap.md",
    "docs/roadmap/forge-roadmap.md",
    "docs/roadmap/roadmap-forge-contrats-json-schema.md",
    "docs/starters/index.md",
    "docs/starters/welcome-events/bilan.md",
    "docs/starters/welcome-helpers/bilan.md",
    "docs/starters/welcome-helpers/installation.md",
    "docs/starters/welcome-markdown/avance/notes-et-attributs.md",
    "docs/starters/welcome-markdown/avance/texte-enrichi.md",
    "docs/starters/welcome-markdown/intermediaire/code.md",
    "docs/testing/tickets/ft-01-install-version-check-001.md",
    "official-site/docs/audits/FW-AUDIT-EXISTING-001.md",
    "official-site/docs/audits/FW-DOCS-IMPORT-001.md",
    "official-site/docs/audits/FW-LOCAL-QA-001.md",
    "official-site/docs/audits/FW-MKDOCS-INIT-001.md",
    "official-site/docs/audits/FW-PUBLISH-READINESS-001.md",
    "official-site/docs/audits/FW-REPO-STRUCTURE-001.md",
    "official-site/docs/meta/01-architecture-generale-forge-web.md",
    "packages/forge-mvc-audio/docs/welcome/debutant/audio-play.md",
    "packages/forge-mvc-audio/docs/welcome/debutant/audio-upload.md",
    "packages/forge-mvc-entities/docs/modules/db_apply.md",
    "packages/forge-mvc-files/docs/welcome/avance/file-safe-path.md",
    "packages/forge-mvc-files/docs/welcome/intermediaire/file-validate.md",
    "packages/forge-mvc-fixtures/docs/welcome/avance/fixtures-reliees.md",
    "packages/forge-mvc-images/docs/welcome/avance/image-delete.md",
    "packages/forge-mvc-images/docs/welcome/avance/image-safety.md",
    "packages/forge-mvc-images/docs/welcome/intermediaire/image-alt-order.md",
    "packages/forge-mvc-iot/docs/architecture.md",
    "packages/forge-mvc-iot/docs/doctor.md",
    "packages/forge-mvc-iot/docs/esp32-example.md",
    "packages/forge-mvc-iot/docs/listen-command.md",
    "packages/forge-mvc-iot/docs/mosquitto-local.md",
    "packages/forge-mvc-iot/docs/simulator.md",
    "packages/forge-mvc-mfa/docs/welcome/avance/mfa-crypto.md",
    "packages/forge-mvc-mfa/docs/welcome/intermediaire/mfa-challenge.md",
    "packages/forge-mvc-mfa/docs/welcome/intermediaire/mfa-enroll.md",
    "packages/forge-mvc-mssql/docs/reference.md",
    "packages/forge-mvc-rbac/docs/references/jinja.md",
    "packages/forge-mvc-rbac/docs/welcome/avance/rbac-request-roles.md",
    "packages/forge-mvc-stats/docs/reference.md",
    "packages/forge-mvc-stats/docs/welcome/intermediaire/bilan.md",
    "storage/logs/errors.dev.md",
    "tests/fixtures/app/storage/logs/errors.dev.md",
})


def _markdown_files() -> list[Path]:
    return sorted(
        p for p in PROJECT_ROOT.rglob("*.md")
        if not any(part in p.as_posix() for part in EXCLUDED_PARTS)
    )


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _has_em_dash(text: str) -> bool:
    return EM_DASH in text


def _has_multi_colon_sentence(text: str) -> bool:
    """Une ligne de prose portant deux deux-points ou plus.

    Sont ignorés : les blocs de code, les tableaux, les titres, les citations et
    les listes, où le deux-points est structurel et non rédactionnel. Les URL et
    le code en ligne sont retirés avant comptage, leurs deux-points
    n'appartenant pas à la phrase.
    """
    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue
        if stripped.startswith(("|", "#", ">", "-", "*", "!")):
            continue
        without_urls = re.sub(r"https?://\S+", "", stripped)
        without_code = re.sub(r"`[^`]*`", "", without_urls)
        if without_code.count(":") >= 2:
            return True
    return False


def _offenders(predicate: "object") -> set[str]:
    found: set[str] = set()
    for path in _markdown_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover - binaire inattendu
            continue
        if predicate(text):  # type: ignore[operator]
            found.add(_relative(path))
    return found


def _assert_ratchet(actual: set[str], frozen: frozenset[str], regle: str) -> None:
    nouveaux = sorted(actual - frozen)
    corriges = sorted(frozen - actual)

    assert not nouveaux, (
        f"ADR-087, {regle} : nouveau(x) fichier(s) non conforme(s) {nouveaux}. "
        "Le fonds existant est gelé, mais aucune nouvelle infraction n'est admise."
    )
    assert not corriges, (
        f"ADR-087, {regle} : {corriges} ne sont plus fautifs, très bien. "
        "Retirez-les de la liste gelée dans ce même commit, sinon le cliquet se relâche."
    )


def test_cliquet_tiret_cadratin() -> None:
    """Règle 3 : pas de tiret cadratin, la liste ne peut que décroître."""
    _assert_ratchet(_offenders(_has_em_dash), EM_DASH_LEGACY, "tiret cadratin")


def test_cliquet_deux_points_multiples() -> None:
    """Règle 5 : au plus un deux-points par phrase, la liste ne peut que décroître."""
    _assert_ratchet(_offenders(_has_multi_colon_sentence), MULTI_COLON_LEGACY, "deux-points")


def test_l_adr_087_existe_et_porte_les_sept_regles() -> None:
    """Le garde-fou ne vaut que si sa source est là."""
    adr = (PROJECT_ROOT / "docs" / "adr" / "087-documentation-style-canonical.md").read_text(
        encoding="utf-8"
    )

    for regle in ("**Langue**", "**Une phrase par ligne**", "**Pas de tiret cadratin**",
                  "**Ponctuation française**", "**Au plus un deux-points par phrase**",
                  "**Liens internes**", "**Éviter les anglicismes**"):
        assert regle in adr, f"règle absente de l'ADR-087 : {regle}"


def test_le_briefing_renvoie_a_l_adr_plutot_que_de_le_dupliquer() -> None:
    """CLAUDE.md §2.1 pointe la source, il ne réénonce pas la règle en double."""
    briefing = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "087-documentation-style-canonical.md" in briefing


def test_le_gabarit_projet_declare_sa_source() -> None:
    """Le `002-style-documentation.md` posé dans les projets dérive de l'ADR-087."""
    gabarit = (PROJECT_ROOT / "cli" / "agents" / "seed_adr.py").read_text(encoding="utf-8")

    assert "ADR-087" in gabarit
    assert "Au plus un deux-points par phrase" in gabarit
