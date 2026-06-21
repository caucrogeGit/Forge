"""Configuration TLS MQTT Forge IoT — IOT-CONFIG-TLS-001.

Prépare la configuration TLS sans la brancher dans les clients MQTT
(découpage : le câblage paho viendra dans IOT-MQTT-TLS-CLIENTS-001). Les
tests vérifient :

- TLS désactivé par défaut ;
- ``true``/``1``/``yes``/``on`` (toute casse) activent TLS ;
- ``false``/``0``/``no``/``off`` désactivent TLS ;
- valeur vide → désactivé ;
- valeur invalide → ``ValueError`` ;
- CA file vide → ``None``, CA file non vide conservé ;
- compatibilité ascendante d'``IotConfig`` (construction à 6 / 7 champs) ;
- ``repr()`` ne fuite ni mot de passe, ni token, ni chemin de certificat ;
- les variables TLS sont documentées.

Aucun broker n'est contacté ; aucune connexion TLS n'est ouverte (hors
périmètre de ce ticket).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.config import (
    DEFAULT_TLS_ENABLED,
    ENV_PASSWORD,
    ENV_TLS_CA_FILE,
    ENV_TLS_ENABLED,
    IotConfig,
    load_iot_config,
)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DOC = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "configuration.md"
MOSQUITTO_DOC = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "mosquitto-local.md"


# ── Défaut : TLS désactivé ───────────────────────────────────────────────────


class TestTlsDefaults:
    def test_tls_disabled_by_default(self):
        cfg = load_iot_config({})
        assert cfg.mqtt_tls_enabled is False
        assert DEFAULT_TLS_ENABLED is False

    def test_ca_file_none_by_default(self):
        assert load_iot_config({}).mqtt_tls_ca_file is None


# ── Parsing booléen ──────────────────────────────────────────────────────────


class TestTlsEnabledParsing:
    @pytest.mark.parametrize(
        "raw", ["true", "1", "yes", "on", "TRUE", "Yes", "On", " true "],
    )
    def test_truthy_values_enable_tls(self, raw):
        cfg = load_iot_config({ENV_TLS_ENABLED: raw})
        assert cfg.mqtt_tls_enabled is True

    @pytest.mark.parametrize(
        "raw", ["false", "0", "no", "off", "FALSE", "No", "Off", " off "],
    )
    def test_falsy_values_disable_tls(self, raw):
        cfg = load_iot_config({ENV_TLS_ENABLED: raw})
        assert cfg.mqtt_tls_enabled is False

    def test_empty_value_disables_tls(self):
        assert load_iot_config({ENV_TLS_ENABLED: ""}).mqtt_tls_enabled is False

    def test_whitespace_only_disables_tls(self):
        assert load_iot_config({ENV_TLS_ENABLED: "   "}).mqtt_tls_enabled is False

    @pytest.mark.parametrize("bad", ["maybe", "2", "enabled", "tru", "oui"])
    def test_invalid_value_raises(self, bad):
        with pytest.raises(ValueError, match=ENV_TLS_ENABLED):
            load_iot_config({ENV_TLS_ENABLED: bad})


# ── CA file ──────────────────────────────────────────────────────────────────


class TestTlsCaFile:
    def test_ca_file_kept_when_set(self):
        path = "/etc/ssl/certs/mosquitto-ca.crt"
        cfg = load_iot_config({ENV_TLS_CA_FILE: path})
        assert cfg.mqtt_tls_ca_file == path

    def test_empty_ca_file_becomes_none(self):
        assert load_iot_config({ENV_TLS_CA_FILE: ""}).mqtt_tls_ca_file is None

    def test_ca_file_independent_of_tls_flag(self):
        # On peut renseigner un CA file même si TLS n'est pas (encore) activé
        # — la cohérence d'usage est laissée au ticket de câblage clients.
        cfg = load_iot_config({ENV_TLS_CA_FILE: "/tmp/ca.crt"})
        assert cfg.mqtt_tls_enabled is False
        assert cfg.mqtt_tls_ca_file == "/tmp/ca.crt"


# ── Combinaison réaliste ─────────────────────────────────────────────────────


class TestRealisticTlsConfig:
    def test_tls_enabled_with_ca_file(self):
        cfg = load_iot_config({
            ENV_TLS_ENABLED: "true",
            ENV_TLS_CA_FILE: "/etc/ssl/certs/mosquitto-ca.crt",
        })
        assert cfg.mqtt_tls_enabled is True
        assert cfg.mqtt_tls_ca_file == "/etc/ssl/certs/mosquitto-ca.crt"


# ── Compatibilité ascendante d'IotConfig ─────────────────────────────────────


class TestBackwardCompatibility:
    def test_six_field_construction_still_valid(self):
        cfg = IotConfig(
            mqtt_host="localhost", mqtt_port=1883,
            mqtt_topic="forge/+/+/telemetry", mqtt_client_id="forge-iot",
            mqtt_username=None, mqtt_password=None,
        )
        assert cfg.mqtt_tls_enabled is False
        assert cfg.mqtt_tls_ca_file is None
        assert cfg.api_token is None

    def test_seven_field_construction_still_valid(self):
        cfg = IotConfig(
            mqtt_host="localhost", mqtt_port=1883,
            mqtt_topic="forge/+/+/telemetry", mqtt_client_id="forge-iot",
            mqtt_username=None, mqtt_password=None, api_token="t",
        )
        assert cfg.mqtt_tls_enabled is False
        assert cfg.mqtt_tls_ca_file is None


# ── repr() ne fuite aucun secret ─────────────────────────────────────────────


class TestReprDoesNotLeak:
    def test_repr_shows_tls_enabled(self):
        cfg = load_iot_config({ENV_TLS_ENABLED: "true"})
        assert "mqtt_tls_enabled=True" in repr(cfg)

    def test_repr_masks_ca_file_path(self):
        secret_path = "/secret/path/private-ca-xyz.crt"
        cfg = load_iot_config({ENV_TLS_CA_FILE: secret_path})
        text = repr(cfg)
        assert secret_path not in text
        assert "mqtt_tls_ca_file='***'" in text

    def test_repr_ca_file_none_shown_as_none(self):
        assert "mqtt_tls_ca_file=None" in repr(load_iot_config({}))

    def test_repr_still_masks_password(self):
        cfg = load_iot_config({
            ENV_PASSWORD: "s3cr3t-pwd", ENV_TLS_ENABLED: "true",
        })
        assert "s3cr3t-pwd" not in repr(cfg)

    def test_ca_file_accessible_in_clear_on_attribute(self):
        # Les clients (futur ticket) liront l'attribut en clair ; seul le
        # repr est masqué.
        cfg = load_iot_config({ENV_TLS_CA_FILE: "/etc/ca.crt"})
        assert cfg.mqtt_tls_ca_file == "/etc/ca.crt"


# ── Documentation ────────────────────────────────────────────────────────────


class TestDocumentation:
    def test_configuration_doc_mentions_both_tls_vars(self):
        text = CONFIG_DOC.read_text(encoding="utf-8")
        assert ENV_TLS_ENABLED in text
        assert ENV_TLS_CA_FILE in text

    def test_mosquitto_doc_states_no_tls(self):
        text = MOSQUITTO_DOC.read_text(encoding="utf-8").lower()
        assert "tls" in text
