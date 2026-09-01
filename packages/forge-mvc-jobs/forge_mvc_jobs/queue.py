# pyright: strict
"""File de tâches de fond adossée à MariaDB, sans broker ni runtime async.

`forge-mvc-jobs` permet de déporter un travail lourd hors de la requête HTTP
(envoi d'emails en nombre, transcodage, génération de QR Codes, import massif).
Le modèle est volontairement simple et fidèle à Forge :

- une table `jobs` sert de file (le SQL reste visible) ;
- on **enfile** une tâche avec :func:`enqueue` (par exemple depuis un contrôleur) ;
- un **process worker séparé** la traite avec :func:`drain` ou :func:`run_worker`,
  en appelant un gestionnaire que l'application a explicitement enregistré.

Aucune dépendance lourde (pas de Celery ni de Redis), aucune boucle async : le
serveur web reste synchrone (WSGI). La réservation d'une tâche est atomique : on
choisit une candidate, puis on la réserve sous garde `status='pending'`, donc
plusieurs workers peuvent tourner sans se marcher dessus.

## Reprise après plantage d'un worker

Un worker qui meurt en cours de traitement laisse sa tâche au statut `running`,
jeton posé, et personne ne la reprendrait jamais. :func:`reclaim_stale` remet en
file les tâches dont la réservation a dépassé un **bail**, et marque en échec
celles qui ont épuisé leurs tentatives. `forge jobs:reclaim` est le point
d'entrée à brancher sur un ordonnanceur externe, Forge n'en fournissant pas.

Deux limites à connaître, écrites plutôt que découvertes.

Le bail est une durée fixe. Une tâche légitimement plus longue que lui sera
reprise alors qu'elle tourne encore, donc exécutée deux fois. Réglez le bail
au-dessus de votre tâche la plus longue, et écrivez des gestionnaires
**idempotents** : la reprise ne garantit pas l'exécution unique, elle garantit
qu'aucune tâche ne reste bloquée.

Le worker ne prolonge pas son bail pendant qu'il travaille, ce qui lèverait la
limite précédente. C'est hors périmètre pour l'instant.

La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from forge_mvc_jobs.errors import JobError

#: Nom de la table de file.
TABLE_NAME = "jobs"

#: Un gestionnaire de tâche : reçoit la charge utile (dict) désérialisée.
JobHandler = Callable[[dict[str, Any]], object]


def _dialect() -> Any:
    """Dialecte du backend actif, source des expressions non portables."""
    from core.database.backend import get_backend

    return get_backend().dialect


def _now() -> str:
    """Expression de l'instant courant, propre au backend (OPTIN-DML-DIALECT-001).

    `NOW()` était écrit en dur : mesuré, SQL Server et SQLite ne le connaissent
    pas, et la file de tâches y était inutilisable malgré une DDL déjà
    dialectale.
    """
    return _dialect().now_expression()


def _insert_sql() -> str:
    maintenant = _now()
    return (
        f"INSERT INTO {TABLE_NAME} "
        "(queue, task, payload, max_attempts, priority, idempotency_key, available_at) "
        f"VALUES (?, ?, ?, ?, ?, ?, {_dialect().interval_seconds_expression(maintenant)})"
    )


def _candidate_sql() -> str:
    """Prochaine tâche prête de la file, la plus ancienne d'abord.

    La réservation se fait ensuite en deux temps plutôt qu'en un
    `UPDATE ... ORDER BY ... LIMIT 1`, extension que seul MariaDB accepte. On
    choisit une candidate, puis on la réserve sous garde `status='pending'` :
    deux ouvriers qui visent la même ligne ne peuvent pas gagner tous les deux,
    le second voyant `rowcount` à zéro. Le motif n'ajoute rien au contrat, il
    réemploie `limit_clause()`, déjà dialectale.
    """
    return (
        f"SELECT id FROM {TABLE_NAME} "
        f"WHERE queue=? AND status='pending' AND available_at <= {_now()} "
        f"ORDER BY priority DESC, id {_dialect().limit_clause()}"
    )


def _claim_sql() -> str:
    return (
        f"UPDATE {TABLE_NAME} SET status='running', claim_token=?, "
        f"started_at={_now()}, attempts=attempts+1 "
        "WHERE id=? AND status='pending'"
    )


_SELECT_CLAIMED_SQL = (
    f"SELECT id, task, payload, attempts, max_attempts FROM {TABLE_NAME} "
    "WHERE claim_token=? AND status='running'"
)


def _done_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET status='done', finished_at={_now()}, "
            "claim_token=NULL WHERE id=?")


def _fail_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET status='failed', last_error=?, "
            f"finished_at={_now()}, claim_token=NULL WHERE id=?")


_SELECT_BY_IDEMPOTENCY_SQL = (
    f"SELECT id FROM {TABLE_NAME} WHERE idempotency_key = ?"
)


def _heartbeat_sql() -> str:
    """Repousse le bail d'une tâche en cours, sans changer son statut.

    `started_at` est ce que `reclaim_stale` compare au bail : le repousser
    revient à dire « je travaille encore ». La garde sur `claim_token` fait que
    seul l'ouvrier qui détient la tâche peut la prolonger, sans quoi n'importe
    qui pourrait retenir une tâche qu'il ne traite pas.
    """
    return (
        f"UPDATE {TABLE_NAME} SET started_at={_now()} "
        "WHERE claim_token=? AND status='running'"
    )


def _retry_sql() -> str:
    """Remise en file d'une tâche qui a échoué, après un délai croissant.

    Le délai part en secondes **positives** dans
    `interval_seconds_expression()`, seul régime que les quatre backends
    acceptent. Mesuré, le dialecte SQLite compose son modificateur par
    concaténation (`'+' || ? || ' seconds'`) et rend `NULL` pour une valeur
    négative, ce qui ferait taire toute comparaison l'employant.
    """
    return (f"UPDATE {TABLE_NAME} SET status='pending', claim_token=NULL, "
            f"started_at=NULL, available_at={_dialect().interval_seconds_expression(_now())} "
            "WHERE id=?")


#: Priorités nommées (JOBS-PRIORITY-001).
#:
#: Un entier, et non une énumération fermée : le défaut 0 rend « normales » les
#: tâches déjà en file sans migration de données, et une application peut
#: nuancer entre deux niveaux sans que Forge ait à trancher pour elle.
#:
#: Plus grand vaut plus prioritaire, et l'ancienneté départage à égalité : sans
#: ce second critère, deux tâches de même priorité se prendraient dans un ordre
#: que rien ne garantit.
PRIORITY_LOW = -10
PRIORITY_NORMAL = 0
PRIORITY_HIGH = 10

#: Délai de base du réessai, en secondes.
BACKOFF_BASE_SECONDS = 10
#: Plafond du délai de réessai, en secondes.
BACKOFF_CAP_SECONDS = 600


def backoff_seconds(attempts: int) -> int:
    """Délai avant le réessai suivant, après `attempts` tentatives consommées.

    Doublement à chaque tentative, plafonné : 10, 20, 40, 80, 160, 320, puis
    600 secondes. Formule écrite et bornée plutôt que devinée (principe 3).
    Sans elle, une tâche qui échoue vite était remise en file aussitôt et
    consommait toutes ses tentatives en une fraction de seconde, ce qui ne
    laissait aucune chance à une panne passagère de se résorber.
    """
    if attempts < 1:
        return 0
    return min(BACKOFF_BASE_SECONDS * (2 ** (attempts - 1)), BACKOFF_CAP_SECONDS)


#: Bail par défaut d'une réservation, en secondes.
DEFAULT_LEASE_SECONDS = 900


def _stale_predicate() -> str:
    """Tâches réservées dont le bail a expiré.

    L'inégalité est écrite `started_at + bail < maintenant` et non
    `started_at < maintenant - bail`. Les deux sont équivalentes en
    mathématiques, pas en SQL portable : la seconde forme exigerait un
    intervalle **négatif**, que le dialecte SQLite rend `NULL`. La comparaison
    serait alors fausse partout, et la reprise ne ferait rien du tout sans
    lever la moindre erreur.

    Les deux bornes restent côté serveur, donc aucune horloge applicative
    n'entre dans la décision.
    """
    return (
        f"queue=? AND status='running' AND started_at IS NOT NULL "
        f"AND {_dialect().interval_seconds_expression('started_at')} < {_now()}"
    )


def _reclaim_requeue_sql() -> str:
    return (
        f"UPDATE {TABLE_NAME} SET status='pending', claim_token=NULL, started_at=NULL, "
        f"available_at={_dialect().interval_seconds_expression(_now())} "
        f"WHERE {_stale_predicate()} AND attempts < max_attempts"
    )


def _reclaim_fail_sql() -> str:
    return (
        f"UPDATE {TABLE_NAME} SET status='failed', last_error=?, finished_at={_now()}, "
        f"claim_token=NULL WHERE {_stale_predicate()} AND attempts >= max_attempts"
    )


#: Message porté par une tâche abandonnée faute de tentatives restantes.
#: Distinct d'une exception du gestionnaire : le diagnostic n'est pas le même.
RECLAIM_FAILURE_MESSAGE = (
    "tâche reprise après expiration du bail de réservation, "
    "tentatives épuisées (le worker n'a jamais rendu de verdict)"
)
_PENDING_COUNT_SQL = f"SELECT COUNT(*) AS n FROM {TABLE_NAME} WHERE queue=? AND status='pending'"
#: Lecture d'une tâche par son identifiant.
#: Sans `LIMIT 1` : la clause porte sur la **clé primaire**, donc au plus une
#: ligne correspond. Le `LIMIT` n'apportait rien et rendait `get_job()`
#: inutilisable sur SQL Server, qui ne le connaît pas
#: (`ADMIN-JOBS-LIMIT-PORTABLE-001`).
_SELECT_JOB_SQL = (
    f"SELECT id, queue, task, status, attempts, max_attempts, last_error FROM {TABLE_NAME} WHERE id=?"
)


@dataclass(frozen=True)
class Job:
    """État d'une tâche, pour inspection."""

    id: int
    queue: str
    task: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def enqueue(
    task: str,
    payload: dict[str, Any] | None = None,
    *,
    queue: str = "default",
    max_attempts: int = 1,
    available_in: int = 0,
    priority: int = PRIORITY_NORMAL,
    idempotency_key: "str | None" = None,
    db: Any = None,
) -> int:
    """Enfile une tâche `task` avec sa charge utile et renvoie son identifiant.

    `payload` est sérialisé en JSON. `max_attempts` borne les tentatives (une
    tâche qui échoue est re-mise en file tant que `attempts < max_attempts`).
    `available_in` retarde la disponibilité de N secondes (0 = immédiat).

    `priority` décide de l'ordre de prise en compte, le plus grand d'abord, et
    l'ancienneté départage à égalité (`PRIORITY_LOW`, `PRIORITY_NORMAL`,
    `PRIORITY_HIGH`). Une priorité ne fait passer personne devant une tâche
    déjà réservée : elle ordonne la file, elle n'interrompt rien.

    `idempotency_key` empêche le doublon : deux mises en file de la même clé ne
    donnent qu'une tâche, et la seconde rend l'identifiant de la première. Un
    utilisateur qui double-clique, un webhook rejoué, une requête relancée après
    un délai d'attente : autant de cas où la tâche partait deux fois
    (`JOBS-IDEMPOTENCY-KEY-001`).

    Lève :class:`JobError` si `task` est vide, `max_attempts < 1`, si
    `priority` n'est pas un entier, ou si `payload` n'est pas sérialisable en
    JSON.
    """
    if not task or not task.strip():
        raise JobError("Le nom de tâche ne peut pas être vide.")
    if max_attempts < 1:
        raise JobError(f"max_attempts doit être >= 1. Reçu : {max_attempts}.")
    if not isinstance(priority, int) or isinstance(priority, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise JobError(f"priority doit être un entier. Reçu : {priority!r}.")
    try:
        payload_json = json.dumps(payload or {})
    except (TypeError, ValueError) as exc:
        raise JobError(f"Charge utile non sérialisable en JSON : {exc}") from exc
    cle = (idempotency_key or "").strip() or None
    database = db if db is not None else _db_module()

    if cle is not None:
        # La contrainte d'unicité ferme la course : deux appels simultanés ne
        # peuvent pas insérer tous les deux, et le perdant relit la ligne
        # gagnante. Vérifier d'abord évite l'exception dans le cas courant.
        existante = database.fetch_one(_SELECT_BY_IDEMPOTENCY_SQL, (cle,))
        if existante:
            return int(existante["id"])

    try:
        return database.insert(
            _insert_sql(),
            (queue, task, payload_json, max_attempts, priority, cle, available_in),
        )
    except Exception:
        if cle is None:
            raise
        existante = database.fetch_one(_SELECT_BY_IDEMPOTENCY_SQL, (cle,))
        if existante:
            return int(existante["id"])
        raise


def process_one(handlers: Mapping[str, JobHandler], *, queue: str = "default", db: Any = None) -> bool:
    """Réserve et exécute une tâche disponible de `queue`. Renvoie `True` si une
    tâche a été traitée, `False` si la file est vide.

    En cas d'échec du gestionnaire, la tâche est re-mise en file si
    `attempts < max_attempts`, sinon marquée `failed`. Une tâche sans
    gestionnaire enregistré est marquée `failed`.
    """
    database = db if db is not None else _db_module()
    token = uuid4().hex
    candidate = database.fetch_one(_candidate_sql(), (queue, 1))
    if candidate is None:
        return False
    if not database.execute(_claim_sql(), (token, int(candidate["id"]))):
        # Un autre ouvrier a réservé cette ligne entre-temps : ce n'est pas une
        # file vide, mais on rend la main plutôt que de boucler ici.
        return False
    row = database.fetch_one(_SELECT_CLAIMED_SQL, (token,))
    if row is None:
        return False

    job_id = int(row["id"])
    task = str(row["task"])
    attempts = int(row["attempts"])
    max_attempts = int(row["max_attempts"])
    payload: dict[str, Any] = json.loads(row["payload"])

    handler = handlers.get(task)
    if handler is None:
        database.execute(_fail_sql(), (f"tâche inconnue : {task}", job_id))
        return True

    try:
        handler(payload)
    except Exception as exc:  # noqa: BLE001 — toute erreur du gestionnaire est rapportée
        if attempts < max_attempts:
            database.execute(_retry_sql(), (backoff_seconds(attempts), job_id))
        else:
            database.execute(_fail_sql(), (str(exc), job_id))
        return True

    database.execute(_done_sql(), (job_id,))
    return True


def drain(
    handlers: Mapping[str, JobHandler],
    *,
    queue: str = "default",
    max_jobs: int | None = None,
    db: Any = None,
) -> int:
    """Traite les tâches disponibles de `queue` jusqu'à épuisement (ou `max_jobs`).

    Renvoie le nombre de tâches traitées. C'est une passe unique : pas d'attente.
    """
    processed = 0
    while max_jobs is None or processed < max_jobs:
        if not process_one(handlers, queue=queue, db=db):
            break
        processed += 1
    return processed


def run_worker(
    handlers: Mapping[str, JobHandler],
    *,
    queue: str = "default",
    poll_interval: float = 1.0,
    db: Any = None,
    stop: Callable[[], bool] | None = None,
) -> None:
    """Boucle de worker : vide la file, puis attend `poll_interval` si vide.

    L'application lance cette fonction depuis son propre point d'entrée (un
    script worker), en fournissant ses gestionnaires : le worker est donc une
    commande explicite, jamais déclenchée par la requête HTTP. `stop` est une
    condition d'arrêt optionnelle vérifiée à chaque cycle.
    """
    while True:
        if stop is not None and stop():
            return
        processed = drain(handlers, queue=queue, db=db)
        if processed == 0:
            time.sleep(poll_interval)


@dataclass(frozen=True)
class ReclaimResult:
    """Effet d'une passe de reprise.

    `requeued` compte les tâches remises en file, `failed` celles abandonnées
    faute de tentatives restantes. Les deux ensembles sont disjoints.
    """

    requeued: int
    failed: int

    @property
    def total(self) -> int:
        return self.requeued + self.failed


def reclaim_stale(
    *,
    queue: str = "default",
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db: Any = None,
) -> ReclaimResult:
    """Reprend les tâches dont la réservation a dépassé `lease_seconds`.

    Une tâche qui a encore des tentatives repart en file, après le délai
    croissant habituel. Une tâche qui les a épuisées est marquée `failed` avec
    :data:`RECLAIM_FAILURE_MESSAGE`, distinct du message d'une exception : un
    worker tué n'a pas rendu de verdict, et confondre les deux ferait chercher
    un bogue applicatif là où il y a eu une panne de processus.

    Ne fait rien tant que le bail n'est pas dépassé, donc peut être appelée
    aussi souvent que voulu. Lève :class:`JobError` si `lease_seconds` est
    inférieur à 1 : un bail nul reprendrait des tâches en cours d'exécution.
    """
    if lease_seconds < 1:
        raise JobError(
            f"lease_seconds doit être >= 1. Reçu : {lease_seconds}. "
            "Un bail nul reprendrait des tâches en cours d'exécution."
        )
    database = db if db is not None else _db_module()

    requeued = int(
        database.execute(
            _reclaim_requeue_sql(),
            (backoff_seconds(1), queue, lease_seconds),
        )
    )
    failed = int(
        database.execute(
            _reclaim_fail_sql(),
            (RECLAIM_FAILURE_MESSAGE, queue, lease_seconds),
        )
    )
    return ReclaimResult(requeued=requeued, failed=failed)


def heartbeat(claim_token: str, *, db: Any = None) -> bool:
    """Prolonge le bail d'une tâche en cours. Vrai si elle a été prolongée.

    Une tâche longue dépassait son bail et se faisait reprendre par
    `reclaim_stale`, donc **exécutée une seconde fois** pendant que la première
    tournait encore. Le remède était d'allonger le bail pour tout le monde, au
    prix d'une reprise tardive des vraies pannes (`JOBS-HEARTBEAT-001`).

    Un traitement long appelle `heartbeat` régulièrement, avec le jeton que
    `process_one` lui a attribué : le bail se recale, et une tâche vraiment
    abandonnée reste reprise vite.

    Rend `False` quand le jeton ne désigne aucune tâche en cours, ce qui arrive
    si elle a déjà été reprise. C'est une information utile à l'appelant : son
    travail est peut être en train d'être refait ailleurs.
    """
    if not claim_token or not claim_token.strip():
        return False
    database = db if db is not None else _db_module()
    return int(database.execute(_heartbeat_sql(), (claim_token,))) >= 1


def pending_count(*, queue: str = "default", db: Any = None) -> int:
    """Nombre de tâches en attente dans `queue`."""
    row = (db if db is not None else _db_module()).fetch_one(_PENDING_COUNT_SQL, (queue,))
    return int(row["n"]) if row else 0


#: Statuts qu'une tâche peut porter, dans l'ordre où ils comptent pour qui
#: surveille : ce qui reste à faire d'abord, ce qui est fini ensuite.
JOB_STATUSES = ("pending", "running", "failed", "done")


@dataclass(frozen=True)
class QueueStatus:
    """État d'une file, tel que `forge jobs:status` le rend.

    `ready` compte les tâches en attente **et disponibles maintenant**.
    `pending` inclut les tâches différées par `available_in` ou par un réessai :
    une file de cent tâches toutes différées n'a rien à faire, et confondre les
    deux ferait chercher un ouvrier en panne là où tout se déroule normalement.
    """

    queue: str
    counts: dict[str, int]
    ready: int

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _status_counts_sql(par_file: bool) -> str:
    filtre = "WHERE queue=? " if par_file else ""
    return (
        f"SELECT queue, status, COUNT(*) AS n FROM {TABLE_NAME} "
        f"{filtre}GROUP BY queue, status"
    )


def _ready_counts_sql(par_file: bool) -> str:
    """Tâches en attente et disponibles maintenant, par file.

    La borne temporelle vient du dialecte, jamais d'un `NOW()` écrit en dur :
    l'audit `OPTIN-DML-DIALECT-001` a mesuré que ce raccourci rendait la DML
    inutilisable ailleurs que sur MariaDB.
    """
    filtre = "AND queue=? " if par_file else ""
    return (
        f"SELECT queue, COUNT(*) AS n FROM {TABLE_NAME} "
        f"WHERE status='pending' AND available_at <= {_now()} {filtre}"
        "GROUP BY queue"
    )


def status_counts(*, queue: "str | None" = None, db: Any = None) -> list[QueueStatus]:
    """État des files, triées par nom. Toutes les files si `queue` est absente.

    Une file sans aucune tâche n'apparaît pas : elle n'existe que par ses
    lignes, et en inventer une vide supposerait de connaître les files que
    l'application compte utiliser.
    """
    database = db if db is not None else _db_module()
    par_file = queue is not None
    params: tuple[Any, ...] = (queue,) if par_file else ()

    par_nom: dict[str, dict[str, int]] = {}
    for ligne in database.fetch_all(_status_counts_sql(par_file), params):
        nom = str(ligne["queue"])
        par_nom.setdefault(nom, {})[str(ligne["status"])] = int(ligne["n"])

    prets: dict[str, int] = {
        str(ligne["queue"]): int(ligne["n"])
        for ligne in database.fetch_all(_ready_counts_sql(par_file), params)
    }

    return [
        QueueStatus(queue=nom, counts=counts, ready=prets.get(nom, 0))
        for nom, counts in sorted(par_nom.items())
    ]


def get_job(job_id: int, *, db: Any = None) -> Job | None:
    """Renvoie l'état d'une tâche par son identifiant, ou `None` si absente."""
    row = (db if db is not None else _db_module()).fetch_one(_SELECT_JOB_SQL, (job_id,))
    if row is None:
        return None
    return Job(
        id=int(row["id"]),
        queue=str(row["queue"]),
        task=str(row["task"]),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        last_error=row["last_error"],
    )
