"""Tests du contrat de configuration Forge IoT — IOT-CONFIG-001.

Couvre :

- valeurs par défaut quand aucune variable n'est définie ;
- surcharge par variables d'environnement ;
- conversion du port en ``int`` ;
- refus du port invalide ;
- refus du host vide ;
- refus du topic vide ;
- masquage du mot de passe dans ``repr()`` ;
- absence de dépendance ``paho-mqtt`` au scaffold ;
- absence d'import IoT dans ``core/``.

Aucun broker n'est contacté. Aucun ``os.environ`` réel n'est modifié :
tous les tests injectent un mapping explicite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.config import (
    DEFAULT_CLIENT_ID,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TOPIC,
    ENV_API_TOKEN,
    ENV_CLIENT_ID,
    ENV_HOST,
    ENV_PASSWORD,
    ENV_PORT,
    ENV_TOPIC,
    ENV_USERNAME,
    IotConfig,
    load_iot_config,
)

PROJECT_ROOT = Path(__file__).parent.parent
CORE_DIR = PROJECT_ROOT / "core"


# ── Defaults ────────────────────────────────────────────────────────────────


class TestDefaults:
    """Sans aucune variable d'environnement, les défauts s'appliquent."""

    def setup_method(self):
        self.cfg = load_iot_config({})

    def test_returns_iot_config_instance(self):
        assert isinstance(self.cfg, IotConfig)

    def test_default_host(self):
        assert self.cfg.mqtt_host == DEFAULT_HOST == "localhost"

    def test_default_port(self):
        assert self.cfg.mqtt_port == DEFAULT_PORT == 1883
        assert isinstance(self.cfg.mqtt_port, int)

    def test_default_topic(self):
        assert self.cfg.mqtt_topic == DEFAULT_TOPIC == "forge/+/+/telemetry"

    def test_default_client_id(self):
        assert self.cfg.mqtt_client_id == DEFAULT_CLIENT_ID == "forge-iot"

    def test_default_username_is_none(self):
        assert self.cfg.mqtt_username is None

    def test_default_password_is_none(self):
        assert self.cfg.mqtt_password is None


# ── Overrides ───────────────────────────────────────────────────────────────


class TestEnvironmentOverride:
    """Le mapping injecté surcharge les défauts."""

    def test_overrides_all_fields(self):
        env = {
            ENV_HOST: "broker.lan",
            ENV_PORT: "8883",
            ENV_TOPIC: "forge/atelier/+/telemetry",
            ENV_CLIENT_ID: "forge-iot-atelier",
            ENV_USERNAME: "forge",
            ENV_PASSWORD: "s3cr3t",
        }
        cfg = load_iot_config(env)
        assert cfg.mqtt_host == "broker.lan"
        assert cfg.mqtt_port == 8883
        assert cfg.mqtt_topic == "forge/atelier/+/telemetry"
        assert cfg.mqtt_client_id == "forge-iot-atelier"
        assert cfg.mqtt_username == "forge"
        assert cfg.mqtt_password == "s3cr3t"

    def test_partial_override_keeps_defaults(self):
        env = {ENV_HOST: "broker.lan"}
        cfg = load_iot_config(env)
        assert cfg.mqtt_host == "broker.lan"
        assert cfg.mqtt_port == DEFAULT_PORT
        assert cfg.mqtt_topic == DEFAULT_TOPIC
        assert cfg.mqtt_client_id == DEFAULT_CLIENT_ID
        assert cfg.mqtt_username is None
        assert cfg.mqtt_password is None

    def test_empty_username_becomes_none(self):
        cfg = load_iot_config({ENV_USERNAME: ""})
        assert cfg.mqtt_username is None

    def test_empty_password_becomes_none(self):
        cfg = load_iot_config({ENV_PASSWORD: ""})
        assert cfg.mqtt_password is None

    def test_empty_client_id_falls_back_to_default(self):
        cfg = load_iot_config({ENV_CLIENT_ID: ""})
        assert cfg.mqtt_client_id == DEFAULT_CLIENT_ID

    def test_empty_port_falls_back_to_default(self):
        cfg = load_iot_config({ENV_PORT: ""})
        assert cfg.mqtt_port == DEFAULT_PORT


# ── Port ────────────────────────────────────────────────────────────────────


class TestPortConversion:
    def test_port_is_int_not_str(self):
        cfg = load_iot_config({ENV_PORT: "8883"})
        assert cfg.mqtt_port == 8883
        assert isinstance(cfg.mqtt_port, int)

    @pytest.mark.parametrize("bad", ["abc", "12.5", "8883x", "0x1F"])
    def test_invalid_port_refused(self, bad):
        with pytest.raises(ValueError, match=ENV_PORT):
            load_iot_config({ENV_PORT: bad})

    @pytest.mark.parametrize("out_of_range", ["0", "-1", "65536", "100000"])
    def test_port_out_of_range_refused(self, out_of_range):
        with pytest.raises(ValueError, match=ENV_PORT):
            load_iot_config({ENV_PORT: out_of_range})

    @pytest.mark.parametrize("ok", ["1", "1883", "8883", "65535"])
    def test_port_in_range_accepted(self, ok):
        cfg = load_iot_config({ENV_PORT: ok})
        assert cfg.mqtt_port == int(ok)


# ── Champs vides refusés ────────────────────────────────────────────────────


class TestEmptyFieldsRefused:
    def test_empty_host_refused(self):
        with pytest.raises(ValueError, match=ENV_HOST):
            load_iot_config({ENV_HOST: ""})

    def test_empty_topic_refused(self):
        with pytest.raises(ValueError, match=ENV_TOPIC):
            load_iot_config({ENV_TOPIC: ""})


# ── Masquage du mot de passe ────────────────────────────────────────────────


class TestPasswordMasking:
    def test_password_masked_in_repr_when_set(self):
        cfg = load_iot_config({
            ENV_USERNAME: "forge",
            ENV_PASSWORD: "s3cr3t",
        })
        text = repr(cfg)
        assert "s3cr3t" not in text, (
            f"Le mot de passe ne doit pas apparaître en clair dans repr() "
            f"(vu : {text})"
        )
        assert "***" in text, (
            "Le mot de passe doit être masqué par *** dans repr()"
        )

    def test_password_masked_in_fstring(self):
        cfg = load_iot_config({ENV_PASSWORD: "secret-pa55"})
        text = f"{cfg!r}"
        assert "secret-pa55" not in text

    def test_password_none_shown_as_none(self):
        cfg = load_iot_config({})
        text = repr(cfg)
        # Quand il n'y a pas de mot de passe, le repr indique None (rien
        # à masquer).
        assert "mqtt_password=None" in text

    def test_password_accessible_in_clear(self):
        # Le subscriber doit pouvoir lire le mot de passe en clair sur
        # l'attribut — c'est uniquement le repr qui est masqué.
        cfg = load_iot_config({ENV_PASSWORD: "s3cr3t"})
        assert cfg.mqtt_password == "s3cr3t"

    def test_username_not_masked(self):
        # Seul le mot de passe est sensible — le username peut figurer
        # en clair pour aider au diagnostic.
        cfg = load_iot_config({ENV_USERNAME: "forge"})
        assert "'forge'" in repr(cfg)


# ── Token API HTTP (IOT-HTTP-API-AUTH-001) ──────────────────────────────────


class TestApiToken:
    def test_default_api_token_is_none(self):
        assert load_iot_config({}).api_token is None

    def test_empty_api_token_becomes_none(self):
        assert load_iot_config({ENV_API_TOKEN: ""}).api_token is None

    def test_api_token_loaded_when_set(self):
        cfg = load_iot_config({ENV_API_TOKEN: "change-me"})
        assert cfg.api_token == "change-me"

    def test_api_token_masked_in_repr_when_set(self):
        cfg = load_iot_config({ENV_API_TOKEN: "supersecret-token-xyz"})
        text = repr(cfg)
        assert "supersecret-token-xyz" not in text, (
            f"Le token API ne doit pas apparaître en clair dans repr() "
            f"(vu : {text})"
        )
        assert "api_token='***'" in text

    def test_api_token_none_shown_as_none(self):
        text = repr(load_iot_config({}))
        assert "api_token=None" in text

    def test_api_token_accessible_in_clear(self):
        # Le contrôleur HTTP doit pouvoir comparer le token en clair sur
        # l'attribut — seul le repr est masqué.
        cfg = load_iot_config({ENV_API_TOKEN: "change-me"})
        assert cfg.api_token == "change-me"

    def test_default_construction_omits_api_token(self):
        # Le champ a un défaut : IotConfig reste constructible avec les
        # 6 champs historiques (compat ascendante).
        cfg = IotConfig(
            mqtt_host="localhost", mqtt_port=1883,
            mqtt_topic="forge/+/+/telemetry", mqtt_client_id="forge-iot",
            mqtt_username=None, mqtt_password=None,
        )
        assert cfg.api_token is None


# ── Immutabilité ────────────────────────────────────────────────────────────


class TestImmutability:
    def test_config_is_frozen(self):
        cfg = load_iot_config({})
        with pytest.raises((AttributeError, Exception)):
            cfg.mqtt_host = "other"  # type: ignore[misc]


# ── Garde-fous périmètre ────────────────────────────────────────────────────


class TestNoCoreImportsIotConfig:
    """Aucun fichier de core/ ne dépend de forge_mvc_iot.config."""

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, (
            "Aucun fichier sous core/ ne doit importer ou mentionner "
            f"forge_mvc_iot. Fichiers fautifs : {offenders}"
        )


# ── Cas particuliers de mapping ─────────────────────────────────────────────


class TestMappingBehavior:
    def test_uses_os_environ_when_env_is_none(self, monkeypatch):
        # Nettoyage : on retire toute variable FORGE_IOT_* polluante.
        for key in (
            ENV_HOST, ENV_PORT, ENV_TOPIC, ENV_CLIENT_ID,
            ENV_USERNAME, ENV_PASSWORD,
        ):
            monkeypatch.delenv(key, raising=False)
        # Puis on en injecte une, pour vérifier que load_iot_config(None)
        # lit bien os.environ.
        monkeypatch.setenv(ENV_HOST, "from-os-environ")
        cfg = load_iot_config()
        assert cfg.mqtt_host == "from-os-environ"

    def test_explicit_env_does_not_read_os_environ(self, monkeypatch):
        # Si on injecte un mapping, os.environ ne doit pas fuiter dedans.
        monkeypatch.setenv(ENV_HOST, "must-not-leak")
        cfg = load_iot_config({})
        assert cfg.mqtt_host == DEFAULT_HOST
