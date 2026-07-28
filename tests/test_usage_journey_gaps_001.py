"""USAGE-JOURNEY-GAPS-001 : trois accrocs du parcours d'utilisation.

Trouvés en déroulant le parcours documenté de bout en bout sur un vrai serveur :
`db:config`, `db:init`, `build:model`, `migration:apply`, puis usage sous le
compte applicatif.

**1. `build:model` exigeait `relations.json`.** `entity:validate` le déclarait
« optionnel », le squelette ne le livre pas, et seul `make:relation` l'écrit.
Un projet à une entité **sans relation**, le cas le plus courant au premier
jour, ne pouvait donc pas franchir `build:model`.

**2. `db:config` écrivait hors d'un projet Forge.** Il posait ses fichiers dans
n'importe quel dossier, alors que `db:init` refuse ensuite d'y travailler faute
de `config.py`.

**3. `forge doctor` rassurait à tort.** Le contrôle de base était codé en dur en
avertissement, avec le message « normal avant configuration ou db:init », même
sur un projet configuré et migré. Seul avertissement, il laissait `doctor`
sortir en 0 : un contrôle de déploiement passait avec une base morte.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── 1. Un projet sans relation doit pouvoir construire son modèle ────────────

def test_build_model_tolere_l_absence_de_relations() -> None:
    from forge_mvc_entities.model import _validate_model_or_raise  # pyright: ignore[reportPrivateUsage]

    source = (PROJECT_ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities"
              / "model.py").read_text(encoding="utf-8")

    assert 'blocks.append(f"{relations_path}: fichier introuvable")' not in source, (
        "l'absence de relations.json vaut « aucune relation », pas une erreur"
    )
    assert _validate_model_or_raise is not None


def test_sync_relations_tolere_la_meme_absence() -> None:
    """Les deux commandes doivent s'accorder sur ce que veut dire l'absence."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities"
              / "model.py").read_text(encoding="utf-8")
    debut = source.index("def sync_relations(")
    corps = source[debut:source.index("\ndef ", debut + 1)]

    assert "if relations_path.exists():" in corps


def test_le_squelette_ne_livre_toujours_pas_relations_json() -> None:
    """Le contexte du correctif : rien ne crée ce fichier avant `make:relation`.

    Si un jour le squelette le livrait, la tolérance ci-dessus resterait juste
    mais cesserait d'être nécessaire ; ce test le signalerait.
    """
    trouves = list((PROJECT_ROOT / "skeleton").rglob("relations.json"))

    assert trouves == []


# ── 2. `db:config` écrit dans un projet, ou nulle part ──────────────────────

def test_db_config_refuse_hors_projet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from forge_mvc_entities.db_config import main

    (tmp_path / "env").mkdir()
    monkeypatch.chdir(tmp_path)

    code = main([])

    assert code == 1
    assert list((tmp_path / "env").iterdir()) == [], "aucun fichier ne doit être écrit"


def test_db_config_refuse_hors_projet_meme_en_retrait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--remove` touche les mêmes fichiers : même exigence."""
    from forge_mvc_entities.db_config import main

    monkeypatch.chdir(tmp_path)

    assert main(["--remove"]) == 1


# ── 3. `doctor` distingue « pas encore configuré » de « en panne » ──────────

def _env_dev(root: Path, **valeurs: str) -> None:
    (root / "env").mkdir(exist_ok=True)
    lignes = ["# Base de données"] + [f"{cle}={valeur}" for cle, valeur in valeurs.items()]
    (root / "env" / "dev").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def test_un_projet_aux_acces_renseignes_est_considere_configure(tmp_path: Path) -> None:
    from cli.project.doctor import _database_is_configured  # pyright: ignore[reportPrivateUsage]

    _env_dev(tmp_path, DB_NAME="mon_projet", DB_APP_LOGIN="mon_projet_app")

    assert _database_is_configured(tmp_path) is True


@pytest.mark.parametrize(
    "valeurs",
    [
        {"DB_NAME": "", "DB_APP_LOGIN": ""},
        {"DB_NAME": "mon_projet", "DB_APP_LOGIN": ""},
        {"DB_NAME": "", "DB_APP_LOGIN": "app"},
    ],
)
def test_des_acces_incomplets_ne_valent_pas_configuration(
    tmp_path: Path, valeurs: "dict[str, str]",
) -> None:
    """Tant que les clés sont vides, l'absence de connexion reste normale."""
    from cli.project.doctor import _database_is_configured  # pyright: ignore[reportPrivateUsage]

    _env_dev(tmp_path, **valeurs)

    assert _database_is_configured(tmp_path) is False


def test_sans_env_dev_le_projet_n_est_pas_configure(tmp_path: Path) -> None:
    from cli.project.doctor import _database_is_configured  # pyright: ignore[reportPrivateUsage]

    assert _database_is_configured(tmp_path) is False


def test_une_base_injoignable_sur_projet_configure_est_une_erreur() -> None:
    """Le point qui compte : `fail`, pas `warn`, sinon `doctor` sort en 0."""
    source = (PROJECT_ROOT / "cli" / "project" / "doctor.py").read_text(encoding="utf-8")
    debut = source.index("def check_db(root: Path")
    corps = source[debut:source.index("\ndef ", debut + 1)]

    assert "_database_is_configured(root)" in corps
    assert 'CheckResult("fail", "Base de données"' in corps


def test_le_message_de_panne_oriente_le_diagnostic() -> None:
    """« normal » ne doit plus s'afficher quand le projet est configuré."""
    source = (PROJECT_ROOT / "cli" / "project" / "doctor.py").read_text(encoding="utf-8")

    assert "alors que le projet " in source
    assert "serveur joignable ?" in source
