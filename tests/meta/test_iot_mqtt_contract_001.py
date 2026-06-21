"""Garde-fou IOT-MQTT-CONTRACT-001.

Vérifie que la page de contrat MQTT ``docs/iot/mqtt-contract.md`` existe,
est référencée dans la navigation MkDocs, et fige le format des topics
et du payload JSON avant l'écriture du subscriber.

Le contrat est **documentaire** : ce test n'exécute aucune logique
MQTT. Il s'assure uniquement que les décisions architecturales restent
visibles et stables :

- topic canonique ``forge/{site}/{device_id}/telemetry`` ;
- champs obligatoires ``kind``, ``value``, ``unit``, ``timestamp`` ;
- ``site`` et ``device_id`` viennent du topic, pas du payload ;
- au moins un exemple valide et un exemple invalide ;
- liste de codes d'erreur stable.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

CONTRACT_PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "mqtt-contract.md"
MKDOCS_YML = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"

REQUIRED_FIELDS = ("kind", "value", "unit", "timestamp")
OPTIONAL_FIELDS = ("metadata",)
ERROR_CODES = (
    "TOPIC_PATTERN",
    "PAYLOAD_PARSE",
    "PAYLOAD_FIELD_MISSING",
    "PAYLOAD_FIELD_TYPE",
    "PAYLOAD_VALUE_FORMAT",
)


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PAGE.read_text(encoding="utf-8")


class TestContractPageExists:
    def test_file_present(self):
        assert CONTRACT_PAGE.exists(), (
            f"{CONTRACT_PAGE.relative_to(PROJECT_ROOT)} doit exister"
        )

    def test_file_substantial(self, contract_text):
        assert len(contract_text) > 1500, (
            "La page de contrat MQTT doit être substantielle (> 1500 caractères)."
        )


class TestNavReference:
    def test_listed_in_mkdocs_yml(self):
        text = MKDOCS_YML.read_text(encoding="utf-8")
        assert "mqtt-contract.md" in text, (
            "docs/iot/mqtt-contract.md doit être référencé dans mkdocs.yml"
        )


class TestTopicContract:
    def test_topic_pattern_documented(self, contract_text):
        # Forme canonique exacte explicite (le `{` ne doit pas être interprété
        # par Jinja/MkDocs car la page n'utilise pas le moteur de macros).
        assert "forge/{site}/{device_id}/telemetry" in contract_text, (
            "Le topic canonique forge/{site}/{device_id}/telemetry doit "
            "apparaître textuellement dans la page"
        )

    def test_topic_example_present(self, contract_text):
        # Un exemple concret du topic doit figurer pour servir de référence.
        assert "forge/atelier/esp32-001/telemetry" in contract_text


class TestPayloadFields:
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_required_field_documented(self, contract_text, field):
        assert f"`{field}`" in contract_text, (
            f"Le champ obligatoire `{field}` doit être documenté"
        )

    @pytest.mark.parametrize("field", OPTIONAL_FIELDS)
    def test_optional_field_documented(self, contract_text, field):
        assert f"`{field}`" in contract_text, (
            f"Le champ optionnel `{field}` doit être documenté"
        )


class TestArchitecturalDecision:
    """site/device_id viennent du topic, pas du payload."""

    def test_decision_stated_explicitly(self, contract_text):
        # On exige une formulation claire : "site" et "device_id" viennent
        # du topic.
        assert "viennent du topic" in contract_text, (
            "La décision « site et device_id viennent du topic » doit "
            "être présente textuellement"
        )

    def test_decision_section_present(self, contract_text):
        assert "Décision" in contract_text or "décision" in contract_text


class TestExamples:
    """La page contient au moins un exemple valide et un exemple invalide."""

    def _extract_json_blocks(self, text: str) -> list[str]:
        # Capture les blocs ``` json … ```.
        return re.findall(r"```json\s*(.*?)```", text, flags=re.DOTALL)

    def test_at_least_one_valid_example(self, contract_text):
        blocks = self._extract_json_blocks(contract_text)
        parsed_valid: list[dict] = []
        for block in blocks:
            try:
                obj = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if all(field in obj for field in REQUIRED_FIELDS):
                parsed_valid.append(obj)
        assert parsed_valid, (
            "La page doit contenir au moins un exemple JSON valide "
            "(parsable et contenant tous les champs obligatoires)."
        )

    def test_valid_example_types_consistent(self, contract_text):
        """Le premier exemple valide doit respecter les types du contrat."""
        blocks = self._extract_json_blocks(contract_text)
        for block in blocks:
            try:
                obj = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if not all(field in obj for field in REQUIRED_FIELDS):
                continue
            assert isinstance(obj["kind"], str), "kind doit être string"
            assert isinstance(obj["value"], (int, float)), (
                "value doit être number (int|float)"
            )
            assert isinstance(obj["unit"], str), "unit doit être string"
            assert isinstance(obj["timestamp"], str), "timestamp doit être string"
            # On a trouvé au moins un exemple valide bien typé : sortir.
            return
        pytest.fail("Aucun exemple JSON valide n'a pu être contrôlé.")

    def test_at_least_one_invalid_example_section(self, contract_text):
        # Une section dédiée aux exemples invalides doit exister.
        assert "## Exemples invalides" in contract_text or (
            "Exemples invalides" in contract_text
        ), "Une section « Exemples invalides » doit figurer dans la page"


class TestErrorCodes:
    @pytest.mark.parametrize("code", ERROR_CODES)
    def test_error_code_documented(self, contract_text, code):
        assert code in contract_text, (
            f"Le code d'erreur de contrat {code} doit figurer dans la page"
        )


class TestDocumentaryStatus:
    """Le contrat doit explicitement indiquer qu'il est documentaire."""

    def test_status_documentary(self, contract_text):
        # Une mention claire que le contrat est documentaire, pas encore
        # implémenté.
        markers = (
            "contrat documentaire",
            "contrat **documentaire**",
            "documentaire — pas",
            "aucun subscriber",
            "documentaire** — aucun",
        )
        assert any(m in contract_text for m in markers), (
            "La page doit indiquer explicitement que le contrat est "
            "documentaire et qu'aucun subscriber MQTT n'existe encore."
        )


class TestRoadmapMention:
    def test_roadmap_lists_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "IOT-MQTT-CONTRACT-001" in text, (
            "docs/roadmap/forge-roadmap.md doit lister IOT-MQTT-CONTRACT-001"
        )
