"""Les opt-ins n'écrivent pas d'horodatage conscient du fuseau (OPTIN-AWARE-TIMESTAMP-001).

Le ticket `TIMESTAMPS-NAIVE-UTC-001` a établi la règle, et son garde-fou
listait **quatre fichiers à la main**. Cette liste était le défaut : elle ne
couvrait que les écrivains connus au moment où elle a été écrite, et deux
opt-ins posaient la forme consciente sans que rien ne le signale.

    forge-mvc-iot    storage/events.py   received_at = datetime.now(UTC)
    forge-mvc-mail   log.py              created_at  = datetime.now(timezone.utc)

PostgreSQL convertit une valeur consciente vers l'heure locale du serveur.
Un événement IoT reçu à midi UTC était donc daté de 14 h dans une base où tout
le reste est en UTC, et le journal d'envoi de mails souffrait du même décalage.
Aucune erreur n'était levée : la valeur reste plausible, seulement fausse.

Ce fichier remplace la liste manuelle par un **relevé automatique**.

Le relevé a lui-même dû être élargi. Il ne retenait d'abord que les modules
contenant une instruction SQL, et a manqué `forge-mvc-mail/mailer.py`, qui
**fabrique** les horodatages que `log.py` **écrit**. Rien n'oblige le
producteur d'une valeur à être son écrivain, et c'est une limite structurelle
de tout critère fondé sur la présence de SQL.

La charge est donc inversée : tout le code de production est examiné, et un
module qui pose la forme consciente doit **prouver** qu'elle ne persiste pas,
en figurant dans `_NE_PERSISTENT_PAS` avec sa raison.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent.parent

#: Une instruction d'écriture suffit à classer un module comme écrivain.
_SQL_ECRITURE = re.compile(r"\b(INSERT INTO|UPDATE\s+\w|DELETE FROM)\b", re.IGNORECASE)

#: Ces modules posent la forme consciente sans qu'elle atteigne jamais une
#: colonne : comparaison en mémoire, valeur rendue à l'application qui la
#: persiste elle-même (ADR-008), ou horodatage d'affichage. Chaque entrée porte
#: sa raison, pour qu'une relecture puisse la contester plutôt que de buter sur
#: un silence.
_NE_PERSISTENT_PAS = {
    "core/auth/email.py": "jeton de vérification, rendu à l'application (ADR-008)",
    "core/auth/rate_limit.py": "fenêtre glissante en mémoire, rien n'est écrit",
    "core/auth/reset.py": "expiration rendue à l'application, qui la persiste",
    "core/auth/tokens.py": "expiration rendue à l'application, qui la persiste",
    "core/errors/runtime_error_markdown.py": "horodatage d'un rapport Markdown",
    "core/errors/runtime_errors.py": "horodatage d'un événement JSONL, pas d'une colonne",
    "packages/forge-mvc-iot/forge_mvc_iot/cli/simulate.py": "relevé simulé, envoyé par MQTT",
    "packages/forge-mvc-mail/forge_mvc_mail/cli.py": "horodatage d'un affichage CLI",
    "packages/forge-mvc-mail/forge_mvc_mail/transports.py": "en-tête `Date` d'un message",
    "packages/forge-mvc-mfa/forge_mvc_mfa/mfa.py": "facteurs rendus à l'application, qui les persiste",
    "packages/forge-mvc-mfa/forge_mvc_mfa/recovery.py": "codes rendus à l'application, qui les persiste",
}

#: Ces modules rendent une chaîne via `strftime` : le pilote ne peut rien
#: convertir, et la forme consciente y est sans effet.
_RENDENT_UNE_CHAINE = {
    # Les bornes de rétention d'audit et de stats ne figurent plus ici : leur
    # calcul vit dans `core.database.retention`, qui emploie `utc_now()`
    # (IOT-RETENTION-GC-001). L'exemption a disparu avec sa cause.
    "packages/forge-mvc-sessions-db/forge_mvc_sessions_db/store.py": "expiration formatée en chaîne",
    "packages/forge-mvc-entities/forge_mvc_entities/migrations.py": "horodatage de nom de fichier de migration",
}


def _ecrit_en_base(arbre: ast.Module) -> bool:
    for noeud in ast.walk(arbre):
        if (
            isinstance(noeud, ast.Constant)
            and isinstance(noeud.value, str)
            and _SQL_ECRITURE.search(noeud.value)
        ):
            return True
    return False


def _est_rendu_naif(appel: ast.Call, arbre: ast.Module) -> bool:
    """Vrai si `datetime.now(...)` est immédiatement suivi de `.replace(tzinfo=None)`."""
    for noeud in ast.walk(arbre):
        if (
            isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and noeud.func.attr == "replace"
            and noeud.func.value is appel
        ):
            return any(
                mot.arg == "tzinfo" and isinstance(mot.value, ast.Constant) and mot.value.value is None
                for mot in noeud.keywords
            )
    return False


def _ecrivains() -> list[tuple[str, ast.Module]]:
    """Tout module du code de production, qu'il porte du SQL ou non.

    Le relevé ne retenait d'abord que les modules contenant une instruction
    d'écriture. Il a manqué `forge-mvc-mail/mailer.py`, qui **fabrique** les
    horodatages que `log.py` **écrit** : la valeur naît dans un module sans
    SQL et se persiste dans un autre.

    C'est la limite de tout critère fondé sur la présence de SQL, et elle est
    structurelle : rien n'oblige le producteur d'une valeur à être son
    écrivain. Le relevé porte donc sur tout le code, et la charge est inversée.
    Un module qui pose la forme consciente doit désormais **prouver** qu'elle
    ne persiste pas, en figurant dans `_NE_PERSISTENT_PAS` avec sa raison.
    """
    trouves: list[tuple[str, ast.Module]] = []
    for chemin in sorted(RACINE.rglob("*.py")):
        rel = chemin.relative_to(RACINE).as_posix()
        if not rel.startswith(("core/", "cli/", "packages/")):
            continue
        if "test" in rel or "/build/" in rel:
            continue
        try:
            arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        trouves.append((rel, arbre))
    return trouves


def test_le_releve_trouve_bien_des_ecrivains() -> None:
    """Un relevé automatique qui ne relève rien passerait toujours.

    C'est le mode de défaillance propre aux garde-fous par balayage : un motif
    trop étroit rend une liste vide, et la liste vide se lit comme un succès.
    """
    ecrivains = _ecrivains()

    assert len(ecrivains) >= 15, (
        f"seulement {len(ecrivains)} écrivains détectés : le motif de détection "
        "s'est resserré, et le garde-fou ne garde plus grand-chose"
    )


def test_aucun_opt_in_ne_pose_la_forme_consciente() -> None:
    """La règle de l'ADR-081, tenue sur tout le dépôt et non sur une liste."""
    fautes: list[str] = []

    for rel, arbre in _ecrivains():
        if rel in _RENDENT_UNE_CHAINE or rel in _NE_PERSISTENT_PAS:
            continue
        for noeud in ast.walk(arbre):
            if (
                isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == "now"
                and isinstance(noeud.func.value, ast.Name)
                and noeud.func.value.id == "datetime"
                and not _est_rendu_naif(noeud, arbre)
            ):
                fautes.append(f"{rel}:{noeud.lineno}")

    assert not fautes, (
        "Ces modules écrivent en base et posent `datetime.now(...)` sans le "
        "rendre naïf. PostgreSQL convertira la valeur vers l'heure locale du "
        "serveur, et la base portera deux référentiels horaires.\n"
        "  Employez `core.database.timestamps.utc_now()`.\n  "
        + "\n  ".join(fautes)
    )


def test_les_exemptions_sont_toujours_justifiees() -> None:
    """Une exemption qui survit à son motif est une porte laissée ouverte.

    Si un module exempté cesse de formater en chaîne, il redevient un écrivain
    ordinaire et l'exemption doit tomber avec son motif.
    """
    perimees: list[str] = []

    for rel in _NE_PERSISTENT_PAS:
        chemin = RACINE / rel
        if not chemin.exists():
            perimees.append(f"{rel} (le fichier n'existe plus)")
            continue
        if "datetime.now" not in chemin.read_text(encoding="utf-8"):
            perimees.append(f"{rel} (ne pose plus la forme consciente)")

    for rel in _RENDENT_UNE_CHAINE:
        chemin = RACINE / rel
        if not chemin.exists():
            perimees.append(f"{rel} (le fichier n'existe plus)")
            continue
        if "strftime" not in chemin.read_text(encoding="utf-8"):
            perimees.append(f"{rel} (ne formate plus en chaîne)")

    assert not perimees, (
        "Ces exemptions ne reposent plus sur leur motif :\n  " + "\n  ".join(perimees)
    )


def test_l_exemption_timestamps_ne_peut_pas_s_elargir() -> None:
    """`core.database.timestamps` ne doit jamais dépendre que de la bibliothèque standard.

    Deux garde-fous d'architecture interdisent à `forge-mvc-iot` d'importer
    quoi que ce soit de `core.database`, afin que son module de sérialisation
    reste sans couplage à la base. Ils écartent ce seul module, au motif qu'il
    n'importe rien d'autre que `datetime`.

    Ce test est la contrepartie de l'exemption. Sans lui, il suffirait d'ajouter
    un import au module d'horodatage pour faire entrer un connecteur par une
    porte que personne ne surveille plus.
    """
    module = RACINE / "core" / "database" / "timestamps.py"
    arbre = ast.parse(module.read_text(encoding="utf-8"))

    importes: list[str] = []
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            importes.extend(alias.name for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            importes.append(noeud.module)

    externes = [nom for nom in importes if nom.split(".")[0] not in {"datetime", "__future__"}]

    assert not externes, (
        "`core.database.timestamps` a gagné des dépendances, alors que deux "
        "garde-fous l'exemptent au motif qu'il n'en a aucune :\n  "
        + "\n  ".join(externes)
    )


@pytest.mark.db
def test_l_horodatage_iot_traverse_le_moteur_sans_decalage(real_backend_db: str) -> None:
    """La vérification là où elle se joue : contre le serveur, pas sur la forme du code."""
    pytest.importorskip("forge_mvc_iot")

    from datetime import datetime, timezone

    from forge_mvc_iot.mqtt.contract import Measurement
    from forge_mvc_iot.storage.events import (
        INSERT_IOT_EVENT_SQL,
        build_insert_iot_event_sql,
    )
    from forge_mvc_iot.tables import IOT_EVENTS

    from forge_mvc_testing.real_db import tables_temporaires

    with tables_temporaires(IOT_EVENTS) as db:
        mesure = Measurement(
            site="atelier",
            device_id="sonde-1",
            kind="temperature",
            value=21.5,
            unit="C",
            timestamp="2026-08-13T12:00:00Z",
            metadata=None,
        )
        sql, params = build_insert_iot_event_sql(mesure)
        assert sql == INSERT_IOT_EVENT_SQL
        db.execute(sql, params)

        ligne = db.fetch_one('SELECT received_at AS "received_at" FROM iot_events', ())
        assert ligne is not None
        lu = ligne["received_at"]
        if isinstance(lu, str):
            lu = datetime.fromisoformat(lu)
        ecart = abs((lu - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())

        assert ecart < 120, (
            f"`received_at` s'écarte de {ecart:.0f} s de l'UTC : le pilote a "
            "converti la valeur, et l'événement est daté dans un autre référentiel"
        )
