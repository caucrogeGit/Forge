from core.database.connection import close_connection, get_connection

SELECT_OBS_BY_ID = """
SELECT
    oc.Id,
    oc.EleveId,
    oc.CoursId,
    oc.NeTravaillePas,
    oc.Bavarde,
    oc.Dort,
    oc.Telephone,
    oc.Perturbe,
    oc.RefuseConsigne,
    oc.Remarque,
    e.Nom       AS EleveNom,
    e.Prenom    AS ElevePrenom,
    e.Classe    AS EleveClasse,
    c.Titre     AS CoursTitre,
    c.DateCours AS CoursDate,
    c.Classe    AS CoursClasse
FROM observation_cours oc
JOIN eleve e ON e.Id = oc.EleveId
JOIN cours  c ON c.Id = oc.CoursId
WHERE oc.Id = ?
LIMIT 1
"""

SELECT_OBS_BY_ELEVE = """
SELECT
    oc.Id,
    oc.NeTravaillePas,
    oc.Bavarde,
    oc.Dort,
    oc.Telephone,
    oc.Perturbe,
    oc.RefuseConsigne,
    oc.Remarque,
    c.Titre     AS CoursTitre,
    c.DateCours AS CoursDate
FROM observation_cours oc
JOIN cours c ON c.Id = oc.CoursId
WHERE oc.EleveId = ?
ORDER BY c.DateCours DESC, oc.Id DESC
"""

SELECT_OBS_BY_COURS = """
SELECT
    oc.Id,
    oc.NeTravaillePas,
    oc.Bavarde,
    oc.Dort,
    oc.Telephone,
    oc.Perturbe,
    oc.RefuseConsigne,
    oc.Remarque,
    e.Nom    AS EleveNom,
    e.Prenom AS ElevePrenom
FROM observation_cours oc
JOIN eleve e ON e.Id = oc.EleveId
WHERE oc.CoursId = ?
ORDER BY e.Nom, e.Prenom
"""

INSERT_OBS = """
INSERT INTO observation_cours
    (EleveId, CoursId, NeTravaillePas, Bavarde, Dort, Telephone, Perturbe, RefuseConsigne, Remarque)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_OBS = """
UPDATE observation_cours
SET NeTravaillePas = ?,
    Bavarde        = ?,
    Dort           = ?,
    Telephone      = ?,
    Perturbe       = ?,
    RefuseConsigne = ?,
    Remarque       = ?
WHERE Id = ?
"""


def _bool_params(data: dict) -> tuple:
    return (
        bool(data.get("ne_travaille_pas")),
        bool(data.get("bavarde")),
        bool(data.get("dort")),
        bool(data.get("telephone")),
        bool(data.get("perturbe")),
        bool(data.get("refuse_consigne")),
        data.get("remarque") or None,
    )


def get_observation_by_id(obs_id: int) -> dict | None:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_OBS_BY_ID, (obs_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_observations_by_eleve(eleve_id: int) -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_OBS_BY_ELEVE, (eleve_id,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_observations_by_cours(cours_id: int) -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_OBS_BY_COURS, (cours_id,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def add_observation(eleve_id: int, cours_id: int, data: dict) -> int:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(INSERT_OBS, (eleve_id, cours_id, *_bool_params(data)))
        connection.commit()
        return cursor.lastrowid
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def update_observation(obs_id: int, data: dict) -> None:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(UPDATE_OBS, (*_bool_params(data), obs_id))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
