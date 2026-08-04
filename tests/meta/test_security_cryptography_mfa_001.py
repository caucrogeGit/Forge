"""Garde-fou SECURITY-CRYPTOGRAPHY-MFA-001.

Verrouille le plancher `cryptography>=50.0.0` du paquet opt-in MFA,
**l'absence de borne haute**, et l'absence de `cryptography` dans les
dépendances runtime du cœur.

## Historique des bornes

- `>=42,<46` : audit post-publication 1.0.0-beta.8, des CVE corrigées en 46.0.7.
- `>=46.0.7,<47` : suite du même audit, plafonné sous un major non éprouvé.
- `>=48.0.1,<49` : `GHSA-537c-gmf6-5ccf`, OpenSSL lié statiquement dans les
  wheels antérieures à 48.0.1.
- `>=50.0.0,<51` : trois avis du 2026-08-04 sur la 48.0.1
  (`DEPS-CRYPTOGRAPHY-50-001`).
- `>=50.0.0`, sans plafond (`DEPS-CRYPTOGRAPHY-NO-CEILING-001`), ci-dessous.

Les trois avis du 2026-08-04 : `CVE-2026-69248` laisse une CA intermédiaire
limitée à `foo.example.com` accepter une feuille portant le joker
`*.example.com` ; `CVE-2026-69249` provoque une explosion exponentielle sur une
chaîne invalide contenant des copies d'un même certificat auto-signé ;
`CVE-2026-69247` est un oracle de déchiffrement PKCS#7, qui révélait la longueur
récupérée de l'opération RSA. Les deux premiers sont corrigés en 49.0.0, le
troisième en 50.0.0 seulement, d'où le plancher.

## Pourquoi cette dépendance n'a plus de plafond

Quatre changements de borne, aucun motivé par une rupture d'API. Les quatre
venaient d'un avis de sécurité, sur des majors 42 à 50. Le plafond n'a jamais
servi à ce pour quoi il existait.

Il nuisait, en revanche, de trois façons.

**Il interdit le correctif au moment où il paraît.** `cryptography` livre ses
correctifs de sécurité dans une nouvelle majeure, pas dans un patch de la
précédente. Un plafond `<majeure+1` exclut donc le correctif par construction.
Mesuré : le plafond `<49` a été posé le 2026-06-24, alors que la 49.0.0 était
sortie douze jours plus tôt. La borne naissait périmée.

**Il transfère la fenêtre de vulnérabilité vers Forge.** Tant que le plafond
tient, un utilisateur de `forge-mvc-mfa` ne peut pas prendre le correctif amont,
même en le voulant. Il attend une release de Forge. Sur une bibliothèque de
sécurité, c'est le contraire du but recherché.

**Il contamine les applications.** `forge-mvc-mfa` est une bibliothèque. Une
application qui aurait besoin d'une majeure plus récente, pour une tout autre
dépendance, verrait sa résolution échouer sans recours. Plafonner est légitime
dans une application, qui décide pour elle-même ; dans une bibliothèque, on
décide pour des tiers.

## Ce qui remplace le plafond

Le plafond ne protégeait réellement que d'une rupture d'API dans Fernet, le seul
usage de Forge. Ce risque est tenu par des tests, pas par une borne :
`tests/test_mfa_secret_crypto.py` porte un aller-retour chiffrement puis
déchiffrement réel, qui rougirait sur une rupture.

L'abandon d'un vieux Python par une majeure, lui, est déjà géré par la
métadonnée `requires-python` : pip n'installe pas une version qui ne supporte
pas l'interpréteur du projet. Le plafond n'y était pour rien.

Enfin la détection existe : l'audit hebdomadaire
(`.github/workflows/dependency-audit.yml`) a relevé ces trois avis en moins de
vingt-quatre heures.

## Portée de la décision

Elle ne vise que `cryptography`, seule dépendance sans plafond de
`requirements-audit.txt`. Le raisonnement vaut surtout pour une bibliothèque de
sécurité, dont les correctifs sont fréquents et urgents. L'étendre aux autres
dépendances serait une décision distincte, à prendre sur ses propres mesures.

Le cœur ne doit jamais embarquer `cryptography` : Fernet n'est utilisé que côté
MFA. Si une future modification ajoute la dépendance au cœur, ce test échoue
immédiatement.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
MFA_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"

#: Plancher exigé : sous cette version, `CVE-2026-69247` (oracle PKCS#7) n'est
#: pas corrigé. Sans borne haute, pour les motifs écrits en tête de fichier.
REQUIRED_CONSTRAINT = "cryptography>=50.0.0"

#: Le fichier d'audit doit déclarer la même contrainte que le paquet.
SURFACE_AUDITEE = PROJECT_ROOT / "requirements-audit.txt"


def _project_dependencies(pyproject_path: Path) -> list[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("dependencies", [])


def _optional_dependencies(pyproject_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


class TestMfaCryptographyConstraint:
    def test_mfa_pins_cryptography_secure_range(self):
        deps = _project_dependencies(MFA_PYPROJECT)
        assert REQUIRED_CONSTRAINT in deps, (
            f"forge-mvc-mfa doit déclarer `{REQUIRED_CONSTRAINT}` "
            f"(CVE-2026-69247 sur PKCS#7, corrigé en 50.0.0 seulement). "
            f"Dépendances trouvées : {deps}"
        )

    def test_mfa_ne_replafonne_pas_cryptography(self):
        """Le cœur de la décision, et ce qu'un futur réflexe rétablirait.

        Reposer un plafond interdirait de nouveau le correctif amont au moment
        même de sa parution, et casserait la résolution de toute application
        ayant besoin d'une majeure plus récente.
        """
        contrainte = next(
            d for d in _project_dependencies(MFA_PYPROJECT)
            if d.lower().startswith("cryptography"))

        assert "<" not in contrainte, (
            f"`{contrainte}` replafonne cryptography. Les correctifs de sécurité "
            f"de cette bibliothèque paraissent dans une NOUVELLE majeure : un "
            f"plafond les exclut par construction, et `forge-mvc-mfa` étant une "
            f"bibliothèque, il contamine la résolution des applications. "
            f"Motifs complets en tête de ce fichier.")

    def test_la_surface_auditee_declare_la_meme_contrainte(self):
        """Une divergence ferait auditer autre chose que ce qui est expédié."""
        lignes = [ligne.strip() for ligne
                  in SURFACE_AUDITEE.read_text(encoding="utf-8").splitlines()
                  if ligne.strip().lower().startswith("cryptography")]

        assert lignes == [REQUIRED_CONSTRAINT], (
            f"requirements-audit.txt déclare {lignes}, le paquet déclare "
            f"`{REQUIRED_CONSTRAINT}`")

    def test_le_motif_de_l_absence_de_plafond_est_ecrit(self):
        """Une décision inhabituelle sans motif écrit se fait annuler par réflexe."""
        entete = Path(__file__).read_text(encoding="utf-8").split('"""')[1]

        assert "n'a plus de plafond" in entete
        assert "bibliothèque" in entete
        assert "requires-python" in entete


class TestCoreDoesNotShipCryptography:
    def test_core_runtime_excludes_cryptography(self):
        deps = _project_dependencies(ROOT_PYPROJECT)
        offenders = [d for d in deps if d.lower().startswith("cryptography")]
        assert not offenders, (
            "Le core forge-mvc ne doit pas dépendre de `cryptography` — "
            "Fernet est réservé à forge-mvc-mfa (opt-in). "
            f"Trouvé : {offenders}"
        )

    def test_core_extras_exclude_cryptography(self):
        extras = _optional_dependencies(ROOT_PYPROJECT)
        offenders: dict[str, list[str]] = {}
        for name, items in extras.items():
            hits = [d for d in items if d.lower().startswith("cryptography")]
            if hits:
                offenders[name] = hits
        assert not offenders, (
            "Les extras du core ne doivent pas tirer `cryptography` "
            "directement — il vient via forge-mvc-mfa quand l'utilisateur "
            f"installe explicitement le module. Trouvé : {offenders}"
        )
